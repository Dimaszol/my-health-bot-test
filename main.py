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

# ✅ ОБНОВЛЕННЫЕ ИМПОРТЫ - PostgreSQL версии
from db_postgresql import (
    get_user, create_user, save_document, update_document_title, is_fully_registered, get_user_name,
    get_user_documents, get_document_by_id, delete_document, save_message, 
    get_last_messages, get_conversation_summary,
    get_user_profile, get_user_language, t, get_all_values_for_key,
    initialize_db_pool, close_db_pool, get_db_stats, db_health_check, set_user_language
)

from registration import user_states, start_registration, handle_registration_step
from error_handler import handle_telegram_errors, BotError, OpenAIError, get_user_friendly_message, log_error_with_context, check_openai_health
from keyboards import main_menu_keyboard, settings_keyboard
from profile_keyboards import (
    profile_view_keyboard, profile_edit_keyboard, smoking_choice_keyboard,
    alcohol_choice_keyboard, activity_choice_keyboard, language_choice_keyboard, cancel_keyboard
)
from profile_manager import ProfileManager, CHOICE_MAPPINGS
from documents import handle_show_documents, handle_ignore_document
from save_utils import maybe_update_summary, format_user_profile
from rate_limiter import check_rate_limit, record_user_action, get_rate_limit_stats

# ✅ ОБНОВЛЕННЫЕ ИМПОРТЫ - Vector DB PostgreSQL
from vector_db_postgresql import (
    initialize_vector_db, search_similar_chunks, keyword_search_chunks, 
    delete_document_from_vector_db
)

from gpt import ask_doctor, check_openai_status, fallback_response, fallback_summarize
from subscription_manager import check_document_limit, SubscriptionManager, check_gpt4o_limit
from stripe_config import check_stripe_setup
from subscription_handlers import SubscriptionHandlers, upsell_tracker
from notification_system import NotificationSystem
from stripe_manager import StripeManager
from prompt_logger import process_user_question_detailed, log_search_summary
from photo_analyzer import handle_photo_analysis, handle_photo_question, cancel_photo_analysis

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def detect_user_language(user: types.User) -> str:
    """Автоопределение языка по Telegram"""
    phone_lang = user.language_code if user.language_code else 'en'
    print(f"🌍 Язык телефона: {phone_lang}")
    
    # Простой маппинг на 4 языка
    if phone_lang == 'ru':
        return 'ru'
    elif phone_lang == 'uk': 
        return 'uk'
    elif phone_lang == 'de':
        return 'de'
    else:
        return 'en'  # По умолчанию

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    try:
        # Проверяем, есть ли пользователь в базе
        user_data = await get_user(user_id)
        
        if user_data is None:
            # 🆕 НОВЫЙ ПОЛЬЗОВАТЕЛЬ
            
            # 🌍 Автоопределяем язык и сразу сохраняем
            auto_lang = detect_user_language(message.from_user)
            await set_user_language(user_id, auto_lang)
            
            # 🚀 СРАЗУ НАЧИНАЕМ РЕГИСТРАЦИЮ с автоопределенным языком
            await start_registration_with_language_option(user_id, message, auto_lang)
            return
            
        # ✅ Существующий пользователь
        if await is_fully_registered(user_id):
            # Показываем главное меню
            name = user_data.get('name', 'Пользователь')
            lang = await get_user_language(user_id)
            
            await message.answer(
                t("welcome_back", lang, name=name), 
                reply_markup=main_menu_keyboard(lang)
            )
        else:
            # Продолжаем регистрацию
            await start_registration(user_id, message)
            
    except Exception as e:
        print(f"❌ Ошибка в команде /start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")

