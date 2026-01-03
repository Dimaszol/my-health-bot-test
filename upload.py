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
from file_utils import validate_file_size, validate_file_extension, create_simple_file_path
from file_storage import get_file_storage

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

        # ===================================================
        # 🆕 НОВАЯ ЛОГИКА: ИСПОЛЬЗУЕМ document_processor.py
        # ===================================================

        from document_processor import process_document

        # Определяем тип файла
        file_type = "pdf" if file_ext == ".pdf" else "image"

        # Обрабатываем документ через новый пайплайн
        result = await process_document(
            file_path=local_file,
            user_id=user_id,
            lang=lang,
            additional_context=None  # В Telegram боте пока нет доп. контекста
        )

        # Проверяем результат
        if not result.get('success', False):
            # Удаляем временный файл
            if os.path.exists(local_file):
                os.remove(local_file)
            
            error_type = result.get('error_type', 'unknown')
            
            # Специальная обработка для немедицинских документов
            if error_type == 'not_medical':
                await message.answer(t("not_medical_document", lang))
                return
            
            # Общая ошибка обработки
            await message.answer(t("document_processing_error", lang))
            return

        # Извлекаем результаты
        title = result['title']
        raw_text = result['raw_text']
        summary = result['summary']
        vision_text = result['full_analysis']
        document_type = result.get('document_type')
        subtype = result.get('subtype')
        document_date = result.get('document_date')

        # ===================================================
        # 📱 ОТПРАВКА РЕЗУЛЬТАТА ПОЛЬЗОВАТЕЛЮ В TELEGRAM
        # ===================================================

        if raw_text:
            # Импортируем функции разбивки сообщений
            from gpt import safe_telegram_text, split_long_message
            
            # Применяем правильное форматирование 
            formatted_text = safe_telegram_text(raw_text)
            
            # Заголовок включаем в header сообщения
            header = f"{t('vision_read_text', lang)}\n «{title}»"
            full_text = f"{header}\n\n{formatted_text}"
            
            # Разбиваем на части если слишком длинное
            message_parts = split_long_message(full_text, max_length=4000)
            
            # Отправляем каждую часть отдельно
            for i, part in enumerate(message_parts):
                try:
                    await message.answer(part, parse_mode="HTML")
                    
                    # Небольшая задержка между сообщениями для читаемости
                    if i < len(message_parts) - 1:
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
            return

        # ===================================================
        # 💾 СОХРАНЕНИЕ В ПОСТОЯННОЕ ХРАНИЛИЩЕ И БД
        # ===================================================

        storage = get_file_storage()
        success, permanent_path = storage.save_file(
            user_id=user_id,
            filename=original_filename,
            source_path=local_file
        )

        if not success:
            await message.answer(t("file_storage_error", lang))
            return

        # Логируем успешное сохранение
        logger.info(f"✅ Файл сохранен в постоянное хранилище: {permanent_path}")

        # Сохраняем в БД
        document_id = await save_document(
            user_id=user_id,
            file_path=permanent_path,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary,
            full_analysis=vision_text,
            title=title,
            document_type=document_type,
            subtype=subtype,
            additional_context=None,
            document_date=document_date
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

        await message.answer(t("document_saved", lang, title=title), parse_mode="HTML")

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