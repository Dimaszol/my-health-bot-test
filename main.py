import asyncio
import os
import html
import logging
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

from db_postgresql import (
    get_user, save_document, update_document_title, is_fully_registered, get_user_name,
    get_document_by_id, delete_document, save_message, get_last_messages, get_conversation_summary,
    get_user_language, t, get_all_values_for_key, initialize_db_pool, close_db_pool, set_user_language, save_user
)
from registration import user_states, start_registration, handle_registration_step
from error_handler import handle_telegram_errors, BotError, OpenAIError, get_user_friendly_message, log_error_with_context, check_openai_health
from keyboards import main_menu_keyboard, settings_keyboard, show_main_menu
from profile_keyboards import (
    profile_view_keyboard, profile_edit_keyboard, smoking_choice_keyboard,
    alcohol_choice_keyboard, activity_choice_keyboard, language_choice_keyboard, cancel_keyboard
)
from profile_manager import ProfileManager, CHOICE_MAPPINGS
from documents import handle_show_documents, handle_ignore_document
from save_utils import maybe_update_summary, format_user_profile
from rate_limiter import check_rate_limit, record_user_action
from vector_db_postgresql import initialize_vector_db, search_similar_chunks, keyword_search_chunks
from gpt import ask_doctor, check_openai_status, fallback_summarize
from subscription_manager import SubscriptionManager, check_gpt4o_limit, spend_gpt4o_limit
from stripe_config import check_stripe_setup
from subscription_handlers import SubscriptionHandlers, upsell_tracker
from notification_system import NotificationSystem
from stripe_manager import StripeManager
from prompt_logger import process_user_question_detailed
from photo_analyzer import handle_photo_analysis, handle_photo_question, cancel_photo_analysis
from analytics_system import Analytics
from faq_handler import handle_faq_main, handle_faq_section
from promo_manager import PromoManager, check_promo_on_message
from safe_message_answer import send_error_message, send_response_message
from user_checker import full_process_debug_7374723347

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)

# Убираем спам от сторонних библиотек
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Основной логгер
logger = logging.getLogger(__name__)

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
@handle_telegram_errors
async def send_welcome(message: types.Message):
    """✅ ИСПРАВЛЕННЫЙ обработчик команды /start"""
    
    user_id = message.from_user.id
    
    try:
        # 1️⃣ Получаем данные пользователя
        user_data = await get_user(user_id)
        auto_lang = detect_user_language(message.from_user)
        
        # 2️⃣ Определяем, новый это пользователь или нет
        is_new_user = user_data is None
        
        # 📊 Отслеживаем аналитику
        await Analytics.track_user_started(user_id, auto_lang, is_new_user)
        
        # 3️⃣ НОВЫЙ ПОЛЬЗОВАТЕЛЬ
        if user_data is None:
            await set_user_language(user_id, auto_lang, message.from_user)
            
            from registration import show_gdpr_welcome
            await show_gdpr_welcome(user_id, message, auto_lang)
            return
            
        # 4️⃣ СУЩЕСТВУЮЩИЙ ПОЛЬЗОВАТЕЛЬ - проверяем GDPR согласие
        from db_postgresql import has_gdpr_consent
        if not await has_gdpr_consent(user_id):
            lang = await get_user_language(user_id) 
            from registration import show_gdpr_welcome
            await show_gdpr_welcome(user_id, message, lang)
            return
        
        # 5️⃣ ПРОВЕРЯЕМ РЕГИСТРАЦИЮ (имя + год рождения для медицинских рекомендаций)
        lang = await get_user_language(user_id)
        
        if await is_fully_registered(user_id):
            # ✅ У пользователя есть имя и год рождения - показываем главное меню
            name = user_data.get('name', 'Пользователь')
            
            await message.answer(
                t("welcome_back", lang, name=name), 
                reply_markup=main_menu_keyboard(lang)
            )
        else:
            
            from registration import start_registration
            await start_registration(user_id, message)
            
    except Exception as e:
        log_error_with_context(e, {"action": "start_command", "user_id": user_id})
        await message.answer(t("start_command_error", lang))

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
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="set_lang_de")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk")],
        [InlineKeyboardButton(text="🇷 Русский", callback_data="set_lang_ru")]
        
    ])
    
    await callback.message.edit_text(
        "🇬🇧 Choose your language\n"
        "🇩🇪 Sprache wählen\n"
        "🇺🇦 Оберіть мову інтерфейсу\n"
        "🇷 Выберите язык интерфейса", 
        
        reply_markup=language_keyboard
    )
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("set_lang_"))
@handle_telegram_errors  # ✅ ДОБАВИТЬ ЭТОТ ДЕКОРАТОР!
async def handle_set_language_during_registration(callback: types.CallbackQuery):
    """Обновляем существующий обработчик"""
    user_id = callback.from_user.id
    selected_lang = callback.data.replace("set_lang_", "")
    
    try:  # ✅ ДОБАВИТЬ TRY-CATCH
        # Обновляем язык пользователя
        await set_user_language(user_id, selected_lang)
        
        # ✅ ПРОВЕРЯЕМ: это GDPR экран или обычная регистрация?
        user_data = await get_user(user_id)
        from db_postgresql import has_gdpr_consent
        
        if user_data is None or not await has_gdpr_consent(user_id):
            # Это GDPR экран - показываем дисклеймер заново
            from registration import show_gdpr_welcome
            await show_gdpr_welcome(user_id, callback.message, selected_lang)
        else:
            # Это обычная регистрация - возвращаемся к регистрации
            await start_registration(user_id, callback.message)
    
    except Exception as e:
        try:
            from registration import show_gdpr_welcome
            await show_gdpr_welcome(user_id, callback.message, selected_lang)
        except Exception as e2:
            await callback.answer("❌ Произошла ошибка. Попробуйте /start", show_alert=True)
    
    await callback.answer()