async def start_registration_with_language_option(user_id: int, message: types.Message, lang: str):
    """Начало регистрации с возможностью смены языка"""
    
    # Устанавливаем состояние ожидания имени
    user_states[user_id] = {"step": "awaiting_name"}
    
    # Формируем интро-текст
    intro_text = f"{t('intro_1', lang)}\n\n{t('intro_2', lang)}\n\n{t('ask_name', lang)}"
    
    # Клавиатура с кнопкой смены языка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("change_language", lang), 
            callback_data="change_language_registration"
        )]
    ])
    
    await message.answer(
        intro_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# 🆕 ДОБАВЬТЕ эти обработчики ПОСЛЕ start_registration_with_language_option:

@dp.callback_query(lambda c: c.data == "change_language_registration")
async def handle_language_change_during_registration(callback: types.CallbackQuery):
    """Обработка смены языка во время регистрации"""
    
    # Показываем выбор языков
    language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="set_lang_de")]
    ])
    
    await callback.message.edit_text(
        "🇺🇦 Оберіть мову інтерфейсу\n"
        "🇷🇺 Выберите язык интерфейса\n" 
        "🇬🇧 Choose your language\n"
        "🇩🇪 Sprache wählen",
        reply_markup=language_keyboard
    )
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("set_lang_"))
async def handle_set_language_during_registration(callback: types.CallbackQuery):
    """Установка языка и возврат к регистрации"""
    user_id = callback.from_user.id
    selected_lang = callback.data.replace("set_lang_", "")
    
    # Обновляем язык пользователя
    await set_user_language(user_id, selected_lang)
    
    # Возвращаемся к началу регистрации с новым языком
    await start_registration_with_language_option(user_id, callback.message, selected_lang)
    
    await callback.answer()

