# garmin_ui_handlers.py - Обработчики интерфейса для Garmin интеграции

import logging
import asyncio
from datetime import time
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db_postgresql import get_user_language, t
from garmin_connector import garmin_connector
from subscription_manager import SubscriptionManager
from medication_notifications import get_user_notification_settings, set_user_medication_timezone

logger = logging.getLogger(__name__)

# ================================
# СОСТОЯНИЯ ДЛЯ FSM
# ================================

class GarminStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()
    waiting_for_time = State()

# ================================
# КЛАВИАТУРЫ
# ================================

async def garmin_main_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    """Главная клавиатура настроек Garmin"""
    
    # Проверяем, подключен ли Garmin
    connection = await garmin_connector.get_garmin_connection(user_id)
    is_connected = connection is not None
    
    buttons = []
    
    if is_connected:
        # Если подключен - показываем статус и настройки
        buttons.extend([
            [InlineKeyboardButton(
                text="✅ Garmin подключен",
                callback_data="garmin_status"
            )],
            [InlineKeyboardButton(
                text="⏰ Время анализа", 
                callback_data="garmin_set_time"
            )],
            [InlineKeyboardButton(
                text="🌍 Часовой пояс",
                callback_data="garmin_timezone"
            )],
            [InlineKeyboardButton(
                text="📊 Последние данные",
                callback_data="garmin_show_data"
            )],
            [InlineKeyboardButton(
                text="❌ Отключить Garmin",
                callback_data="garmin_disconnect"
            )]
        ])
    else:
        # Если не подключен - показываем кнопку подключения
        buttons.extend([
            [InlineKeyboardButton(
                text="🔗 Подключить Garmin",
                callback_data="garmin_connect"
            )],
            [InlineKeyboardButton(
                text="❓ Что это дает?",
                callback_data="garmin_info"
            )]
        ])
    
    # Кнопка назад
    buttons.append([InlineKeyboardButton(
        text="← Назад к настройкам",
        callback_data="back_to_settings"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def garmin_timezone_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора часового пояса (используем из лекарств)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Москва (UTC+3)", callback_data="garmin_tz_180")],
        [InlineKeyboardButton(text="🇺🇦 Киев (UTC+2)", callback_data="garmin_tz_120")],
        [InlineKeyboardButton(text="🇰🇿 Алматы (UTC+6)", callback_data="garmin_tz_360")],
        [InlineKeyboardButton(text="🇺🇿 Ташкент (UTC+5)", callback_data="garmin_tz_300")],
        [InlineKeyboardButton(text="🇩🇪 Берлин (UTC+1)", callback_data="garmin_tz_60")],
        [InlineKeyboardButton(text="🇬🇧 Лондон (UTC+0)", callback_data="garmin_tz_0")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
    ])

# ================================
# ОБРАБОТЧИКИ CALLBACK'ОВ
# ================================

async def handle_garmin_menu(callback: types.CallbackQuery):
    """Показать главное меню настроек Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        keyboard = await garmin_main_keyboard(lang, user_id)
        
        text = """📱 <b>Интеграция с Garmin</b>

🩺 <b>Что это дает:</b>
• Ежедневный AI анализ здоровья
• Персональные рекомендации
• Отслеживание прогресса
• Связь сна, активности и самочувствия

⚠️ <b>Важно:</b> Анализ доступен только при наличии детальных консультаций (подписка или покупка пакета)"""

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка показа Garmin меню: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки настроек Garmin")
    
    await callback.answer()

async def handle_garmin_info(callback: types.CallbackQuery):
    """Показать информацию о возможностях Garmin"""
    lang = await get_user_language(callback.from_user.id)
    
    text = """🩺 <b>Ежедневный анализ здоровья с Garmin</b>

<b>📊 Какие данные анализируются:</b>
• 😴 <b>Сон:</b> качество, фазы, восстановление
• ❤️ <b>Пульс:</b> покоя, вариабельность, нагрузки  
• 🏃 <b>Активность:</b> шаги, калории, тренировки
• 🔋 <b>Body Battery:</b> энергия и восстановление
• 😰 <b>Стресс:</b> уровень в течение дня
• 🫁 <b>Дыхание и SpO2:</b> кислород в крови

<b>🤖 Что получаете каждое утро:</b>
• Анализ качества сна и восстановления
• Оценка готовности к нагрузкам
• Персональные рекомендации по активности
• Предупреждения о высоком стрессе
• Тренды за неделю/месяц

<b>💡 Пример анализа:</b>
"Сон 7ч 20мин - отлично! Пульс покоя снизился на 3 удара - признак улучшения формы. Body Battery 85% утром показывает хорошее восстановление. Рекомендация: можете увеличить интенсивность тренировки сегодня."

⚠️ <b>Требования:</b>
• Часы Garmin с функциями здоровья
• Аккаунт Garmin Connect  
• Активная подписка или пакет консультаций"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Подключить сейчас", callback_data="garmin_connect")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_garmin_connect(callback: types.CallbackQuery, state: FSMContext):
    """Начать процесс подключения Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Проверяем лимиты пользователя
    try:
        limits = await SubscriptionManager.get_user_limits(user_id)
        has_consultations = limits.get('gpt4o_queries_left', 0) > 0
        
        if not has_consultations:
            text = """⚠️ <b>Нужны детальные консультации</b>

Для работы анализа Garmin требуются детальные консультации (GPT-5).

📊 <b>Ваши лимиты:</b>
• Детальные консультации: {gpt4o_queries_left}

💎 Оформите подписку или купите пакет для использования анализа Garmin.""".format(**limits)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Оформить подписку", callback_data="subscription")],
                [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
            return
            
    except Exception as e:
        logger.error(f"Ошибка проверки лимитов: {e}")
    
    # Если лимиты есть - продолжаем подключение
    text = """🔗 <b>Подключение Garmin Connect</b>

Введите email от вашего аккаунта Garmin Connect:

🔐 <b>Безопасность:</b>
• Данные шифруются перед сохранением
• Используются только для сбора данных здоровья
• Можно отключить в любой момент

⚠️ <b>Убедитесь, что данные верны - иначе подключение не сработает</b>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_garmin")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GarminStates.waiting_for_email)
    await callback.answer()

async def handle_garmin_disconnect(callback: types.CallbackQuery):
    """Отключить Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    text = """❌ <b>Отключение Garmin</b>

Вы уверены, что хотите отключить интеграцию с Garmin?

• Ежедневные анализы здоровья прекратятся
• Сохраненные данные останутся в истории
• Можно подключить заново в любое время"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, отключить", callback_data="garmin_disconnect_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_garmin")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_garmin_disconnect_confirm(callback: types.CallbackQuery):
    """Подтвердить отключение Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        success = await garmin_connector.disconnect_garmin(user_id)
        
        if success:
            text = "✅ <b>Garmin отключен</b>\n\nИнтеграция отключена. Вы можете подключить её заново в любое время."
        else:
            text = "❌ <b>Ошибка отключения</b>\n\nПопробуйте позже или обратитесь в поддержку."
            
    except Exception as e:
        logger.error(f"Ошибка отключения Garmin: {e}")
        text = "❌ <b>Ошибка отключения</b>\n\nПопробуйте позже или обратитесь в поддержку."
    
    # Возвращаемся к главному меню Garmin
    keyboard = await garmin_main_keyboard(lang, user_id)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_garmin_set_time(callback: types.CallbackQuery, state: FSMContext):
    """Настройка времени анализа"""
    lang = await get_user_language(callback.from_user.id)
    
    text = """⏰ <b>Время ежедневного анализа</b>

