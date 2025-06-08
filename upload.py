# upload.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с лучшей обработкой файлов

import os
import html
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from save_utils import send_to_gpt_vision, convert_pdf_to_images
from gpt import ask_gpt, ask_structured, is_medical_text, generate_medical_summary, generate_title_from_text, extract_text_from_image
from db import save_document, get_user_language, t
from registration import user_states
from vector_utils import split_into_chunks, add_chunks_to_vector_db

# ИСПРАВЛЕННЫЙ ИМПОРТ - используем простую функцию для отладки
from file_utils import validate_file_size, validate_file_extension, create_simple_file_path

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
        raw_text = await ask_structured(vision_text[:3000], lang=lang)
        summary = await generate_medical_summary(vision_text[:3000], lang)

        if raw_text:
            clean_text = html.escape(raw_text[:2000])
            await message.answer(t("vision_read_text", lang) + "\n\n" + clean_text, parse_mode="HTML")
        else:
            await message.answer(t("vision_failed", lang))
            return

        print("🏷️ Генерирую заголовок...")
        auto_title = await generate_title_from_text(text=raw_text[:1500], lang=lang)

        print("💾 Сохраняю документ в БД...")
        document_id = await save_document(
            user_id=user_id,
            title=auto_title,
            file_path=local_file,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary
        )
        
        print("🧠 Добавляю в векторную базу...")
        chunks = await split_into_chunks(summary, document_id, user_id)
        add_chunks_to_vector_db(chunks)

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

async def handle_image_analysis(message: types.Message, bot):
    """Обработка анализа изображений"""
    user_id = message.from_user.id
    user_states[user_id] = None
    lang = await get_user_language(user_id)

    try:
        print(f"\n🖼️ Начало анализа изображения для пользователя {user_id}")
        
        if message.content_type not in [types.ContentType.DOCUMENT, types.ContentType.PHOTO]:
            await message.answer(t("unrecognized_document", lang))
            return

        file = message.document or message.photo[-1]
        file_id = file.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        print(f"📁 File info: {file_info}")

        # ✅ БЕЗОПАСНОЕ ОПРЕДЕЛЕНИЕ ИМЕНИ ФАЙЛА
        if hasattr(file, "file_name") and file.file_name:
            original_filename = file.file_name
            print(f"📝 Оригинальное имя файла: {original_filename}")
        else:
            original_filename = f"scan_{file_id[:8]}.jpg"
            print(f"📝 Сгенерированное имя файла: {original_filename}")

        # ✅ СОЗДАНИЕ ПУТИ - используем простую функцию
        try:
            local_file = create_simple_file_path(user_id, original_filename)
            print(f"💾 Путь для сохранения: {local_file}")
        except Exception as e:
            print(f"❌ Ошибка создания пути: {e}")
            await message.answer(f"❌ Ошибка имени файла: {str(e)}")
            return

        print("⬇️ Скачиваю файл...")
        await bot.download_file(file_path, destination=local_file)
        print("✅ Файл скачан")

        if not validate_file_size(local_file):
            os.remove(local_file)
            await message.answer("❌ Файл слишком большой. Максимальный размер: 5 МБ")
            return

        await message.answer(t("image_processing", lang))

        # ОПРЕДЕЛЕНИЕ ТИПА ФАЙЛА И ОБРАБОТКА
        file_ext = os.path.splitext(original_filename.lower())[1]
        if not file_ext:
            file_ext = '.jpg'
            
        image_path = None
        
        if file_ext == '.pdf':
            print("📄 Обрабатываю PDF снимок...")
            try:
                image_paths = convert_pdf_to_images(local_file, output_dir=f"files/{user_id}/pages")
                if not image_paths:
                    await message.answer(t("pdf_read_failed", lang))
                    return
                if len(image_paths) > 1:
                    await message.answer(t("pdf_single_page_only", lang))
                    return
                image_path = image_paths[0]
            except Exception as e:
                print(f"❌ Ошибка обработки PDF: {e}")
                await message.answer("❌ Ошибка при обработке PDF файла")
                return
        else:
            image_path = local_file

        print("🔍 Анализирую изображение с помощью GPT Vision...")
        from gpt import send_to_gpt_vision
        try:
            vision_text, _ = await send_to_gpt_vision(image_path, lang=lang)
        except Exception as e:
            print(f"❌ Ошибка GPT Vision: {e}")
            await message.answer("❌ Ошибка при анализе изображения ИИ")
            return
        
        if not vision_text:
            await message.answer(t("vision_failed_response", lang))
            return

        print("🔍 Проверяю медицинский контент...")
        if not await is_medical_text(vision_text):
            await message.answer(t("not_medical_doc1", lang))
            return
        
        print("📝 Создаю резюме и заголовок...")
        summary = await generate_medical_summary(vision_text[:3000], lang)
        title = await generate_title_from_text(text=vision_text[:1500], lang=lang)

        clean_text = html.escape(vision_text[:2000])
        await message.answer(t("image_vision_text", lang) + "\n\n" + clean_text, parse_mode="HTML")

        print("💾 Сохраняю в БД...")
        document_id = await save_document(
            user_id=user_id,
            title=title,
            file_path=local_file,
            file_type="image",
            raw_text=vision_text,
            summary=summary,
            confirmed=True
        )

        print("🧠 Добавляю в векторную базу...")
        chunks = await split_into_chunks(summary, document_id, user_id)
        add_chunks_to_vector_db(chunks)

        await message.answer(t("image_saved", lang, title=title), parse_mode="HTML")
        
        from documents import send_note_controls
        await send_note_controls(message, document_id)

        print("✅ Изображение успешно проанализировано")

    except Exception as e:
        print(f"❌ Общая ошибка при анализе изображения: {e}")
        import traceback
        print(f"📊 Полная трассировка: {traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при анализе изображения. Попробуйте еще раз.")