@dp.message(lambda msg: msg.text in ["🇷 Русский", "🇺🇦 Українська", "🇬🇧 English"])
@handle_telegram_errors
async def language_start(message: types.Message):
    from db_postgresql import set_user_language
    user_id = message.from_user.id

    lang_map = {
        "🇷 Русский": "ru",
        "🇺🇦 Українська": "uk",
        "🇬🇧 English": "en"
    }
    lang_code = lang_map[message.text]
    await set_user_language(user_id, lang_code)
   
    if await is_fully_registered(user_id):
        name = await get_user_name(user_id)
        keyboard = main_menu_keyboard(lang_code)
        await message.answer(t("welcome_back", lang_code, name=name), reply_markup=keyboard)
    else:
        await start_registration(user_id, message)

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_upload_doc"))
@handle_telegram_errors
async def prompt_document_upload(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # ✅ НОВАЯ ЛОГИКА: Проверяем лимиты и показываем уведомления
    can_upload = await NotificationSystem.check_and_notify_limits(
        message, user_id, action_type="document"
    )
    
    if not can_upload:
        return  # Лимиты исчерпаны, уведомление уже показано
    
    # Если лимиты есть - разрешаем загрузку
    user_states[message.from_user.id] = "awaiting_document"
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
        from db_postgresql import format_medications_schedule, get_user_language
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
async def show_settings_menu_new(message: types.Message):
    """Показать меню настроек"""
    lang = await get_user_language(message.from_user.id)
    
    await message.answer(
        t("settings_menu_title", lang),
        reply_markup=settings_keyboard(lang)
    )

@dp.message(lambda msg: msg.text == "/reset123456")
@handle_telegram_errors
async def reset_user(message: types.Message):
    user_id = message.from_user.id
    from db_postgresql import delete_user_completely

    await delete_user_completely(user_id)
    lang = "ru"  # ✅ ИСПРАВЛЕНО: используем дефолтный язык после удаления
    await message.answer(t("reset_done", lang))



@dp.message()
@handle_telegram_errors
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # ✅ ИСПРАВЛЕНИЕ 1: Обработка отмены ПЕРВЫМ ДЕЛОМ (до всех других проверок)
    if message.text and message.text in [t("cancel", lang)]:
        current_state = user_states.get(user_id)
        
        # Сбрасываем состояние пользователя
        user_states[user_id] = None
        
        # Определяем, какую отмену выполняем и отправляем соответствующее сообщение
        if current_state == "awaiting_memory_note":
            await message.answer(
                t("note_cancelled", lang),
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        elif isinstance(current_state, dict) and current_state.get("mode") == "editing_profile":
            await message.answer(
                t("profile_edit_cancelled", lang),
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        elif current_state == "editing_medications":
            await message.answer(
                "❌ Редактирование лекарств отменено",
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        elif isinstance(current_state, str) and current_state.startswith("rename_"):
            await message.answer(
                t("rename_cancelled", lang),
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        else:
            # Любая другая отмена
            await message.answer(
                "❌ Операция отменена",
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        
        # ✅ ГЛАВНОЕ ИСПРАВЛЕНИЕ: ВСЕГДА показываем главное меню после отмены
        from keyboards import show_main_menu
        await show_main_menu(message, lang)
        return  # ✅ Выходим из функции, больше ничего не обрабатываем

    # ✅ Теперь получаем состояние пользователя ПОСЛЕ обработки отмены
    current_state = user_states.get(user_id)
    
    # Если пользователь в режиме ожидания файла, но отправил текст
    if current_state == "awaiting_document":
        if message.text is not None:  # Если отправлен текст вместо файла
            await message.answer(t("unrecognized_document", lang))
            user_states[user_id] = None
            return
    
    # Обработка файлов
    if message.text is None:
        if current_state == "awaiting_document":
            allowed, error_msg = await check_rate_limit(user_id, "document")
            if not allowed:
                await message.answer(error_msg)
                return
            try:
                from upload import handle_document_upload
                await handle_document_upload(message, bot)
                await record_user_action(user_id, "document")
                return
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "document_upload"})
                await message.answer(get_user_friendly_message(e, lang))
                return
        
        elif message.content_type == types.ContentType.PHOTO:
            # ✅ НОВАЯ ЛОГИКА: Обработка фото для анализа
            allowed, error_msg = await check_rate_limit(user_id, "image")
            if not allowed:
                await message.answer(error_msg)
                return
            try:
                await handle_photo_analysis(message, bot)
                await record_user_action(user_id, "image")
                return
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "photo_analysis"})
                await message.answer(get_user_friendly_message(e, lang))
                return

        else:
            # Файл отправлен, но пользователь не в режиме ожидания
            await message.answer(t("unsupported_input", lang))
            return

    # Обработка регистрации
    if await handle_registration_step(user_id, message):
        return
    
    # ✅ НОВОЕ: Обработка вопроса к фото
    elif isinstance(current_state, dict) and current_state.get("type") == "awaiting_photo_question":
        try:
            await handle_photo_question(message, bot)
            return
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "photo_question"})
            await message.answer(get_user_friendly_message(e, lang))
            return
        
    # Обработка переименования документов
    elif isinstance(current_state, str) and current_state.startswith("rename_"):
        # ✅ Отмена уже обработана выше, убираем дублирующую проверку
        try:
            doc_id = int(current_state.split("_")[1])
            new_title = message.text.strip()
            await update_document_title(doc_id, new_title)
            await message.answer(t("document_renamed", lang, name=new_title), parse_mode="HTML")
            user_states[user_id] = None
            
            # ✅ ИСПРАВЛЕНИЕ: показываем главное меню после переименования
            from keyboards import show_main_menu
            await show_main_menu(message, lang)
            return
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "rename_document"})
            await message.answer(get_user_friendly_message(e, lang))
            return

    # Обработка заметок в память
    elif current_state == "awaiting_memory_note":
        # ✅ Отмена уже обработана выше, убираем дублирующую проверку
        allowed, error_msg = await check_rate_limit(user_id, "note")
        if not allowed:
            await message.answer(error_msg)
            return
        try:
            from gpt import summarize_note_text, generate_title_for_note
            from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
            from db_postgresql import save_document
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
            await add_chunks_to_vector_db(document_id, user_id, chunks)

            await message.answer(t("note_saved", lang, title=title), parse_mode="HTML")
            await send_note_controls(message, document_id)
            user_states[user_id] = None
            
            await record_user_action(user_id, "note")
            
            from keyboards import show_main_menu
            await show_main_menu(message, lang)
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "save_memory_note"})
            await message.answer(get_user_friendly_message(e, lang))
            return

    # Обработка редактирования профиля
    elif isinstance(current_state, dict) and current_state.get("mode") == "editing_profile":
        # ✅ Отмена уже обработана выше, убираем дублирующую проверку
        try:
            state = user_states[user_id]
            field = state.get("field")
            
            if not field:
                await message.answer("❌ Ошибка состояния редактирования")
                user_states[user_id] = None
                return
            
            # Обновляем поле
            success, response_message = await ProfileManager.update_field(
                user_id, field, message.text, lang
            )
            
            if success:
                await message.answer(
                    response_message,
                    reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
                )
                user_states[user_id] = None
                # ✅ ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ после успешного обновления
                from keyboards import show_main_menu
                await show_main_menu(message, lang)
            else:
                # Если ошибка валидации, остаемся в том же поле
                await message.answer(response_message)
                # Показываем клавиатуру снова для продолжения ввода
                from profile_keyboards import cancel_keyboard
                await message.answer(
                    "Попробуйте ещё раз:",
                    reply_markup=cancel_keyboard(lang)
                )
            
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "edit_profile_field"})
            await message.answer(
                "❌ Ошибка обновления профиля",
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
            user_states[user_id] = None
            # ✅ ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ при ошибке
            from keyboards import show_main_menu
            await show_main_menu(message, lang)
            return

    # Обработка редактирования лекарств
    elif current_state == "editing_medications":
        try:
            from db_postgresql import get_medications, replace_medications
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
                    
                    # ✅ ИСПРАВЛЕНИЕ: показываем главное меню после обновления лекарств
                    from keyboards import show_main_menu
                    await show_main_menu(message, lang)
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
            
            # ✅ НОВАЯ ЛОГИКА: Проверяем нужно ли показать upsell для сообщений
            await NotificationSystem.check_and_notify_limits(
                message, user_id, action_type="message"
            )
            
            # 🔍 ДЕТАЛЬНАЯ ОБРАБОТКА ВОПРОСА С ЛОГИРОВАНИЕМ
            try:
                prompt_data = await process_user_question_detailed(user_id, user_input)
                
                # Извлекаем данные из результата
                profile_text = prompt_data["profile_text"]
                summary_text = prompt_data["summary_text"]
                chunks_text = prompt_data["chunks_text"]
                chunks_found = prompt_data["chunks_found"]
                lang = prompt_data["lang"]
                
            except Exception as e:
                # Fallback на старую логику если что-то пошло не так
                print(f"❌ Ошибка детального логирования: {e}")
                print("🔄 Переключаемся на упрощенную обработку...")
                
                # Упрощенная версия (ваш старый код)
                from gpt import enrich_query_for_vector_search
                try:
                    refined_query = await enrich_query_for_vector_search(user_input)
                    print(f"🔍 Запрос: '{user_input}' → улучшен для поиска ({len(refined_query)} симв.)")
                except OpenAIError:
                    refined_query = user_input
                    print(f"🔍 Запрос: '{user_input}' (GPT недоступен)")

                # Простой поиск БЕЗ исключений
                vector_chunks = await search_similar_chunks(user_id, refined_query, limit=10)
                keyword_chunks = await keyword_search_chunks(user_id, user_input, limit=10)
                
                # Получаем только сводку разговора
                summary_text, _ = await get_conversation_summary(user_id)

                def filter_chunks_simple(chunks, limit=5):
                    """Простая фильтрация без исключений документов"""
                    filtered_texts = []
                    for chunk in chunks:
                        chunk_text = chunk.get("chunk_text", "")
                        if chunk_text.strip():  # Только непустые чанки
                            filtered_texts.append(chunk_text)
                            if len(filtered_texts) >= limit:
                                break
                    return filtered_texts

                vector_texts = filter_chunks_simple(vector_chunks, limit=4)
                keyword_texts = filter_chunks_simple(keyword_chunks, limit=2)
                all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
                chunks_text = "\n\n".join(all_chunks[:6])
                chunks_found = len(all_chunks)
                
                # Краткое логирование БЕЗ excluded_doc_id
                print(f"🧠 Найдено: {len(vector_chunks)} векторных + {len(keyword_chunks)} ключевых = {chunks_found} итого")
                
                # Создаем данные для fallback
                profile_text = await format_user_profile(user_id)
                lang = await get_user_language(user_id)

            # ==========================================
            # ОТПРАВКА В GPT (исправленная версия)
            # ==========================================

            # Проверка лимитов GPT-4o
            use_gpt4o = await check_gpt4o_limit(user_id)

            try:
                # Получаем недавние сообщения для контекста
                try:
                    from db_postgresql import get_last_messages
                    recent_messages = await get_last_messages(user_id, limit=6)
                    
                    # Форматируем недавние сообщения
                    context_lines = []
                    for msg in recent_messages:
                        if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                            role = "USER" if msg[0] == 'user' else "BOT"
                            content = str(msg[1])[:100]  # Ограничиваем длину
                            context_lines.append(f"{role}: {content}")
                        else:
                            print(f"⚠️ Неожиданный формат сообщения: {msg}")
                    
                    context_text = "\n".join(context_lines)
                    
                except Exception as e:
                    context_text = ""
                    print(f"⚠️ Не удалось получить контекст сообщений: {e}")

                 # ✅ НОВАЯ ЛОГИКА ВЫБОРА МОДЕЛИ
                # Проверяем есть ли у пользователя лимиты
                has_premium_limits = await check_gpt4o_limit(user_id)
                
                # ✅ ОПРЕДЕЛЯЕМ КАКУЮ МОДЕЛЬ ИСПОЛЬЗОВАТЬ
                if has_premium_limits:
                    # У пользователя есть лимиты → используем Gemini
                    use_gemini = True
                    model_name = "Gemini 2.5 Flash"
                    print(f"💎 Пользователь {user_id} имеет лимиты → используем {model_name}")
                else:
                    # У пользователя нет лимитов → используем GPT-4o mini
                    use_gemini = False
                    model_name = "GPT-4o-mini"
                    print(f"🆓 Пользователь {user_id} без лимитов → используем {model_name}")

                # Правильный вызов ask_doctor с вашими параметрами
                response = await ask_doctor(
                    profile_text=profile_text,
                    summary_text=summary_text, 
                    chunks_text=chunks_text,
                    context_text=context_text,
                    user_question=user_input,
                    lang=lang,
                    user_id=user_id,
                    use_gemini=use_gemini
                )
                
                print(f"🤖 {'GPT-4o' if use_gpt4o else 'GPT-4o-mini'} | Чанков: {chunks_found}")
                
                # Остальная логика отправки ответа пользователю остается без изменений
                if response:
                    await message.answer(response)
                    await save_message(user_id, "assistant", response)
                    await maybe_update_summary(user_id)
                    print(f"✅ Ответ отправлен: {len(response)} символов")
                else:
                    await message.answer(get_user_friendly_message("Не удалось получить ответ", lang))
                    
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "gpt_request"})
                await message.answer(get_user_friendly_message(e, lang))
                    
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "message_processing"})
            await message.answer(get_user_friendly_message(e, lang))

