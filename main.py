import asyncio
import os
import html
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from db import save_user, user_exists, get_user_name, save_document, update_document_title, \
    get_documents_by_user, get_document_by_id, delete_document, save_message, get_last_messages, \
    get_conversation_summary, get_last_summary, get_user_profile, get_user_language, t, \
    get_all_values_for_key
from registration import user_states, start_registration, handle_registration_step
from error_handler import handle_telegram_errors, BotError, OpenAIError, get_user_friendly_message, log_error_with_context, check_openai_health
from keyboards import main_menu_keyboard
from documents import handle_show_documents, handle_ignore_document
from save_utils import maybe_update_summary, format_user_profile
from vector_utils import search_similar_chunks, keyword_search_chunks
from vector_db import delete_document_from_vector_db
from rate_limiter import check_rate_limit, record_user_action, get_rate_limit_stats
from db_pool import initialize_db_pool, close_db_pool, get_db_stats, db_health_check
from gpt import ask_gpt, ask_doctor, check_openai_status, fallback_response, fallback_summarize

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(CommandStart())
@handle_telegram_errors
async def send_welcome(message: types.Message):
    from db import is_fully_registered, get_user_language
    from keyboards import show_main_menu, language_keyboard
    user_id = message.from_user.id

    if await is_fully_registered(user_id):
        name = await get_user_name(user_id)
        lang = await get_user_language(user_id)
        await message.answer(t("welcome_back", lang, name=name))
        await show_main_menu(message, lang)
    else:
        await message.answer(
            "🇺🇦 Обери мову інтерфейсу\n\n🇷🇺 Выбери язык интерфейса\n\n🇬🇧 Choose your language",
            reply_markup=language_keyboard()
        )

@dp.message(lambda msg: msg.text in ["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"])
@handle_telegram_errors
async def language_start(message: types.Message):
    from db import set_user_language
    user_id = message.from_user.id

    lang_map = {
        "🇷🇺 Русский": "ru",
        "🇺🇦 Українська": "uk",
        "🇬🇧 English": "en"
    }
    lang_code = lang_map[message.text]
    await set_user_language(user_id, lang_code)

    from db import is_fully_registered

    if await is_fully_registered(user_id):
        name = await get_user_name(user_id)
        keyboard = main_menu_keyboard(lang_code)
        await message.answer(t("welcome_back", lang_code, name=name), reply_markup=keyboard)
    else:
        await start_registration(user_id, message)

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_upload_doc"))
@handle_telegram_errors
async def prompt_document_upload(message: types.Message):
    user_states[message.from_user.id] = "awaiting_document"
    lang = await get_user_language(message.from_user.id)
    await message.answer(t("please_send_file", lang))

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_note"))
@handle_telegram_errors
async def prompt_memory_note(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    user_states[message.from_user.id] = "awaiting_memory_note"
    keyboard = ReplyKeyboardMarkup(
         keyboard=[[KeyboardButton(text=t("cancel", lang))]],
        resize_keyboard=True
    )
    await message.answer(t("write_note", lang), reply_markup=keyboard)

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_upload_image"))
@handle_telegram_errors
async def ask_for_image(message: types.Message):
    user_states[message.from_user.id] = "awaiting_image_analysis"
    lang = await get_user_language(message.from_user.id)
    await message.answer(t("please_send_image", lang))

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_documents"))
@handle_telegram_errors
async def show_documents_handler(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"mode": "viewing_documents", "offset": 0}
    await handle_show_documents(message, user_id=message.from_user.id)

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_schedule"))
@handle_telegram_errors
async def show_medications_schedule(message: types.Message):
    try:
        from db import format_medications_schedule, get_user_language
        from locales import translations
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        user_id = message.from_user.id
        lang = await get_user_language(user_id)

        text = await format_medications_schedule(user_id)
        if not text:
            text = translations[lang]["schedule_empty"]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=translations[lang]["edit_schedule_button"],
                callback_data="edit_meds"
            )
        ]])
        await message.answer(
            f"🗓 <b>{translations[lang]['your_schedule']}</b>\n\n<pre>{text}</pre>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        lang = await get_user_language(message.from_user.id)
        log_error_with_context(e, {"user_id": message.from_user.id, "action": "show_medications"})
        await message.answer(get_user_friendly_message(e, lang))

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_settings"))
@handle_telegram_errors
async def show_settings_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="settings_profile")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="settings_help")]
    ])
    lang = await get_user_language(message.from_user.id)
    await message.answer(t("settings_title", lang), reply_markup=keyboard)

