# 🔧 ИСПРАВЛЕННЫЙ upload.py - все ошибки устранены

import os
import html
import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from save_utils import send_to_gpt_vision, convert_pdf_to_images
from gpt import ask_structured, is_medical_text, generate_medical_summary, generate_title_from_text, extract_text_from_image
from db_postgresql import save_document, get_user_language, t
from registration import user_states
from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
# ❌ УДАЛИТЬ: from subscription_manager import spend_document_limit, SubscriptionManager
from file_utils import validate_file_size, validate_file_extension, create_simple_file_path

logger = logging.getLogger(__name__)

async def handle_document_upload(message: types.Message, bot):
    user_id = message.from_user.id
    user_states[user_id] = None
    lang = await get_user_language(user_id)

    # ✅ СНАЧАЛА быстрые проверки БЕЗ трат лимитов
    if message.content_type not in [types.ContentType.DOCUMENT, types.ContentType.PHOTO]:
        await message.answer(t("unrecognized_document", lang))
        return

    # ✅ ПОТОМ проверяем лимиты
    from rate_limiter import check_rate_limit, record_user_action
    
    allowed, error_msg = await check_rate_limit(user_id, "document")
    if not allowed:
        await message.answer(error_msg)
        return
    
    from keyboards import show_main_menu
    await show_main_menu(message, lang)

    try:
        file = message.document or message.photo[-1]
        file_id = file.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # ✅ ИСПРАВЛЕННОЕ ОПРЕДЕЛЕНИЕ ИМЕНИ ФАЙЛА
        if hasattr(file, "file_name") and file.file_name:
            original_filename = file.file_name
        else:
            # Для фото без имени создаем простое имя
            original_filename = f"document_{file_id[:8]}.jpg"

        # ✅ СОЗДАНИЕ БЕЗОПАСНОГО ПУТИ - используем простую функцию
        try:
            local_file = create_simple_file_path(user_id, original_filename)
        except ValueError as e:
            # Локализуем ошибки файловой системы
            error_key = {
                "Empty filename": "file_empty_name_error",
                "Invalid filename: contains dangerous characters": "file_invalid_name_error", 
                "Filename too long": "file_name_too_long_error",
                "File path outside allowed directory": "file_path_security_error",
            }.get(str(e), "file_creation_error")
            await message.answer(t(error_key, lang))
            return  # ← НЕ записываем лимит при ошибке пути
        except Exception as e:
            await message.answer(t("file_creation_error", lang))
            return  # ← НЕ записываем лимит при ошибке

        # СКАЧИВАНИЕ ФАЙЛА
        await bot.download_file(file_path, destination=local_file)

        # ПРОВЕРКА РАЗМЕРА ФАЙЛА ПОСЛЕ СКАЧИВАНИЯ
        if not validate_file_size(local_file):
            os.remove(local_file)  # Удаляем слишком большой файл
            await message.answer(t("file_too_large", lang))
            return  # ← НЕ записываем лимит для больших файлов

        # Определяем тип файла
        file_ext = os.path.splitext(original_filename.lower())[1]
        if not file_ext:
            file_ext = '.jpg'  # По умолчанию
        
        file_type = "pdf" if file_ext == ".pdf" else "image"

        await message.answer(t("document_received", lang))

        # ОБРАБОТКА ФАЙЛА
        if file_ext == '.pdf':
            try:
                image_paths = convert_pdf_to_images(local_file, output_dir=f"files/{user_id}/pages")
                if not image_paths:
                    await message.answer(t("pdf_read_failed", lang))
                    return  # ← НЕ записываем лимит если PDF нечитаемый
                if len(image_paths) > 5:
                    await message.answer(t("file_too_many_pages", lang, pages=len(image_paths)))
                    image_paths = image_paths[:5]

                vision_text = ""
                for img_path in image_paths:
                    page_text, _ = await send_to_gpt_vision(img_path)
                    vision_text += page_text + "\n\n"

                vision_text = vision_text.strip()
            except Exception as e:
                await message.answer(t("pdf_processing_error", lang))
                return  # ← НЕ записываем лимит при ошибке PDF
        else:
            try:
                vision_text, _ = await send_to_gpt_vision(local_file)
            except Exception as e:
                await message.answer(t("image_analysis_error", lang))
                return  # ← НЕ записываем лимит при ошибке изображения

        if not await is_medical_text(vision_text):
            await message.answer(t("not_medical_doc", lang))
            return  # ← НЕ записываем лимит для немедицинских документов
        
        # ✅ НОВЫЙ ПОРЯДОК: Сначала заголовок!
        auto_title = await generate_title_from_text(text=vision_text[:1500], lang=lang)
        
        # ✅ Затем структурированный текст БЕЗ заголовка
        raw_text = await ask_structured(vision_text[:8000], lang=lang)
        
        # ✅ И резюме для векторной базы
        summary = await generate_medical_summary(vision_text[:8000], lang)

        if raw_text:
            # ✅ Импортируем функции разбивки сообщений
            from gpt import safe_telegram_text, split_long_message
            
            # ✅ Применяем правильное форматирование 
            formatted_text = safe_telegram_text(raw_text)
            
            # ✅ НОВОЕ: Заголовок включаем в header сообщения
            header = f"{t('vision_read_text', lang)}\n «{auto_title}»"
            full_text = f"{header}\n\n{formatted_text}"
            
            # ✅ Разбиваем на части если слишком длинное
            message_parts = split_long_message(full_text, max_length=4000)
            
            # ✅ Отправляем каждую часть отдельно
            for i, part in enumerate(message_parts):
                try:
                    await message.answer(part, parse_mode="HTML")
                    
                    # Небольшая задержка между сообщениями для читаемости
                    if i < len(message_parts) - 1:  # Не ждем после последнего
                        import asyncio
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    # Fallback: отправляем без HTML форматирования
                    try:
                        plain_text = part.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
                        await message.answer(plain_text)
                    except Exception as fallback_error:
                        await message.answer(t("display_error", lang))
        else:
            await message.answer(t("vision_failed", lang))
            return  # ← НЕ записываем лимит если обработка не удалась

        document_id = await save_document(
            user_id=user_id,
            title=auto_title,
            file_path=local_file,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary
        )
        
        chunks = await split_into_chunks(summary, document_id, user_id)
        await add_chunks_to_vector_db(document_id, user_id, chunks)

        try:
            
            from medical_timeline import update_medical_timeline_on_document_upload
            
            # Используем полный текст документа для извлечения медицинских событий
            medical_timeline_success = await update_medical_timeline_on_document_upload(
                user_id=user_id,
                document_id=document_id,
                document_text=raw_text,  # Используем исходный текст
                use_gemini=False  # По умолчанию GPT, можно переключить для тестирования
            )

        except Exception as e:
            # Не прерываем процесс загрузки документа из-за ошибки медкарты
            from error_handler import log_error_with_context
            log_error_with_context(e, {
                "function": "medical_timeline_update", 
                "user_id": user_id, 
                "document_id": document_id
            })

        # ✅ ЗАПИСЫВАЕМ ЛИМИТ ТОЛЬКО ПОСЛЕ ПОЛНОЙ УСПЕШНОЙ ОБРАБОТКИ
        await record_user_action(user_id, "document")
        logger.info(f"✅ Rate limiter записан для пользователя")

        from subscription_manager import SubscriptionManager
        await SubscriptionManager.spend_limits(user_id, documents=1)
        logger.info(f"✅ Основной лимит списан для пользователя")

        await message.answer(t("document_saved", lang, title=auto_title), parse_mode="HTML")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("rename_doc_button", lang), callback_data=f"rename_{document_id}")],
            [InlineKeyboardButton(text=t("delete_doc_button", lang), callback_data=f"delete_{document_id}")]
        ])

        await message.answer(
            t("next_steps_info", lang),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        user_states[user_id] = None


    except Exception as e:
        # Безопасное логирование через централизованную систему
        from error_handler import log_error_with_context
        log_error_with_context(e, {
            "function": "document_processing",
            "user_id": getattr(message, 'from_user', {}).id if hasattr(message, 'from_user') else None,
            "file_type": "document"  # без деталей файла
        })
        
        await message.answer(t("processing_error", lang))