@dp.callback_query(lambda c: c.data == "settings_profile")
@handle_telegram_errors  
async def handle_profile_settings(callback: types.CallbackQuery):
    """Показать профиль пользователя"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем текст профиля
    profile_text = await ProfileManager.get_profile_text(user_id, lang)
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=profile_view_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "edit_profile")
@handle_telegram_errors
async def handle_edit_profile(callback: types.CallbackQuery):
    """Показать меню редактирования профиля"""
    lang = await get_user_language(callback.from_user.id)
    
    await callback.message.edit_text(
        t("edit_profile_title", lang),
        reply_markup=profile_edit_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_profile")
@handle_telegram_errors
async def handle_back_to_profile(callback: types.CallbackQuery):
    """Вернуться к просмотру профиля"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Сбрасываем состояние редактирования
    user_states[user_id] = None
    
    profile_text = await ProfileManager.get_profile_text(user_id, lang)
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=profile_view_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_settings")
@handle_telegram_errors
async def handle_back_to_settings(callback: types.CallbackQuery):
    """Вернуться в меню настроек"""
    lang = await get_user_language(callback.from_user.id)
    
    await callback.message.edit_text(
        t("settings_menu_title", lang),
        reply_markup=settings_keyboard(lang)
    )
    await callback.answer()

