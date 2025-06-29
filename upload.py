# upload.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с лучшей обработкой файлов

import os
import html
import logging  # ✅ ДОБАВЛЕНО
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from save_utils import send_to_gpt_vision, convert_pdf_to_images
from gpt import ask_structured, is_medical_text, generate_medical_summary, generate_title_from_text, extract_text_from_image
from db_postgresql import save_document, get_user_language, t
from registration import user_states
from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
from subscription_manager import check_document_limit, check_gpt4o_limit, spend_document_limit, spend_gpt4o_limit, SubscriptionManager

# ИСПРАВЛЕННЫЙ ИМПОРТ - используем простую функцию для отладки
from file_utils import validate_file_size, validate_file_extension, create_simple_file_path

# ✅ СОЗДАЕМ LOGGER
logger = logging.getLogger(__name__)

async def handle_document_upload(message: types.Message, bot):
    user_id = message.from_user.id
    user_states[user_id] = None
    lang = await get_user_language(user_id)
    
    try:
        print(f"\n📄 Начало загрузки документа для пользователя {user_id}")
        
        if message.content_type not in [types.ContentType.DOCUMENT, types.ContentType.PHOTO]:
            await message.answer(t("unrecognized_document", lang))
            return

        file = message.document or message.photo[-1]
        file_id = file.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        print(f"📁 File info: {file_info}")

        # ✅ ИСПРАВЛЕННОЕ ОПРЕДЕЛЕНИЕ ИМЕНИ ФАЙЛА
        if hasattr(file, "file_name") and file.file_name:
            original_filename = file.file_name
            print(f"📝 Оригинальное имя файла: {original_filename}")
        else:
            # Для фото без имени создаем простое имя
            original_filename = f"document_{file_id[:8]}.jpg"
            print(f"📝 Сгенерированное имя файла: {original_filename}")

        # ✅ СОЗДАНИЕ БЕЗОПАСНОГО ПУТИ - используем простую функцию
        try:
            local_file = create_simple_file_path(user_id, original_filename)
            print(f"💾 Путь для сохранения: {local_file}")
        except Exception as e:
            print(f"❌ Ошибка создания пути: {e}")
            await message.answer(f"❌ Ошибка имени файла: {str(e)}")
            return

        # СКАЧИВАНИЕ ФАЙЛА
        print("⬇️ Начинаю скачивание файла...")
        await bot.download_file(file_path, destination=local_file)
        print("✅ Файл скачан успешно")

        # ПРОВЕРКА РАЗМЕРА ФАЙЛА ПОСЛЕ СКАЧИВАНИЯ
        if not validate_file_size(local_file):
            os.remove(local_file)  # Удаляем слишком большой файл
            await message.answer("❌ Файл слишком большой. Максимальный размер: 5 МБ")
            return

        # Определяем тип файла
        file_ext = os.path.splitext(original_filename.lower())[1]
        if not file_ext:
            file_ext = '.jpg'  # По умолчанию
        
        file_type = "pdf" if file_ext == ".pdf" else "image"
        print(f"📋 Тип файла: {file_type} (расширение: {file_ext})")

        await message.answer(t("document_received", lang))

        # ОБРАБОТКА ФАЙЛА
        if file_ext == '.pdf':
            print("📄 Обрабатываю PDF...")
            try:
                image_paths = convert_pdf_to_images(local_file, output_dir=f"files/{user_id}/pages")
                if not image_paths:
                    await message.answer(t("pdf_read_failed", lang))
                    return
                if len(image_paths) > 5:
                    await message.answer(t("file_too_many_pages", lang, pages=len(image_paths)))
                    image_paths = image_paths[:5]

                vision_text = ""
                for img_path in image_paths:
                    page_text, _ = await send_to_gpt_vision(img_path)
                    vision_text += page_text + "\n\n"

                vision_text = vision_text.strip()
            except Exception as e:
                print(f"❌ Ошибка обработки PDF: {e}")
                await message.answer("❌ Ошибка при обработке PDF файла")
                return
        else:
            print("🖼️ Обрабатываю изображение...")
            try:
                vision_text, _ = await send_to_gpt_vision(local_file)
            except Exception as e:
                print(f"❌ Ошибка обработки изображения: {e}")
                await message.answer("❌ Ошибка при анализе изображения")
                return

        print("🔍 Проверяю, является ли текст медицинским...")
        if not await is_medical_text(vision_text):
            await message.answer(t("not_medical_doc", lang))
            return

        print("📝 Создаю структурированный текст и резюме...")
        
        # ✅ НОВЫЙ ПОРЯДОК: Сначала заголовок!
        print("🏷️ Генерирую заголовок...")
        auto_title = await generate_title_from_text(text=vision_text[:1500], lang=lang)
        
        # ✅ Затем структурированный текст БЕЗ заголовка
        print("📝 Создаю структурированный текст...")
        raw_text = await ask_structured(vision_text[:8000], lang=lang)
        
        # ✅ И резюме для векторной базы
        print("📝 Создаю резюме для векторной базы...")
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
                    print(f"❌ Ошибка отправки части {i+1}: {e}")
                    # Fallback: отправляем без HTML форматирования
                    try:
                        plain_text = part.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
                        await message.answer(plain_text)
                    except Exception as fallback_error:
                        print(f"❌ Критическая ошибка отправки: {fallback_error}")
                        await message.answer("❌ Ошибка отображения результата")
        else:
            await message.answer(t("vision_failed", lang))
            return

        print("💾 Сохраняю документ в БД...")
        document_id = await save_document(
            user_id=user_id,
            title=auto_title,
            file_path=local_file,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary
        )
        
        # ✅ СПИСЫВАЕМ ЛИМИТ НА ДОКУМЕНТ
        await spend_document_limit(user_id)
        logger.info(f"Списан лимит на документ для пользователя {user_id}")
        
        print("🧠 Добавляю в векторную базу...")
        chunks = await split_into_chunks(summary, document_id, user_id)
        await add_chunks_to_vector_db(document_id, user_id, chunks)

        try:
            print(f"\n🏥 Обновление медицинской карты для документа {document_id}")
            
            from medical_timeline import update_medical_timeline_on_document_upload
            
            # Используем полный текст документа для извлечения медицинских событий
            medical_timeline_success = await update_medical_timeline_on_document_upload(
                user_id=user_id,
                document_id=document_id,
                document_text=raw_text,  # Используем исходный текст
                use_gemini=False  # По умолчанию GPT, можно переключить для тестирования
            )
            
            if medical_timeline_success:
                print(f"✅ Медицинская карта обновлена для документа {document_id}")
            else:
                print(f"⚠️ Не удалось обновить медицинскую карту для документа {document_id}")
                
        except Exception as e:
            print(f"❌ Ошибка обновления медицинской карты: {e}")
            # Не прерываем процесс загрузки документа из-за ошибки медкарты
            from error_handler import log_error_with_context
            log_error_with_context(e, {
                "function": "medical_timeline_update", 
                "user_id": user_id, 
                "document_id": document_id
            })

        await message.answer(t("document_saved", lang, title=auto_title), parse_mode="HTML")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("view_full_text_button", lang), callback_data=f"view_{document_id}")],
            [InlineKeyboardButton(text=t("rename_doc_button", lang), callback_data=f"rename_{document_id}")],
            [InlineKeyboardButton(text=t("delete_doc_button", lang), callback_data=f"delete_{document_id}")]
        ])

        await message.answer(
            "ℹ️ Что дальше?\n\n"
            "▸ Нажми <b>«Посмотреть весь документ»</b>, чтобы увидеть всё, что удалось прочитать\n"
            "▸ Если текст получился нечитаемым — нажми <b>«Удалить»</b> и попробуй загрузить фото получше\n"
            "▸ Можно <b>переименовать</b> документ для удобства",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        print("✅ Документ успешно обработан")

    except Exception as e:
        print(f"❌ Общая ошибка при загрузке документа: {e}")
        import traceback
        print(f"📊 Полная трассировка: {traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке файла. Попробуйте еще раз.")

