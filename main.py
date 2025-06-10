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
from keyboards import main_menu_keyboard, settings_keyboard
from profile_keyboards import (
    profile_view_keyboard, profile_edit_keyboard, smoking_choice_keyboard,
    alcohol_choice_keyboard, activity_choice_keyboard, language_choice_keyboard, cancel_keyboard
    )
from profile_manager import ProfileManager, CHOICE_MAPPINGS
from documents import handle_show_documents, handle_ignore_document
from save_utils import maybe_update_summary, format_user_profile
from vector_utils import search_similar_chunks, keyword_search_chunks
from vector_db import delete_document_from_vector_db
from rate_limiter import check_rate_limit, record_user_action, get_rate_limit_stats
from db_pool import initialize_db_pool, close_db_pool, get_db_stats, db_health_check
from gpt import ask_gpt, ask_doctor, check_openai_status, fallback_response, fallback_summarize
from subscription_manager import check_document_limit, SubscriptionManager
from stripe_config import check_stripe_setup
from subscription_handlers import SubscriptionHandlers, upsell_tracker
from notification_system import NotificationSystem
from stripe_manager import StripeManager

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

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_upload_image"))
@handle_telegram_errors
async def ask_for_image(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # ✅ НОВАЯ ЛОГИКА: Проверяем лимиты и показываем уведомления
    can_upload = await NotificationSystem.check_and_notify_limits(
        message, user_id, action_type="image"
    )
    
    if not can_upload:
        return  # Лимиты исчерпаны, уведомление уже показано
    
    # Если лимиты есть - разрешаем загрузку
    user_states[message.from_user.id] = "awaiting_image_analysis"
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
async def show_settings_menu_new(message: types.Message):
    """Показать меню настроек"""
    lang = await get_user_language(message.from_user.id)
    
    await message.answer(
        t("settings_menu_title", lang),
        reply_markup=settings_keyboard(lang)
    )

@dp.message(lambda msg: msg.text == "/reset")
@handle_telegram_errors
async def reset_user(message: types.Message):
    user_id = message.from_user.id
    from db import delete_user_completely

    await delete_user_completely(user_id)
    lang = "ru"  # ✅ ИСПРАВЛЕНО: используем дефолтный язык после удаления
    await message.answer(t("reset_done", lang))

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

@dp.message(lambda msg: msg.text and msg.text.startswith("/test_payment"))
@handle_telegram_errors
async def test_payment_handler(message: types.Message):
    """
    Тестовый обработчик для симуляции успешного платежа
    Использовать только в тестовом режиме!
    Формат: /test_payment session_id
    """
    if not message.text.startswith("/test_payment "):
        await message.answer("❌ Формат: /test_payment session_id")
        return
    
    session_id = message.text.replace("/test_payment ", "").strip()
    
    try:
        success, result_message = await StripeManager.handle_successful_payment(session_id)
        
        if success:
            await message.answer(f"✅ Тестовый платеж обработан:\n{result_message}")
        else:
            await message.answer(f"❌ Ошибка обработки платежа:\n{result_message}")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# Добавьте этот обработчик в main.py для тестирования

@dp.message(lambda msg: msg.text and msg.text.startswith("/check_payment"))
@handle_telegram_errors
async def check_payment_handler(message: types.Message):
    """
    Проверяет статус последнего платежа пользователя
    Команда: /check_payment
    """
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # Ищем последний pending платеж пользователя
        from db_pool import fetch_one, fetch_all
        
        pending_payment = await fetch_one("""
            SELECT stripe_session_id, package_id, created_at, amount_usd
            FROM transactions 
            WHERE user_id = ? AND status = 'pending'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        if not pending_payment:
            await message.answer(
                "❌ Нет ожидающих платежей\n"
                "💡 Сначала создайте ссылку для оплаты через меню подписок"
            )
            return
        
        session_id, package_id, created_at, amount = pending_payment
        
        # Проверяем статус в Stripe
        import stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            stripe_status = session.payment_status
            
            await message.answer(
                f"📋 <b>Статус последнего платежа:</b>\n\n"
                f"💳 Session ID: <code>{session_id}</code>\n"
                f"📦 Пакет: {package_id}\n"
                f"💰 Сумма: ${amount}\n"
                f"📅 Создан: {created_at[:16]}\n"
                f"🔍 Статус Stripe: <b>{stripe_status}</b>\n\n"
                f"💡 Если статус 'paid' - нажмите /process_payment",
                parse_mode="HTML"
            )
            
        except Exception as stripe_error:
            await message.answer(f"❌ Ошибка проверки Stripe: {stripe_error}")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(lambda msg: msg.text and msg.text == "/process_payment")
@handle_telegram_errors
async def process_payment_handler(message: types.Message):
    """
    Обрабатывает последний успешный платеж пользователя
    Команда: /process_payment
    """
    user_id = message.from_user.id
    
    try:
        # Ищем последний pending платеж
        from db_pool import fetch_one
        
        pending_payment = await fetch_one("""
            SELECT stripe_session_id 
            FROM transactions 
            WHERE user_id = ? AND status = 'pending'
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        if not pending_payment:
            await message.answer("❌ Нет платежей для обработки")
            return
        
        session_id = pending_payment[0]
        
        # Обрабатываем платеж
        success, result_message = await StripeManager.handle_successful_payment(session_id)
        
        if success:
            await message.answer(f"✅ <b>Платеж обработан!</b>\n\n{result_message}", parse_mode="HTML")
            
            # Показываем обновленные лимиты
            limits = await SubscriptionManager.get_user_limits(user_id)
            await message.answer(
                f"📊 <b>Ваши новые лимиты:</b>\n"
                f"📄 Документы: <b>{limits['documents_left']}</b>\n"
                f"🤖 GPT-4o запросы: <b>{limits['gpt4o_queries_left']}</b>",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"❌ Ошибка обработки: {result_message}")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(lambda msg: msg.text and msg.text == "/my_limits")
@handle_telegram_errors
async def show_my_limits_handler(message: types.Message):
    """
    Показывает текущие лимиты пользователя
    Команда: /my_limits
    """
    user_id = message.from_user.id
    
    try:
        limits = await SubscriptionManager.get_user_limits(user_id)
        
        if limits:
            expiry_text = ""
            if limits.get('expires_at'):
                try:
                    from datetime import datetime
                    expiry_date = datetime.fromisoformat(limits['expires_at'])
                    expiry_text = f"\n⏰ Истекает: <b>{expiry_date.strftime('%d.%m.%Y')}</b>"
                except:
                    pass
            
            await message.answer(
                f"📊 <b>Ваши текущие лимиты:</b>\n\n"
                f"📄 Документы: <b>{limits['documents_left']}</b>\n"
                f"🤖 GPT-4o запросы: <b>{limits['gpt4o_queries_left']}</b>\n"
                f"💳 Тип: <b>{limits['subscription_type']}</b>"
                f"{expiry_text}",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Не удалось загрузить лимиты")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# Добавьте также помощь по командам
@dp.message(lambda msg: msg.text and msg.text == "/help_payments")
@handle_telegram_errors
async def help_payments_handler(message: types.Message):
    """Помощь по тестированию платежей"""
    
    help_text = """
🧪 <b>Команды для тестирования платежей:</b>

<code>/check_payment</code> - проверить статус последнего платежа
<code>/process_payment</code> - обработать успешный платеж  
<code>/my_limits</code> - показать текущие лимиты

📝 <b>Как тестировать:</b>
1. Создайте ссылку через меню подписок
2. Оплатите тестовой картой: 4242 4242 4242 4242
3. Используйте /check_payment для проверки
4. Если статус 'paid' - используйте /process_payment
5. Проверьте лимиты через /my_limits

⚠️ <b>Только для TEST режима!</b>
"""
    
    await message.answer(help_text, parse_mode="HTML")

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
    if current_state in ["awaiting_document", "awaiting_image_analysis"]:
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
                
        elif current_state == "awaiting_image_analysis":
            allowed, error_msg = await check_rate_limit(user_id, "image")
            if not allowed:
                await message.answer(error_msg)
                return
            try:
                from upload import handle_image_analysis
                await handle_image_analysis(message, bot)
                await record_user_action(user_id, "image")
                return
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "image_analysis"})
                await message.answer(get_user_friendly_message(e, lang))
                return
        else:
            # Файл отправлен, но пользователь не в режиме ожидания
            await message.answer(t("unsupported_input", lang))
            return

    # Обработка регистрации
    if await handle_registration_step(user_id, message):
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
            # (каждые 5 сообщений если нет GPT-4o лимитов)
            await NotificationSystem.check_and_notify_limits(
                message, user_id, action_type="message"
            )
            
            # Получаем данные для контекста (код остается тот же)
            summary_text, _ = await get_conversation_summary(user_id)
            last_doc_id, last_summary = await get_last_summary(user_id)
            exclude_texts = last_summary.strip().split("\n\n")

            # Безопасный вызов GPT для улучшения запроса
            try:
                from gpt import enrich_query_for_vector_search
                refined_query = await enrich_query_for_vector_search(user_input)
                print(f"\n🧠 Переформулированный запрос: {refined_query}\n")
            except OpenAIError:
                refined_query = user_input
                print("⚠️ Использую оригинальный запрос из-за недоступности GPT")

            # Поиск в векторной базе (код остается тот же)
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

            # Подготовка контекста (код остается тот же)
            MAX_LEN = 300
            last_messages = await get_last_messages(user_id, limit=7)
            if last_messages and last_messages[-1][0] == "user" and last_messages[-1][1] == message.text:
                last_messages = last_messages[:-1]
            context_text = "\n".join([
                f"{role.upper()}: {msg[:MAX_LEN]}" for role, msg in last_messages
            ])

            profile = await get_user_profile(user_id)
            profile_text = format_user_profile(profile)

            # ✅ ОБНОВЛЕНО: ask_doctor уже содержит логику выбора модели на основе лимитов
            try:
                gpt_response = await ask_doctor(
                    profile_text=profile_text,
                    summary_text=summary_text,
                    last_summary=last_summary,
                    chunks_text=chunks_text,
                    context_text=context_text,
                    user_question=message.text,
                    lang=lang,
                    user_id=user_id  # ✅ ВАЖНО: передаем user_id для проверки лимитов
                )
            except OpenAIError as e:
                gpt_response = fallback_response(message.text, lang)
                print(f"⚠️ Используется fallback ответ: {e}")

            await save_message(user_id, "bot", gpt_response)

            # Безопасная отправка ответа (код остается тот же)
            try:
                await message.answer(gpt_response)
            except Exception as e:
                print(f"⚠️ Ошибка отправки HTML, отправляю plain text: {e}")
                from html import escape
                safe_response = escape(gpt_response)
                await message.answer(safe_response, parse_mode=None)
                
            await record_user_action(user_id, "message")

            # Обновление резюме разговора (код остается тот же)
            try:
                await maybe_update_summary(user_id)
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "update_summary"})
                
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "handle_main_question"})
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

@handle_telegram_errors
async def main():
    print("✅ Бот запущен. Ожидаю сообщения...")
    
    # ✅ НОВАЯ ПРОВЕРКА: Проверяем настройку Stripe
    if not check_stripe_setup():
        print("⚠️ Stripe не настроен - платежи будут недоступны")
        print("💡 Добавьте STRIPE_PUBLISHABLE_KEY и STRIPE_SECRET_KEY в .env файл")
    else:
        print("💳 Stripe готов к работе")
    
    from user_state_manager import user_state_manager
    await user_state_manager.start_cleanup_loop()
    
    # Инициализация пула базы данных (код остается тот же)
    try:
        await initialize_db_pool(max_connections=10)
        print("🗄️ Database pool готов")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # Проверяем состояние OpenAI при запуске (код остается тот же)
    if await check_openai_status():
        print("✅ OpenAI API доступен")
    else:
        print("⚠️ OpenAI API недоступен - бот будет работать в ограниченном режиме")
    
    # Инициализируем Rate Limiter (код остается тот же)
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
        await user_state_manager.stop_cleanup_loop()
        await close_db_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
    except Exception as e:
        print("❌ Ошибка при запуске:", e)