# HANDLERS для редактирования конкретных полей
@dp.callback_query(lambda c: c.data.startswith("edit_field_"))
@handle_telegram_errors
async def handle_edit_field(callback: types.CallbackQuery):
    """Начать редактирование конкретного поля"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    field = callback.data.replace("edit_field_", "")
    
    # Устанавливаем состояние редактирования
    user_states[user_id] = {
        "mode": "editing_profile",
        "field": field
    }
    
    if field in ["name", "height_cm", "weight_kg", "allergies"]:
        # Текстовый ввод
        prompts = {
            "name": "enter_new_name",
            "height_cm": "enter_new_height", 
            "weight_kg": "enter_new_weight",
            "allergies": "enter_new_allergies"
        }
        
        await callback.message.answer(
            t(prompts[field], lang),
            reply_markup=cancel_keyboard(lang)
        )
        
    elif field == "smoking":
        # Выбор из кнопок
        await callback.message.edit_text(
            t("choose_smoking", lang),
            reply_markup=smoking_choice_keyboard(lang)
        )
        
    elif field == "alcohol":
        await callback.message.edit_text(
            t("choose_alcohol", lang),
            reply_markup=alcohol_choice_keyboard(lang)
        )
        
    elif field == "physical_activity":
        await callback.message.edit_text(
            t("choose_activity", lang),
            reply_markup=activity_choice_keyboard(lang)
        )
        
    elif field == "language":
        await callback.message.edit_text(
            t("choose_language", lang),
            reply_markup=language_choice_keyboard()
        )
    
    await callback.answer()

# HANDLERS для выбора из кнопок
@dp.callback_query(lambda c: c.data.startswith(("smoking_", "alcohol_", "activity_", "lang_")))
@handle_telegram_errors
async def handle_choice_selection(callback: types.CallbackQuery):
    """Обработка выбора из кнопок"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    state = user_states.get(user_id)
    if not state or state.get("mode") != "editing_profile":
        await callback.answer("❌ Ошибка состояния")
        return
    
    field = state.get("field")
    choice = callback.data
    
    print(f"🔧 DEBUG: field={field}, choice={choice}")  # Для отладки
    
    # Обработка выбора языка
    if choice.startswith("lang_"):
        new_lang = choice.replace("lang_", "")
        success, message = await ProfileManager.update_field(user_id, "language", new_lang, lang)
        
        if success:
            # Обновляем язык в состоянии
            lang = new_lang
        
        await callback.message.edit_text(message, parse_mode="HTML")
        user_states[user_id] = None
        
        # ✅ ДОБАВЛЕНО: показываем главное меню после смены языка
        from keyboards import show_main_menu
        await show_main_menu(callback.message, lang)
        
        await callback.answer()
        return
    
    # ✅ ИСПРАВЛЕННЫЙ маппинг для других полей
    # Определяем реальное поле в базе данных по callback data
    if choice.startswith("smoking_"):
        db_field = "smoking"
    elif choice.startswith("alcohol_"):
        db_field = "alcohol"
    elif choice.startswith("activity_"):
        db_field = "physical_activity"  # ✅ ВАЖНО: правильное имя поля в БД
    else:
        await callback.answer("❌ Неизвестный тип выбора")
        return
    
    # ✅ ИСПРАВЛЕНО: получаем читаемое значение из CHOICE_MAPPINGS
    if db_field in CHOICE_MAPPINGS and choice in CHOICE_MAPPINGS[db_field]:
        readable_value = CHOICE_MAPPINGS[db_field][choice][lang]
        print(f"🔧 DEBUG: readable_value={readable_value}")  # Для отладки
    else:
        # Fallback на прямое значение
        readable_value = choice
        print(f"⚠️ DEBUG: Fallback value={readable_value}")
    
    # Обновляем поле
    success, message = await ProfileManager.update_field(user_id, db_field, readable_value, lang)
    
    if success:
        await callback.message.edit_text(message, parse_mode="HTML")
        user_states[user_id] = None
        
        # ✅ ДОБАВЛЕНО: показываем главное меню после успешного обновления
        from keyboards import show_main_menu
        await show_main_menu(callback.message, lang)
    else:
        await callback.message.edit_text(message)
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_edit")
@handle_telegram_errors
async def handle_cancel_edit(callback: types.CallbackQuery):
    """Отменить редактирование"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    user_states[user_id] = None
    
    await callback.message.edit_text(
        t("profile_edit_cancelled", lang),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "settings_faq")
@handle_telegram_errors
async def handle_faq_settings(callback: types.CallbackQuery):
    """Обработка кнопки FAQ (заглушка)"""
    lang = await get_user_language(callback.from_user.id)
    
    await callback.message.edit_text(
        t("faq_coming_soon", lang)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "settings_subscription")
@handle_telegram_errors
async def handle_subscription_settings(callback: types.CallbackQuery):
    """Обработка кнопки Подписка в настройках"""
    await SubscriptionHandlers.show_subscription_menu(callback)

# 2. НОВЫЕ обработчики для покупки подписок
@dp.callback_query(lambda c: c.data.startswith("buy_"))
@handle_telegram_errors
async def handle_purchase_request(callback: types.CallbackQuery):
    """Обработка запросов на покупку пакетов"""
    package_id = callback.data.replace("buy_", "")
    await SubscriptionHandlers.handle_purchase_request(callback, package_id)

@dp.callback_query(lambda c: c.data.startswith("confirm_purchase_"))
@handle_telegram_errors
async def handle_purchase_confirmation(callback: types.CallbackQuery):
    """Обработка подтверждения покупки"""
    package_id = callback.data.replace("confirm_purchase_", "")
    await SubscriptionHandlers.handle_purchase_confirmation(callback, package_id)

@dp.callback_query(lambda c: c.data.startswith("upgrade_to_"))
@handle_telegram_errors
async def handle_simple_upgrade(callback: types.CallbackQuery):
    """✅ ПРОСТОЙ обработчик апгрейда - находим старую подписку сами"""
    try:
        user_id = callback.from_user.id
        
        # Получаем новый пакет из callback
        new_package_id = callback.data.replace("upgrade_to_", "")
        
        # ✅ ПРОСТАЯ ЛОГИКА: Находим активную подписку в БД
        from db_postgresql import fetch_one
        active_subscription = await fetch_one("""
            SELECT package_id FROM user_subscriptions 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        
        if not active_subscription:
            await callback.answer("❌ Активная подписка не найдена", show_alert=True)
            return
            
        current_package_id = active_subscription[0]
        
        # ✅ ПРОСТО: Отменяем старую, создаем новую
        await SubscriptionHandlers.handle_subscription_upgrade(
            callback, current_package_id, new_package_id
        )
        
    except Exception as e:
        log_error_with_context(e, {
            "action": "simple_upgrade", 
            "user_id": callback.from_user.id
        })
        await callback.answer("❌ Ошибка", show_alert=True)