@dp.message(lambda msg: msg.text == "/reset")
@handle_telegram_errors
async def reset_user(message: types.Message):
    user_id = message.from_user.id
    from db import delete_user_completely

    await delete_user_completely(user_id)
    lang = "ru"  # ✅ ИСПРАВЛЕНО: используем дефолтный язык после удаления
    await message.answer(t("reset_done", lang))

@dp.message()
@handle_telegram_errors
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # Обработка файлов
    if message.text is None:
        state = user_states.get(user_id)
        if state == "awaiting_document":
            allowed, error_msg = await check_rate_limit(user_id, "document")  # ✅ Добавлен await
            if not allowed:
                await message.answer(error_msg)
                return  # ✅ УБРАНА запись action при блокировке
            try:
                from upload import handle_document_upload
                await handle_document_upload(message, bot)
                await record_user_action(user_id, "document")  # ✅ Записываем только при успехе
                return
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "document_upload"})
                await message.answer(get_user_friendly_message(e, lang))
                return
                
        elif state == "awaiting_image_analysis":
            allowed, error_msg = await check_rate_limit(user_id, "image")  # ✅ Добавлен await
            if not allowed:
                await message.answer(error_msg)
                return
            try:
                from upload import handle_image_analysis
                await handle_image_analysis(message, bot)
                await record_user_action(user_id, "image")  # ✅ Добавлен await + перенесен в try
                return
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "image_analysis"})
                await message.answer(get_user_friendly_message(e, lang))
                return
        else:
            # ✅ Обработка неподдерживаемых файлов
            await message.answer(t("unsupported_input", lang))
            return

    # Обработка регистрации
    if await handle_registration_step(user_id, message):
        return
        
    # Обработка переименования документов
    elif isinstance(user_states.get(user_id), str) and user_states[user_id].startswith("rename_"):
        if message.text.lower() in [t("cancel", lang).lower()]:
            user_states[user_id] = None
            await message.answer(t("rename_cancelled", lang))
            return

        try:
            doc_id = int(user_states[user_id].split("_")[1])
            new_title = message.text.strip()
            await update_document_title(doc_id, new_title)
            await message.answer(t("document_renamed", lang, name=new_title), parse_mode="HTML")
            user_states[user_id] = None
            return
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "rename_document"})
            await message.answer(get_user_friendly_message(e, lang))
            return

    # Обработка отмены
    elif message.text in [t("cancel", lang)]:
        if user_states.get(user_id) == "awaiting_memory_note":
            from keyboards import show_main_menu
            user_states[user_id] = None
            await message.answer(t("note_cancelled", lang))
            await show_main_menu(message, lang)
            return
        
    # Обработка заметок в память
    elif user_states.get(user_id) == "awaiting_memory_note":
        allowed, error_msg = await check_rate_limit(user_id, "note")  # ✅ Добавлен await
        if not allowed:
            await message.answer(error_msg)
            return
        try:
            from gpt import summarize_note_text, generate_title_for_note
            from vector_utils import split_into_chunks, add_chunks_to_vector_db
            from db import save_document
            from documents import send_note_controls

            note_text = message.text.strip()
            
            # Безопасные вызовы GPT с обработкой ошибок
            try:
                title = await generate_title_for_note(note_text)
                summary = await summarize_note_text(note_text, lang)
            except OpenAIError as e:
                title = f"Заметка {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                summary = fallback_summarize(note_text, lang)
                await message.answer("⚠️ ИИ-обработка недоступна, заметка сохранена в упрощенном виде.")

            document_id = await save_document(
                user_id=user_id,
                title=title,
                file_path="memory_note",
                file_type="note",
                raw_text=note_text,
                summary=summary,
                confirmed=True
            )

            chunks = await split_into_chunks(summary, document_id, user_id)
            add_chunks_to_vector_db(chunks)

            await message.answer(t("note_saved", lang, title=title), parse_mode="HTML")
            await send_note_controls(message, document_id)
            user_states[user_id] = None
            
            # ✅ ИСПРАВЛЕНИЕ: Записываем action ЗДЕСЬ, после успешного сохранения
            await record_user_action(user_id, "note")
            
            from keyboards import show_main_menu
            await show_main_menu(message, lang)
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "save_memory_note"})
            await message.answer(get_user_friendly_message(e, lang))
            return
                 
    # Обработка редактирования лекарств
    elif user_states.get(user_id) == "editing_medications":
        try:
            from db import get_medications, replace_medications
            from gpt import update_medications_via_gpt
            from save_utils import update_user_profile_medications

            current_list = await get_medications(user_id)
            user_input = message.text.strip()

            try:
                new_list = await update_medications_via_gpt(user_input, current_list)
                if new_list is not None:
                    await replace_medications(user_id, new_list)
                    await update_user_profile_medications(user_id)
                    user_states[user_id] = None
                    await message.answer(t("schedule_updated", lang))
                else:
                    await message.answer(t("schedule_update_failed", lang))
            except OpenAIError:
                # Fallback - не обновляем лекарства если GPT недоступен
                await message.answer("⚠️ ИИ-помощник недоступен. Попробуйте обновить лекарства позже.")
                
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "edit_medications"})
            await message.answer(get_user_friendly_message(e, lang))
            return

    # Основная обработка вопросов пользователя
    else:
        allowed, error_msg = await check_rate_limit(user_id, "message")
        if not allowed:
            await message.answer(error_msg)
            return
        try:
            name = await get_user_name(user_id)
            if not name:
                await message.answer(t("not_registered", lang))
                return
                
            user_input = message.text
            await save_message(user_id, "user", user_input)
            
            # Получаем данные для контекста
            summary_text, _ = await get_conversation_summary(user_id)
            last_doc_id, last_summary = await get_last_summary(user_id)
            exclude_texts = last_summary.strip().split("\n\n")

            # Безопасный вызов GPT для улучшения запроса
            try:
                from gpt import enrich_query_for_vector_search
                refined_query = await enrich_query_for_vector_search(user_input)
                print(f"\n🧠 Переформулированный запрос: {refined_query}\n")
            except OpenAIError:
                # Если GPT недоступен, используем оригинальный запрос
                refined_query = user_input
                print("⚠️ Использую оригинальный запрос из-за недоступности GPT")

            # Поиск в векторной базе
            vector_chunks = search_similar_chunks(
                user_id, refined_query, exclude_doc_id=last_doc_id,
                exclude_texts=exclude_texts, limit=4
            )
            keyword_chunks = await keyword_search_chunks(
                user_id, user_input, exclude_doc_id=last_doc_id,
                exclude_texts=exclude_texts, limit=2
            )

            all_chunks = list(dict.fromkeys(vector_chunks + keyword_chunks))
            chunks_text = "\n\n".join(all_chunks[:6])
            print("🧠 Векторные чанки:", len(vector_chunks))
            print("🔑 Ключевые чанки:", len(keyword_chunks))
            print("📦 Итоговые чанки:", len(all_chunks))

            # Подготовка контекста
            MAX_LEN = 300
            last_messages = await get_last_messages(user_id, limit=7)
            if last_messages and last_messages[-1][0] == "user" and last_messages[-1][1] == message.text:
                last_messages = last_messages[:-1]
            context_text = "\n".join([
                f"{role.upper()}: {msg[:MAX_LEN]}" for role, msg in last_messages
            ])

            profile = await get_user_profile(user_id)
            profile_text = format_user_profile(profile)

            # Безопасный вызов GPT доктора
            try:
                gpt_response = await ask_doctor(
                    profile_text=profile_text,
                    summary_text=summary_text,
                    last_summary=last_summary,
                    chunks_text=chunks_text,
                    context_text=context_text,
                    user_question=message.text,
                    lang=lang
                )
            except OpenAIError as e:
                # Fallback ответ если GPT недоступен
                gpt_response = fallback_response(message.text, lang)
                print(f"⚠️ Используется fallback ответ: {e}")

            await save_message(user_id, "bot", gpt_response)

            # Безопасная отправка ответа
            try:
                await message.answer(gpt_response)
            except Exception as e:
                print(f"⚠️ Ошибка отправки HTML, отправляю plain text: {e}")
                from html import escape
                safe_response = escape(gpt_response)
                await message.answer(safe_response, parse_mode=None)
                
            await record_user_action(user_id, "message")

            # Обновление резюме разговора
            try:
                await maybe_update_summary(user_id)
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "update_summary"})
                # Не показываем ошибку пользователю, это внутренняя операция
                
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "handle_main_question"})
            await message.answer(get_user_friendly_message(e, lang))