Во сколько присылать анализ данных здоровья?

Введите время в формате <b>ЧЧ:ММ</b> (например: 07:30)

💡 <b>Рекомендация:</b> утренние часы (6:00-9:00) - лучше всего для анализа предыдущего дня"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_garmin")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GarminStates.waiting_for_time)
    await callback.answer()

async def handle_garmin_timezone(callback: types.CallbackQuery):
    """Настройка часового пояса"""
    lang = await get_user_language(callback.from_user.id)
    
    text = """🌍 <b>Часовой пояс</b>

Выберите ваш часовой пояс для точного времени анализа:"""

    keyboard = await garmin_timezone_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_garmin_timezone_set(callback: types.CallbackQuery, offset_minutes: int, timezone_name: str):
    """Установить часовой пояс для Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # Используем систему часовых поясов от уведомлений о лекарствах
        await set_user_medication_timezone(user_id, offset_minutes, timezone_name)
        
        # Также обновляем в таблице Garmin
        conn = garmin_connector.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE garmin_connections 
            SET timezone_offset = %s, timezone_name = %s, updated_at = NOW()
            WHERE user_id = %s
        """, (offset_minutes, timezone_name, user_id))
        
        conn.commit()
        conn.close()
        
        hours = offset_minutes // 60
        sign = "+" if hours >= 0 else ""
        
        text = f"✅ <b>Часовой пояс установлен</b>\n\n🌍 {timezone_name} (UTC{sign}{hours})"
        
    except Exception as e:
        logger.error(f"Ошибка установки часового пояса: {e}")
        text = "❌ <b>Ошибка установки часового пояса</b>\n\nПопробуйте позже."
    
    keyboard = await garmin_main_keyboard(lang, user_id)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