# 3. НОВЫЕ обработчики управления подписками
@dp.callback_query(lambda c: c.data == "subscription_menu")
@handle_telegram_errors
async def handle_subscription_menu(callback: types.CallbackQuery):
    """Возврат в меню подписок"""
    await SubscriptionHandlers.show_subscription_menu(callback)

@dp.callback_query(lambda c: c.data == "show_limits")
@handle_telegram_errors
async def handle_show_limits(callback: types.CallbackQuery):
    """Показ подробной информации о лимитах"""
    await SubscriptionHandlers.show_user_limits(callback)

@dp.callback_query(lambda c: c.data == "cancel_subscription")
@handle_telegram_errors
async def handle_cancel_subscription_request(callback: types.CallbackQuery):
    """Запрос на отмену подписки"""
    await SubscriptionHandlers.handle_cancel_subscription_request(callback)

@dp.callback_query(lambda c: c.data == "confirm_cancel_subscription")
@handle_telegram_errors
async def handle_cancel_subscription_confirmation(callback: types.CallbackQuery):
    """Подтверждение отмены подписки"""
    await SubscriptionHandlers.handle_cancel_subscription_confirmation(callback)

# 4. НОВЫЕ обработчики upsell уведомлений
@dp.callback_query(lambda c: c.data == "dismiss_upsell")
@handle_telegram_errors
async def handle_dismiss_upsell(callback: types.CallbackQuery):
    """Закрытие upsell уведомления"""
    await SubscriptionHandlers.dismiss_upsell(callback)