@dp.callback_query()
@handle_telegram_errors
async def handle_button_action(callback: types.CallbackQuery):
    if callback.data == "more_docs":
        user_id = callback.from_user.id
        state = user_states.get(user_id)

        if isinstance(state, dict) and state.get("mode") == "viewing_documents":
            user_states[user_id]["offset"] += 5
            from documents import handle_show_documents
            await handle_show_documents(callback.message, user_id=user_id)
        else:
            lang = await get_user_language(user_id)  # ✅ ИСПРАВЛЕНО: добавлен await
            await callback.message.answer(t("unknown_state", lang))
        await callback.answer()
        return
        
    if callback.data == "edit_meds":
        user_states[callback.from_user.id] = "editing_medications"
        lang = await get_user_language(callback.from_user.id)
        await callback.message.answer(t("edit_schedule", lang))
        await callback.answer()
        return
    
    if callback.data == "settings_profile":
        lang = await get_user_language(callback.from_user.id)
        await callback.message.answer(t("profile_later", lang))
        await callback.answer()
        return

    if callback.data == "settings_help":
        lang = await get_user_language(callback.from_user.id)
        await callback.message.answer(t("help_later", lang))
        await callback.answer()
        return

    # Обработка действий с документами
    try:
        action, doc_id = callback.data.split("_", 1)
        doc_id = int(doc_id)

        if action == "ignore":
            await handle_ignore_document(callback, doc_id)
            return

        user_id = callback.from_user.id
        doc = await get_document_by_id(doc_id)
        lang = await get_user_language(user_id)
        
        if not doc or doc["user_id"] != user_id:
            await callback.message.answer(t("document_not_found", lang))
            return

        if action == "view":
            title = html.escape(doc["title"])
            text = doc["raw_text"] or t("empty_document", lang)
            clean_text = html.escape(text[:4000])
            from utils.security import safe_send_message
            await safe_send_message(callback.message, clean_text, title=title)
        elif action == "rename":
            user_states[user_id] = f"rename_{doc_id}"
            await callback.message.answer(t("enter_new_name", lang))
        elif action == "delete":
            await delete_document(doc_id)
            delete_document_from_vector_db(doc_id)
            await callback.message.answer(t("document_deleted", lang))
        elif action == "download":
            file_path = doc.get("file_path")
            if not file_path or not os.path.exists(file_path):
                await callback.message.answer(t("file_not_found", lang))
                return
            await callback.message.answer_document(types.FSInputFile(path=file_path))
            
    except Exception as e:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        log_error_with_context(e, {"user_id": user_id, "action": "button_callback", "callback_data": callback.data})
        await callback.message.answer(get_user_friendly_message(e, lang))