async def handle_garmin_show_data(callback: types.CallbackQuery):
    """Показать последние данные Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        conn = garmin_connector.get_db_connection()
        cursor = conn.cursor()
        
        # Получаем последние данные
        cursor.execute("""
            SELECT * FROM garmin_daily_data 
            WHERE user_id = %s 
            ORDER BY data_date DESC 
            LIMIT 3
        """, (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            text = "📊 <b>Данные Garmin</b>\n\nДанных пока нет. Подождите до завтрашнего утра для первого анализа."
        else:
            text = "📊 <b>Последние данные Garmin</b>\n\n"
            
            for row in results:
                date_str = row['data_date'].strftime('%d.%m.%Y')
                text += f"<b>📅 {date_str}:</b>\n"
                
                if row['steps']:
                    text += f"🚶 Шаги: {row['steps']:,}\n"
                if row['sleep_duration_minutes']:
                    hours = row['sleep_duration_minutes'] // 60
                    minutes = row['sleep_duration_minutes'] % 60
                    text += f"😴 Сон: {hours}ч {minutes}мин\n"
                if row['resting_heart_rate']:
                    text += f"❤️ Пульс покоя: {row['resting_heart_rate']} уд/мин\n"
                if row['body_battery_max']:
                    text += f"🔋 Body Battery: {row['body_battery_max']}%\n"
                if row['stress_avg']:
                    text += f"😰 Стресс: {row['stress_avg']}/100\n"
                
                text += "\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="garmin_show_data")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка показа данных Garmin: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки данных")
    
    await callback.answer()

# ================================
# ОБРАБОТЧИКИ FSM СОСТОЯНИЙ
# ================================

async def handle_garmin_email_input(message: types.Message, state: FSMContext):
    """Обработка ввода email"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    email = message.text.strip()
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        await message.answer("❌ Некорректный формат email. Попробуйте еще раз:")
        return
    
    # Сохраняем email в состоянии
    await state.update_data(email=email)
    
    text = f"""📧 Email: <b>{email}</b>

Теперь введите пароль от Garmin Connect:

🔐 <b>Безопасность:</b> пароль будет зашифрован перед сохранением"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="garmin_cancel_setup")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GarminStates.waiting_for_password)

async def handle_garmin_password_input(message: types.Message, state: FSMContext):
    """Обработка ввода пароля"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    password = message.text.strip()
    
    # Получаем email из состояния
    data = await state.get_data()
    email = data.get('email')
    
    if not email:
        await message.answer("❌ Ошибка: email не найден. Начните настройку заново.")
        await state.clear()
        return
    
    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except:
        pass
    
    test_message = await message.answer("🔄 Проверяю подключение к Garmin...")
    
    # Тестируем подключение
    success, result_message = await garmin_connector.test_garmin_connection(email, password)
    
    if success:
        # Сохраняем подключение
        saved = await garmin_connector.save_garmin_connection(
            user_id=user_id,
            email=email, 
            password=password
        )
        
        if saved:
            text = f"""✅ <b>Garmin подключен успешно!</b>

{result_message}

⏰ <b>Время анализа:</b> 07:00 (по умолчанию)
🌍 <b>Часовой пояс:</b> UTC+0

📊 Первый анализ будет завтра утром"""
            
            keyboard = await garmin_main_keyboard(lang, user_id)
        else:
            text = "❌ <b>Ошибка сохранения</b>\n\nПодключение работает, но не удалось сохранить настройки."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
            ])
    else:
        text = f"❌ <b>Ошибка подключения</b>\n\n{result_message}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="garmin_connect")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
        ])
    
    await test_message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()