@dp.callback_query(lambda c: c.data == "subscription_current")
@handle_telegram_errors
async def handle_current_subscription(callback: types.CallbackQuery):
    """Обработка нажатия на текущую подписку"""
    await callback.answer("✅ Это ваша текущая подписка", show_alert=True)

@dp.callback_query(lambda c: c.data == "cancel_photo_analysis")
async def process_cancel_photo_analysis(callback_query: types.CallbackQuery):
    """Отмена анализа фото"""
    await cancel_photo_analysis(callback_query)

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

# 🚀 ЗАМЕНИТЕ ФУНКЦИЮ main() В КОНЦЕ ВАШЕГО main.py НА ЭТУ:

@handle_telegram_errors
async def main():
    """
    🔧 ИСПРАВЛЕННАЯ функция main() с правильной инициализацией баз данных
    """
    print("🚀 Запуск медицинского бота...")
    
    try:
        # 🔧 1. ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ USER STATE
        from user_state_manager import UserStateManager
        user_state_manager = UserStateManager(ttl_minutes=60)
        print("✅ Бот запущен. Ожидаю сообщения...")
        
        # 💳 2. ПРОВЕРКА STRIPE
        print("🔍 Проверка настройки Stripe...")
        stripe_ok = check_stripe_setup()  # БЕЗ await - функция не async!
        if stripe_ok:
            print("✅ Соединение с Stripe API успешно")
            print("💳 Stripe готов к работе")
        
        # 🌐 3. ЗАПУСК WEBHOOK СЕРВЕРА
        from webhook_subscription_handler import start_webhook_server
        webhook_runner = await start_webhook_server(bot, port=8080)
        
        # 🗄️ 4. ИНИЦИАЛИЗАЦИЯ POSTGRESQL (КРИТИЧНО!)
        print("🔗 Подключение к PostgreSQL...")
        await initialize_db_pool(max_connections=10)
        print("🗄️ Database pool готов")
        
        # 🧠 5. ИНИЦИАЛИЗАЦИЯ VECTOR DB (ПОСЛЕ PostgreSQL!)
        from vector_db_postgresql import initialize_vector_db
                
        await initialize_vector_db()
        print("🧠 Vector database готова")
        
        # 🤖 6. ПРОВЕРКА OPENAI
        openai_status = await check_openai_status()
        if openai_status:
            print("✅ OpenAI API доступен")
        else:
            print("⚠️ Проблемы с OpenAI API")
        
       
        print("🚦 Rate Limiter активирован")
        print("   - Сообщения: 10/мин")
        print("   - Документы: 3/5мин") 
        print("   - Изображения: 3/10мин")
        print("   - Заметки: 5/5мин")
        
        # 🚀 8. ЗАПУСК БОТА
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        log_error_with_context(e, {"action": "main_startup"})
        
    finally:
        # 🧹 ОЧИСТКА РЕСУРСОВ
        print("🧹 Закрытие соединений...")
        try:
            await close_db_pool()
            print("✅ Базы данных закрыты")
        except Exception as e:
            print(f"⚠️ Ошибка закрытия баз: {e}")

# 🎯 ТОЧКА ВХОДА (в самом конце файла, замените существующую)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Фатальная ошибка: {e}")