@dp.message(lambda msg: msg.text and msg.text == "/stats")
@handle_telegram_errors
async def handle_stats_command(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        stats = get_rate_limit_stats(user_id)
        
        block_status = "🚫 Заблокирован" if stats["is_blocked"] else "✅ Активен"
        
        stats_text = f"""📊 <b>Ваша статистика:</b>

🔄 Состояние: {block_status}
📝 Запросов за час: {stats["total_requests_last_hour"]}

<b>Лимиты для всех:</b>
💬 Сообщения: 10 за минуту
📄 Документы: 3 за 5 минут  
🖼 Изображения: 3 за 10 минут
📝 Заметки: 5 за 5 минут"""

        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer("❌ Ошибка при получении статистики")

@handle_telegram_errors
async def main():
    print("✅ Бот запущен. Ожидаю сообщения...")
    from user_state_manager import user_state_manager
    await user_state_manager.start_cleanup_loop()
    # 🔧 НОВОЕ: Инициализация пула базы данных
    try:
        await initialize_db_pool(max_connections=10)
        print("🗄️ Database pool готов")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # Проверяем состояние OpenAI при запуске
    if await check_openai_status():
        print("✅ OpenAI API доступен")
    else:
        print("⚠️ OpenAI API недоступен - бот будет работать в ограниченном режиме")
    
    # Инициализируем Rate Limiter
    print("🚦 Rate Limiter активирован")
    print("   - Сообщения: 10/мин")
    print("   - Документы: 3/5мин") 
    print("   - Изображения: 3/10мин")
    print("   - Заметки: 5/5мин")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        log_error_with_context(e, {"action": "bot_startup"})
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        raise
    finally:
        # 🔧 НОВОЕ: Закрытие пула при завершении
        await user_state_manager.stop_cleanup_loop()
        await close_db_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
    except Exception as e:
        print("❌ Ошибка при запуске:", e)