async def handle_garmin_time_input(message: types.Message, state: FSMContext):
    """Обработка ввода времени анализа - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    time_str = message.text.strip()
    
    try:
        # 🔧 ИСПРАВЛЕНИЕ: Правильная валидация и парсинг времени
        try:
            # Парсим время в объект time
            time_obj = time.fromisoformat(time_str)
        except ValueError:
            # Если не получилось - показываем ошибку
            text = "❌ <b>Некорректный формат времени</b>\n\nИспользуйте формат ЧЧ:ММ (например: 07:30)"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_garmin")]
            ])
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            return
        
        # 🔧 ИСПРАВЛЕНИЕ: Используем новую функцию для обновления времени
        success = await garmin_connector.update_notification_time(user_id, time_str)
        
        if success:
            text = f"✅ <b>Время анализа установлено</b>\n\n⏰ Ежедневный анализ: <b>{time_str}</b>"
            keyboard = await garmin_main_keyboard(lang, user_id)
        else:
            text = "❌ <b>Ошибка сохранения времени</b>\n\nПопробуйте позже или проверьте подключение Garmin."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="garmin_set_time")],
                [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
            ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()
        
    except Exception as e:
        # 🔒 БЕЗОПАСНОЕ ЛОГИРОВАНИЕ: не выводим пользовательские данные
        logger.error(f"❌ Ошибка обработки времени для пользователя {user_id}: {e}")
        
        text = "❌ <b>Произошла ошибка</b>\n\nПопробуйте позже или обратитесь в поддержку."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
        ])
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()

async def handle_garmin_cancel_setup(callback: types.CallbackQuery, state: FSMContext):
    """Отмена настройки Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    await state.clear()
    
    keyboard = await garmin_main_keyboard(lang, user_id)
    text = "❌ Настройка отменена"
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ================================
# CALLBACK DATA HANDLERS MAP
# ================================

GARMIN_CALLBACK_HANDLERS = {
    'garmin_menu': handle_garmin_menu,
    'garmin_info': handle_garmin_info,
    'garmin_connect': handle_garmin_connect,
    'garmin_disconnect': handle_garmin_disconnect,
    'garmin_disconnect_confirm': handle_garmin_disconnect_confirm,
    'garmin_set_time': handle_garmin_set_time,
    'garmin_timezone': handle_garmin_timezone,
    'garmin_show_data': handle_garmin_show_data,
    'garmin_cancel_setup': handle_garmin_cancel_setup,
    'back_to_garmin': handle_garmin_menu,
    
    # Часовые пояса
    'garmin_tz_0': lambda cb: handle_garmin_timezone_set(cb, 0, "London"),
    'garmin_tz_60': lambda cb: handle_garmin_timezone_set(cb, 60, "Berlin"),
    'garmin_tz_120': lambda cb: handle_garmin_timezone_set(cb, 120, "Kyiv"),
    'garmin_tz_180': lambda cb: handle_garmin_timezone_set(cb, 180, "Moscow"),
    'garmin_tz_300': lambda cb: handle_garmin_timezone_set(cb, 300, "Tashkent"),
    'garmin_tz_360': lambda cb: handle_garmin_timezone_set(cb, 360, "Almaty"),
}