@dp.callback_query(lambda callback: callback.data == "gdpr_consent_agree")
@handle_telegram_errors
async def handle_gdpr_consent(callback: types.CallbackQuery):
    """Обработка GDPR согласия"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # ✅ ПОЛЬЗОВАТЕЛЬ УЖЕ СУЩЕСТВУЕТ (создан в set_user_language)
        # Просто обновляем GDPR согласие
        from db_postgresql import set_gdpr_consent
        success = await set_gdpr_consent(user_id, True)
        
        if not success:
            await callback.answer(
                t("error_database_error", lang), 
                show_alert=True
            )
            return
        
        # ✅ ПОКАЗЫВАЕМ ПОДТВЕРЖДЕНИЕ
        await callback.message.edit_text(
            t("gdpr_consent_given", lang)
        )
        
        # Небольшая задержка для лучшего UX
        await asyncio.sleep(1)
        
        # ✅ ЗАПУСКАЕМ РЕГИСТРАЦИЮ
        from registration import start_registration
        await start_registration(user_id, callback.message)
        
    except Exception as e:
        log_error_with_context(e, {"function": "handle_gdpr_consent", "user_id": user_id})
        await callback.answer(
            t("start_command_error", lang), 
            show_alert=True
        )
    
    await callback.answer()

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
    
    # ✅ ДОБАВЛЯЕМ: Показываем кнопку "Отмена" вместо главного меню
    from keyboards import cancel_keyboard
    await message.answer(
        t("please_send_file", lang), 
        reply_markup=cancel_keyboard(lang)  # ← ВОТ ЭТО ВАЖНО!
    )

@dp.message(lambda msg: msg.text in get_all_values_for_key("main_note"))
@handle_telegram_errors
async def prompt_memory_note(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    user_states[message.from_user.id] = "awaiting_memory_note"
    
    # ✅ ИСПРАВЛЕНО: используем cancel_keyboard из keyboards
    from keyboards import cancel_keyboard
    await message.answer(
        t("write_note", lang), 
        reply_markup=cancel_keyboard(lang)
    )

@dp.message(Command("storage_full"))
async def show_full_storage(message):
    if message.from_user.id != 7374723347: return
    
    import os
    try:
        base_path = "/app/persistent_files"
        total_files = 0
        total_size = 0
        result = "📁 **ПОЛНОЕ ХРАНИЛИЩЕ:**\n\n"
        
        # Проходим по всем папкам и файлам
        for root, dirs, files in os.walk(base_path):
            if not files: continue  # Пропускаем пустые папки
            
            # Относительный путь от base_path
            rel_path = root.replace(base_path, "").lstrip("/")
            if not rel_path: rel_path = "root"
            
            # Считаем размер папки
            folder_size = 0
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    folder_size += size
                    total_size += size
                except: pass
            
            total_files += len(files)
            
            # Добавляем в результат
            result += f"📂 **{rel_path}**\n"
            result += f"   📊 {len(files)} файлов, {folder_size/1024/1024:.1f} MB\n"
            
            # Показать первые файлы
            for i, file in enumerate(files[:3]):
                result += f"   📄 {file}\n"
            
            if len(files) > 3:
                result += f"   📄 ... еще {len(files)-3} файлов\n"
            
            result += "\n"
            
            # Ограничение длины сообщения
            if len(result) > 3500:
                result += "... (показано частично)"
                break
        
        result += f"🎯 **ИТОГО:** {total_files} файлов, {total_size/1024/1024:.1f} MB"
        
        await message.answer(result, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

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
        from db_postgresql import format_medications_schedule
        from locales import translations
        
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

@dp.callback_query(lambda c: c.data.startswith("promo_buy:"))
@handle_telegram_errors
async def handle_promo_purchase_callback(callback: types.CallbackQuery):
    """
    💳 Обработчик покупки по промокоду
    """
    logger.info(f"🎫 User {callback.from_user.id} нажал на промокнопку: {callback.data}")
    await PromoManager.handle_promo_purchase(callback)

@dp.callback_query(lambda c: c.data == "promo_dismiss")
@handle_telegram_errors
async def handle_promo_dismiss_callback(callback: types.CallbackQuery):
    """
    ⏰ Обработчик "Может быть позже"
    """
    logger.info(f"⏰ User {callback.from_user.id} отложил промокод")
    await PromoManager.handle_promo_dismiss(callback)

@dp.message(lambda msg: msg.text == "/reset123456")
@handle_telegram_errors
async def reset_user(message: types.Message):
    user_id = message.from_user.id
    from db_postgresql import delete_user_completely

    await delete_user_completely(user_id)
    lang = "ru"  # ✅ ИСПРАВЛЕНО: используем дефолтный язык после удаления
    await message.answer(t("reset_done", lang))

delete_confirmation_states = {}

@dp.callback_query(lambda c: c.data == "delete_profile_data")
@handle_telegram_errors  
async def handle_delete_profile_data(callback: types.CallbackQuery):
    """Первое предупреждение об удалении данных"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("delete_data_confirm", lang),
            callback_data="delete_data_step2"
        )],
        [InlineKeyboardButton(
            text=t("delete_data_cancel", lang), 
            callback_data="back_to_profile"
        )]
    ])
    
    await callback.message.edit_text(
        t("delete_data_warning", lang),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "delete_data_step2")
@handle_telegram_errors
async def handle_delete_step2(callback: types.CallbackQuery):
    """Запрос кода подтверждения"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Устанавливаем состояние ожидания кода
    delete_confirmation_states[user_id] = "awaiting_delete_code"
    
    # Убираем inline клавиатуру и показываем текст с кодом
    await callback.message.edit_text(
        t("delete_data_code_prompt", lang),
        parse_mode="HTML"
    )
    
    # Отправляем новое сообщение с reply клавиатурой для ввода
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("cancel", lang))]],
        resize_keyboard=True
    )
    
    await callback.message.answer(
        t("delete_data_code_input", lang),
        reply_markup=keyboard
    )
    
    await callback.answer()

# ✅ ОБРАБОТЧИК ВВОДА КОДА (тот же что был)
@dp.message(lambda msg: msg.from_user.id in delete_confirmation_states)
@handle_telegram_errors
async def handle_delete_confirmation_code(message: types.Message):
    """Обработка кода подтверждения удаления"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # Проверяем состояние
    if delete_confirmation_states.get(user_id) != "awaiting_delete_code":
        return
    
    # Убираем состояние
    delete_confirmation_states.pop(user_id, None)
    
    # Проверяем код
    if message.text and message.text.strip().upper() == "DELETE":
        # Код верный - выполняем удаление
        await message.answer(
            t("deleting_all_data", lang), 
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        try:
            from db_postgresql import delete_user_completely
            success = await delete_user_completely(user_id)
            
            if success:
                await message.answer(t("delete_data_success", "ru"))  # Дефолтный язык после удаления
            else:
                await message.answer(t("delete_error_contact_support", lang))
                
        except Exception as e:
            await message.answer(t("delete_error_contact_support", lang))
            
    else:
        # Код неверный
        await message.answer(
            t("delete_data_code_wrong", lang),
            reply_markup=types.ReplyKeyboardRemove()
        )
        from keyboards import show_main_menu
        await show_main_menu(message, lang)
        
        # Возвращаемся к профилю
        await asyncio.sleep(1)
        profile_text = await ProfileManager.get_profile_text(user_id, lang)
        await message.answer(
            profile_text,
            reply_markup=profile_view_keyboard(lang),
            parse_mode="HTML"
        )

# 📊 КОМАНДА ДЛЯ СТАТИСТИКИ (ТОЛЬКО ДЛЯ АДМИНА)
ADMIN_USER_ID = 7374723347  # 🔥 ЗАМЕНИТЕ НА ВАШ TELEGRAM ID!

@dp.message(lambda msg: msg.text == "/stats")
@handle_telegram_errors
async def show_stats(message: types.Message):
    """Показать статистику (только для админа)"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_USER_ID:
        return  # Игнорируем, если не админ
    
    try:
        # Получаем статистику за неделю
        stats = await Analytics.get_stats(days=7)
        
        report = f"""📊 <b>СТАТИСТИКА ЗА 7 ДНЕЙ</b>

👥 <b>Пользователи:</b>
• Всего активных: {stats['total_users']}
• Новых: {stats['new_users']}

📈 <b>Активность:</b>
• Регистрации: {stats['registrations']}
• Документы: {stats['documents']}
• Вопросы: {stats['questions']}
• Оплаты: {stats['payments']}

📊 <b>Конверсии:</b>
• Регистрация: {stats['registration_rate']:.1f}%
• Загрузка документов: {stats['document_rate']:.1f}%

🎯 <b>Оценка MVP:</b>"""

        # Простая оценка
        if stats['registration_rate'] > 70:
            report += "\n🟢 Отличная конверсия в регистрацию!"
        elif stats['registration_rate'] > 50:
            report += "\n🟡 Нормальная конверсия в регистрацию"
        else:
            report += "\n🔴 Низкая конверсия - улучшить онбординг"
        
        if stats['document_rate'] > 50:
            report += "\n🟢 Пользователи активно загружают документы!"
        elif stats['document_rate'] > 30:
            report += "\n🟡 Средняя активность с документами"
        else:
            report += "\n🔴 Мало загрузок - улучшить объяснение ценности"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}")

@dp.message(lambda msg: msg.text == "/analytics")
@handle_telegram_errors  
async def show_analytics_help(message: types.Message):
    """Справка по аналитике"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_USER_ID:
        return
    
    help_text = """🔧 <b>КОМАНДЫ АНАЛИТИКИ</b>

📊 <code>/stats</code> - статистика за 7 дней
📈 <code>/stats_today</code> - статистика за сегодня (скоро)
📋 <code>/funnel</code> - анализ воронки (скоро)

💡 <b>Что отслеживаем:</b>
• user_started - запуск бота
• registration_completed - завершение регистрации  
• document_uploaded - загрузка документов
• question_asked - вопросы к ИИ
• payment_completed - оплаты

🎯 <b>Критерии успеха MVP:</b>
• Регистрация > 70%
• Загрузка документов > 50%
• Возврат пользователей > 15%"""

    await message.answer(help_text, parse_mode="HTML")




@dp.message()
@handle_telegram_errors
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    from db_postgresql import has_gdpr_consent
    if not await has_gdpr_consent(user_id):
        # Показываем GDPR дисклеймер вместо обработки сообщения
        from registration import show_gdpr_welcome
        await show_gdpr_welcome(user_id, message, lang)
        return  # ⚠️ ВАЖНО: Прерываем обработку!
    
    # ✅ НОВАЯ ПРОВЕРКА: Обработка устаревших Reply-кнопок (ДОБАВИТЬ ЗДЕСЬ)
    if message.text:
        # ✅ ПОЛНЫЙ СПИСОК всех Reply-кнопок из всех состояний
        reply_buttons = [
            # Основные кнопки управления
            t("skip", lang),                    # ⏭ Пропустить
            t("cancel", lang),                  # ❌ Отмена
            t("cancel_analysis", lang),         # ❌ Отменить (анализ фото)
            
            # Кнопки регистрации - пол
            t("gender_male", lang),             # Мужской/Male/Männlich/Чоловіча
            t("gender_female", lang),           # Женский/Female/Weiblich/Жіноча  
            t("gender_other", lang),            # Другое/Other/Andere/Інше
            
            # Кнопки регистрации - курение
            t("smoking_yes", lang),             # Да/Yes/Ja/Так
            t("smoking_no", lang),              # Нет/No/Nein/Ні
            "Vape",                             # Vape (на всех языках одинаково)
            
            # Кнопки регистрации - алкоголь
            t("alcohol_never", lang),           # Не употребляю/Never/Nie/Не вживаю
            t("alcohol_sometimes", lang),       # Иногда/Sometimes/Manchmal/Іноді
            t("alcohol_often", lang),           # Часто/Often/Oft/Часто
            
            # Кнопки завершения регистрации
            t("complete_profile", lang),        # 📝 Дополнить анкету
            t("finish_registration", lang),     # ✅ Завершить регистрацию
            
            # Кнопки активности (с эмодзи для всех языков)
            "❌ Нет активности", "🚶 Низкая", "🏃 Средняя", "💪 Высокая", "🏆 Профессиональная",
            "❌ Відсутня активність", "🚶 Низька", "🏃 Середня", "💪 Висока", "🏆 Професійна", 
            "❌ No activity", "🚶 Low", "🏃 Medium", "💪 High", "🏆 Professional",
            "❌ Keine Aktivität", "🚶 Niedrig", "🏃 Mittel", "💪 Hoch", "🏆 Professionell",
            
            # Дополнительные варианты на разных языках (для совместимости)
            "Да", "Нет", "Так", "Ні", "Yes", "No", "Ja", "Nein",
            "Мужской", "Женский", "Другое", "Чоловіча", "Жіноча", "Інше",
            "Male", "Female", "Other", "Männlich", "Weiblich", "Andere",
            "Не употребляю", "Иногда", "Часто", "Не вживаю", "Іноді",
            "Never", "Sometimes", "Often", "Nie", "Manchmal", "Oft"
        ]
        
        # Проверяем: это Reply-кнопка И нет активного состояния?
        current_state = user_states.get(user_id)
        is_in_delete_state = user_id in delete_confirmation_states
        
        if message.text in reply_buttons and not current_state and not is_in_delete_state:
            # ✅ Это устаревшая Reply-кнопка!
            await message.answer(
                t("button_expired", lang),
                reply_markup=types.ReplyKeyboardRemove()  # Убираем старую клавиатуру
            )
            
            # Показываем актуальное главное меню
            await show_main_menu(message, lang)
            return

    # Проверяем rate limits
    allowed, rate_message = await check_rate_limit(user_id, "message")
    if not allowed:
        await message.answer(rate_message)
        return

    # Записываем действие
    await record_user_action(user_id, "message")
    
    # ✅ ИСПРАВЛЕНИЕ 1: Обработка отмены ПЕРВЫМ ДЕЛОМ (до всех других проверок)
    if message.text and message.text in [t("cancel", lang)]:
        if user_id in delete_confirmation_states:
            delete_confirmation_states.pop(user_id, None)  # Убираем состояние
            await message.answer(
                t("profile_delete_cancelled", lang),
                reply_markup=types.ReplyKeyboardRemove()
            )
            # ✅ ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ
            await show_main_menu(message, lang)
            return
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
                t("medication_edit_cancelled", lang),
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
                t("operation_cancelled", lang),
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
        
        # ✅ ГЛАВНОЕ ИСПРАВЛЕНИЕ: ВСЕГДА показываем главное меню после отмены
        
        await show_main_menu(message, lang)
        return  # ✅ Выходим из функции, больше ничего не обрабатываем

    # ✅ Теперь получаем состояние пользователя ПОСЛЕ обработки отмены
    current_state = user_states.get(user_id)
    
    # Если пользователь в режиме ожидания файла, но отправил текст
    if current_state == "awaiting_document":
        if message.text is not None:  # Если отправлен текст вместо файла
            await message.answer(t("unrecognized_document", lang))
            user_states[user_id] = None
            # ✅ ДОБАВЛЯЕМ: Возвращаем главное меню
            await show_main_menu(message, lang)
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
            from documents import send_note_controls

            note_text = message.text.strip()
            
            # Безопасные вызовы GPT с обработкой ошибок
            try:
                title = await generate_title_for_note(note_text)
                summary = await summarize_note_text(note_text, lang)
            except OpenAIError as e:
                title = f"Заметка {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                summary = fallback_summarize(note_text, lang)
                await message.answer("⚠️ Обработка недоступна, заметка сохранена в упрощенном виде.")

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
                await show_main_menu(message, lang)
            else:
                # Если ошибка валидации, остаемся в том же поле
                await message.answer(response_message)
                # Показываем клавиатуру снова для продолжения ввода
                await message.answer(
                    t("try_again", lang),
                    reply_markup=cancel_keyboard(lang)
                )
            
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "edit_profile_field"})
            await message.answer(
                t("try_again", lang),
                reply_markup=types.ReplyKeyboardRemove()  # ✅ Убираем клавиатуру
            )
            user_states[user_id] = None
            # ✅ ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ при ошибке
            await show_main_menu(message, lang)
            return

    # Обработка редактирования лекарств
    elif current_state == "editing_medications":
        # ✅ ПРОВЕРЯЕМ ЛИМИТ через существующую систему
        allowed, error_msg = await check_rate_limit(user_id, "pills")
        if not allowed:
            await message.answer(
                error_msg,
                reply_markup=types.ReplyKeyboardRemove()
            )
            user_states[user_id] = None
            await show_main_menu(message, lang)
            return

        try:
            from db_postgresql import get_medications, replace_medications
            from gpt import update_medications_via_gpt
            from save_utils import update_user_profile_medications

            current_list = await get_medications(user_id)
            user_input = message.text.strip()

            try:
                # ✅ ВЫЗЫВАЕМ GPT для обработки лекарств
                new_list = await update_medications_via_gpt(user_input, current_list)
                
                if new_list is not None:
                    # ✅ ЗАПИСЫВАЕМ использование через существующую систему
                    await record_user_action(user_id, "pills")
                    
                    # Сохраняем результат
                    await replace_medications(user_id, new_list)
                    await update_user_profile_medications(user_id)
                    user_states[user_id] = None
                    await message.answer(
                        t("schedule_updated", lang),
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                    await show_main_menu(message, lang)
                else:
                    await message.answer(t("schedule_update_failed", lang))
                    
            except Exception as openai_error:
                # НЕ записываем использование если GPT упал
                await message.answer("⚠️ ИИ-помощник недоступен. Попробуйте обновить лекарства позже.")
                user_states[user_id] = None
                await show_main_menu(message, lang)
                
            return
            
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "edit_medications"})
            await message.answer(get_user_friendly_message(e, lang))
            user_states[user_id] = None
            await show_main_menu(message, lang)
            return

    # Основная обработка вопросов пользователя
    else:
        if message.from_user.id == 7374723347:
            await full_process_debug_7374723347(message.from_user.id, message.text)
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
            
            from subscription_manager import SubscriptionManager
            limits = await SubscriptionManager.get_user_limits(user_id)
            gpt4o_queries_left = limits.get('gpt4o_queries_left', 0)
            subscription_type = limits.get('subscription_type', 'free')
            
            # Увеличиваем счетчик только если нет лимитов И нет подписки
            if gpt4o_queries_left == 0 and subscription_type != 'subscription':
                upsell_tracker.increment_message_count(user_id)
                
                # ✅ ПРАВИЛЬНАЯ ПРОВЕРКА: используем новую функцию
                if upsell_tracker.should_show_upsell(user_id):
                    await SubscriptionHandlers.show_subscription_upsell(
                        message, user_id, reason="better_response"
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
                from error_handler import log_error_with_context
                log_error_with_context(e, {
                    "function": "search_fallback", 
                    "user_id": user_id
                })

                from gpt import enrich_query_for_vector_search
                try:
                    refined_query = await enrich_query_for_vector_search(user_input)
                except OpenAIError:
                    refined_query = user_input

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

                # Создаем данные для fallback
                profile_text = await format_user_profile(user_id)
                lang = await get_user_language(user_id)

            # ==========================================
            # ОТПРАВКА В GPT (исправленная версия)
            # ==========================================

            try:
                # ✅ ОПРЕДЕЛЯЕМ ПОЛНЫЙ КОНТЕКСТ
                if 'prompt_data' in locals() and prompt_data and 'context_text' in prompt_data:
                    # Используем готовый контекст из prompt_logger
                    full_context = prompt_data["context_text"]
                else:
                    # Fallback: собираем контекст из частей
                    context_parts = []
                    
                    context_parts.append(f"📌 Patient profile:\n{profile_text}")
                    context_parts.append(f"🧠 Conversation summary:\n{summary_text}")
                    context_parts.append(f"🔎 Related historical data:\n{chunks_text}")
                    
                    # Получаем недавние сообщения
                    try:
                        recent_messages = await get_last_messages(user_id, limit=6)
                        context_lines = []
                        for msg in recent_messages:
                            if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                                role = "USER" if msg[0] == 'user' else "BOT"
                                content = str(msg[1])[:100]
                                context_lines.append(f"{role}: {content}")
                        recent_context = "\n".join(context_lines)
                        context_parts.append(f"💬 Recent messages:\n{recent_context}")
                    except Exception as e:
                        pass
                    
                    full_context = "\n\n".join(context_parts)

                # ✅ ОПРЕДЕЛЯЕМ КАКУЮ МОДЕЛЬ ИСПОЛЬЗОВАТЬ
                has_premium_limits = await check_gpt4o_limit(user_id)
                
                if has_premium_limits:
                    use_gemini = True
                    model_name = "gpt-4o"
                else:
                    use_gemini = False
                    model_name = "gpt-4o-mini"

                # ✅ ПРАВИЛЬНЫЙ ВЫЗОВ ask_doctor (НОВАЯ СИГНАТУРА):
                processing_msg = None
                if use_gemini:  # GPT-5
                    processing_msg = await message.answer(
                        t("gpt5_processing", lang), 
                        parse_mode="HTML"
                    )

                try:
                    # Основной запрос к модели
                    response = await ask_doctor(
                        context_text=full_context,
                        user_question=user_input,
                        lang=lang,
                        user_id=user_id,
                        use_gemini=use_gemini
                    )
                    
                    # Удаляем уведомление перед отправкой ответа
                    if processing_msg:
                        try:
                            await bot.delete_message(
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id
                            )
                        except Exception:
                            pass  # Игнорируем ошибки удаления
                            
                except Exception as e:
                    # При ошибке тоже удаляем уведомление
                    if processing_msg:
                        try:
                            await bot.delete_message(
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id
                            )
                        except Exception:
                            pass
                    raise e  # Передаем ошибку дальше

                # Отправляем ответ пользователю
                if response:
                    await send_response_message(message, response)
                    
                    # ✅ ИСПРАВЛЕНИЕ: Тратим лимит только если ДЕЙСТВИТЕЛЬНО использовали продвинутую модель
                    if use_gemini:  # Если использовали Gemini - точно тратим лимит
                        
                        await spend_gpt4o_limit(user_id, message, bot)
                    
                    await save_message(user_id, "assistant", response)
                    summary_allowed, _ = await check_rate_limit(user_id, "summary")
                    if summary_allowed:
                        summary_was_updated = await maybe_update_summary(user_id)
                        if summary_was_updated:
                            await record_user_action(user_id, "summary")
                    else:
                        summary_was_updated = False

                    # Проверка upsell ТОЛЬКО если сводка реально обновилась
                    if summary_was_updated:
                        # Увеличиваем счетчик сводок только если нет лимитов И нет подписки
                        if gpt4o_queries_left == 0 and subscription_type != 'subscription':
                            upsell_tracker.increment_summary_count(user_id)
                            
                            # ✅ ПРАВИЛЬНАЯ ПРОВЕРКА: используем новую функцию
                            if upsell_tracker.should_show_upsell_on_summary(user_id):
                                await SubscriptionHandlers.show_subscription_upsell(
                                    message, user_id, reason="summary_updated"
                                )
                else:
                    await send_error_message(message, get_user_friendly_message("Не удалось получить ответ", lang))
                    
            except Exception as e:
                log_error_with_context(e, {"user_id": user_id, "action": "gpt_request"})
                await send_error_message(message, get_user_friendly_message(e, lang))
                    
        except Exception as e:
            log_error_with_context(e, {"user_id": user_id, "action": "message_processing"})
            await send_error_message(message, get_user_friendly_message(e, lang))
    
    # 🎯 ГЛАВНОЕ ДОБАВЛЕНИЕ - ПРОВЕРКА ПРОМОКОДА:
    try:
        # Увеличиваем накопительный счетчик и получаем новое значение
        from cumulative_counter import increment_and_get_total_messages
        total_message_count = await increment_and_get_total_messages(user_id)
        
        logger.info(f"📊 User {user_id}: всего сообщений #{total_message_count}")
        
        # 1️⃣ Проверяем точный номер сообщения (Промокод1)
        if total_message_count == 30:  # Точно на 30 сообщении
            promo_message = await check_promo_on_message(user_id, total_message_count)
            if promo_message:
                logger.info(f"🎉 User {user_id}: показан промокод на {total_message_count}-м сообщении!")
        # Для всех остальных сообщений промокод не проверяем!
            
    except Exception as e:
        # Ошибка промокода не должна ломать основную функциональность
        logger.error(f"❌ Ошибка проверки промокода для user {user_id}: {e}")
    

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
            reply_markup=language_choice_keyboard(lang)
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
        await callback.answer(t("error_state", lang))
        return
    
    field = state.get("field")
    choice = callback.data

    
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
    else:
        # Fallback на прямое значение
        readable_value = choice
    
    # Обновляем поле
    success, message = await ProfileManager.update_field(user_id, db_field, readable_value, lang)
    
    if success:
        await callback.message.edit_text(message, parse_mode="HTML")
        user_states[user_id] = None
        
        # ✅ ДОБАВЛЕНО: показываем главное меню после успешного обновления
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
    await show_main_menu(callback.message, lang)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "settings_faq")
@handle_telegram_errors
async def handle_faq_settings(callback: types.CallbackQuery):
    """Обработка кнопки FAQ"""
    await handle_faq_main(callback)

@dp.callback_query(lambda c: c.data.startswith("faq_"))
@handle_telegram_errors
async def handle_faq_sections(callback: types.CallbackQuery):
    """Обработчик всех разделов FAQ"""
    await handle_faq_section(callback)

@dp.callback_query(lambda c: c.data == "settings_subscription")
@handle_telegram_errors
async def handle_subscription_settings(callback: types.CallbackQuery):
    """
    🔄 Обработка кнопки Подписка в настройках с автосинхронизацией
    """
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # 🔄 ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ с Stripe при каждом заходе
        logger.info(f"🔄 Синхронизация подписки для пользователя {user_id}")
        
        # Показываем "загрузка" пока синхронизируемся
        await callback.message.edit_text(
            t("subscription_syncing", lang),
            parse_mode="HTML"
        )
        
        # Принудительная синхронизация
        sync_result = await SubscriptionManager.force_sync_with_stripe(user_id)
        
        if sync_result.get("actions"):
            # Если были исправления - логируем
            logger.info(f"✅ Синхронизация для {user_id}: {'; '.join(sync_result['actions'])}")
        
        # После синхронизации показываем актуальное меню
        await SubscriptionHandlers.show_subscription_menu(callback)
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации для пользователя {user_id}: {e}")
        
        # Если синхронизация не удалась - всё равно показываем меню
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
    lang = await get_user_language(callback.from_user.id)
    await callback.answer(t("your_current_subscription", lang), show_alert=True)

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
            await handle_show_documents(callback.message, user_id=user_id)
        else:
            await callback.message.answer(t("unknown_state", lang))
        await callback.answer()
        return
        
    if callback.data == "edit_meds":
        user_states[callback.from_user.id] = "editing_medications"
        lang = await get_user_language(callback.from_user.id)
        
        # ✅ ДОБАВЛЯЕМ: Показываем кнопку "Отмена"
        from keyboards import cancel_keyboard
        await callback.message.answer(
            t("edit_schedule", lang),
            reply_markup=cancel_keyboard(lang)  # ← ВОТ ЭТО ВАЖНО!
        )
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
            # ✅ ДОБАВЛЯЕМ ГЛАВНОЕ МЕНЮ ЕСЛИ ДОКУМЕНТ НЕ НАЙДЕН
            await show_main_menu(callback.message, lang)
            return

        if action == "view":
            title = doc["title"]
            text = doc["raw_text"] or t("empty_document", lang)
            clean_text = text[:4000]
            from utils.security import safe_send_message
            await safe_send_message(callback.message, clean_text, title=title)

            
        elif action == "rename":
            user_states[user_id] = f"rename_{doc_id}"
            await callback.message.answer(t("enter_new_name_doc", lang))
            
        elif action == "delete":
            await delete_document(doc_id)
            await callback.message.answer(t("document_deleted", lang))
            # ✅ ДОБАВЛЯЕМ ГЛАВНОЕ МЕНЮ ПОСЛЕ УДАЛЕНИЯ
            await show_main_menu(callback.message, lang)
            
        elif action == "download":
            file_path = doc.get("file_path")
            if not file_path:
                await callback.message.answer(t("file_not_found", lang))
                return
            
            try:
                from file_storage import get_file_storage
                storage = get_file_storage()
                
                if storage.storage_type == "supabase":
                    # ✅ ДЛЯ ПРИВАТНОГО BUCKET СРАЗУ ИСПОЛЬЗУЕМ БЕЗОПАСНОЕ СКАЧИВАНИЕ
                    logger.info(f"📥 [SUPABASE] Скачиваем файл для пользователя: {file_path}")
                    
                    # Определяем имя файла для пользователя
                    original_filename = doc.get("title", "document")
                    file_ext = os.path.splitext(file_path)[1] or ".pdf"
                    safe_filename = f"{original_filename}{file_ext}"
                    
                    # Создаем временный файл
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                        temp_path = temp_file.name
                    
                    # Скачиваем файл из Supabase Storage
                    import asyncio
                    download_success = await storage.storage_manager.download_file(file_path, temp_path)
                    
                    if download_success and os.path.exists(temp_path):
                        # Отправляем файл пользователю
                        await callback.message.answer_document(
                            types.FSInputFile(path=temp_path, filename=safe_filename)
                        )
                        logger.info(f"✅ [SUPABASE] Файл отправлен пользователю: {safe_filename}")
                        
                        # Удаляем временный файл
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    else:
                        await callback.message.answer(t("file_not_found", lang))
                        
                else:
                    # ✅ ЛОКАЛЬНЫЕ ФАЙЛЫ (для fallback режима разработки)
                    if not os.path.exists(file_path):
                        await callback.message.answer(t("file_not_found", lang))
                        return
                    await callback.message.answer_document(types.FSInputFile(path=file_path))
                    
            except Exception as e:
                logger.error(f"❌ Ошибка скачивания файла: {e}")
                await callback.message.answer(t("file_not_found", lang))
          
            
    except Exception as e:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        log_error_with_context(e, {"user_id": user_id, "action": "button_callback", "callback_data": callback.data})
        await callback.message.answer(get_user_friendly_message(e, lang))
        # ✅ ДОБАВЛЯЕМ ГЛАВНОЕ МЕНЮ ДАЖЕ ПРИ ОШИБКАХ
        await show_main_menu(callback.message, lang)
    
    await callback.answer()

@handle_telegram_errors
async def main():
    """Главная функция запуска бота (Railway-ready)"""
    print("🚀 Запуск медицинского бота...")
    
    try:
        # 🔧 Получаем порт от Railway (для webhook)
        port = int(os.getenv("PORT", 8080))
        is_railway = os.getenv("RAILWAY_ENVIRONMENT") == "production"
        
        print(f"🚀 Запуск бота {'на Railway' if is_railway else 'локально'}")
        print(f"🌐 Webhook порт: {port}")
        
        # 🔧 1. ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ USER STATE
        from user_state_manager import UserStateManager
        user_state_manager = UserStateManager(ttl_minutes=60)
        print("✅ Бот инициализирован")
        
        # 💳 2. ПРОВЕРКА STRIPE
        stripe_ok = check_stripe_setup()  # БЕЗ await - функция не async!
        if stripe_ok:
            print("✅ Stripe API готов")
            print("💳 Stripe готов к работе")
        else:
            print("⚠️ Stripe недоступен (возможно, ключи не настроены)")
        
        # 🗄️ 3. ИНИЦИАЛИЗАЦИЯ POSTGRESQL (КРИТИЧНО!)
        print("🔗 Подключение к PostgreSQL...")
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise Exception("❌ DATABASE_URL не найден в переменных окружения")
        
        await initialize_db_pool(max_connections=10)
        print("🗄️ PostgreSQL pool готов")

        from aiogram.types import MenuButtonCommands, BotCommand
    
        # Сначала устанавливаем команды
        commands = [
            BotCommand(command="start", description="🚀 Запуск бота"),
            BotCommand(command="menu", description="📋 Главное меню"),
            BotCommand(command="help", description="❓ Помощь"),
        ]
        await bot.set_my_commands(commands)
        
        # Затем кнопку меню
        menu_button = MenuButtonCommands()
        await bot.set_chat_menu_button(menu_button=menu_button)
        
        print("✅ Кнопка меню и команды установлены")
              
        # 🧠 4. ИНИЦИАЛИЗАЦИЯ VECTOR DB (ПОСЛЕ PostgreSQL!)
        print("🧠 Инициализация pgvector...")
        try:
            await initialize_vector_db()
            print("✅ Vector database готова")
        except Exception as e:
            print(f"❌ Ошибка pgvector: {e}")
            print("⚠️ Проверьте, что расширение pgvector включено в Railway PostgreSQL")
            raise

        # 📁 5. ПРОВЕРКА ФАЙЛОВОГО ХРАНИЛИЩА (ВСТАВИТЬ СЮДА!)
        try:
            from file_storage import check_storage_setup
            storage_info = check_storage_setup()
            
            if storage_info['success']:
                stats = storage_info['stats']
                print(f"✅ Файловое хранилище готово:")
                print(f"   📂 Тип: {stats['storage_type']}")
                print(f"   📍 Путь: {stats['storage_path']}")
                print(f"   📊 Файлов: {stats['file_count']}")
                print(f"   💾 Размер: {stats['total_size_mb']} MB")
                
                if stats['storage_type'] == 'persistent':
                    print("   🎉 Railway Volumes активны!")
                else:
                    print("   ⚠️ Временное хранилище (добавьте Railway Volume)")
            else:
                print(f"❌ Ошибка хранилища: {storage_info['error']}")
                
        except Exception as e:
            print(f"⚠️ Ошибка проверки хранилища: {e}")
        
        # 🤖 6. ПРОВЕРКА OPENAI
        openai_status = await check_openai_status()
        if openai_status:
            print("✅ OpenAI API доступен")
        else:
            print("⚠️ Проблемы с OpenAI API")
        
        # 🌐 7. ЗАПУСК WEBHOOK СЕРВЕРА (на Railway порту)
        if stripe_ok:
            print(f"🔗 Запуск Stripe webhook сервера на порту {port}...")
            from webhook_subscription_handler import start_webhook_server
            webhook_runner = await start_webhook_server(bot, port=port)
            print("✅ Webhook сервер запущен")
        
        print("🚦 Rate Limiter активирован")
        print("   - Сообщения: 10/мин")
        print("   - Документы: 3/5мин") 
        print("   - Изображения: 3/10мин")
        print("   - Заметки: 5/5мин")
        print("🚀 Бот готов к работе на Railway!")
        
        # 🚀 8. ЗАПУСК БОТА
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        log_error_with_context(e, {"action": "railway_startup"})
        
    finally:
        # 🧹 ОЧИСТКА РЕСУРСОВ
        print("🧹 Закрытие соединений...")
        try:
            await close_db_pool()
            print("✅ База данных закрыта")
        except Exception as e:
            print(f"⚠️ Ошибка закрытия: {e}")

# 🎯 ТОЧКА ВХОДА (в самом конце файла, замените существующую)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Фатальная ошибка: {e}")