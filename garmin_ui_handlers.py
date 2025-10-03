# garmin_ui_handlers.py - ОЧИЩЕННАЯ ВЕРСИЯ (удалены: время анализа, часовой пояс, последние данные)

import logging
import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db_postgresql import get_user_language
from garmin_connector import garmin_connector
from subscription_manager import SubscriptionManager

logger = logging.getLogger(__name__)

# ================================
# СОСТОЯНИЯ ДЛЯ FSM (только подключение)
# ================================

class GarminStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

# ================================
# КЛАВИАТУРЫ
# ================================

async def garmin_main_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    """Главная клавиатура настроек Garmin - УПРОЩЕННАЯ"""
    
    # Проверяем, подключен ли Garmin
    connection = await garmin_connector.get_garmin_connection(user_id)
    is_connected = connection is not None
    
    buttons = []
    
    if is_connected:
        # Если подключен - показываем только нужные кнопки
        buttons.extend([
            [InlineKeyboardButton(
                text="✅ Garmin подключен",
                callback_data="garmin_status"
            )],
            [InlineKeyboardButton(
                text="🧪 Тестовый сбор данных",
                callback_data="garmin_test_collection"
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
- Ежедневный AI анализ здоровья
- Персональные рекомендации
- Отслеживание прогресса
- Связь сна, активности и самочувствия

⚠️ <b>Важно:</b> Анализ доступен только при наличии детальных консультаций (подписка или покупка пакета)

🔄 Анализ создается автоматически при появлении новых данных сна"""

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Garmin подключен и настроен")
        else:
            logger.error(f"Ошибка показа Garmin меню: {e}")
            await callback.answer("❌ Ошибка загрузки настроек")

async def handle_garmin_status(callback: types.CallbackQuery):
    """Показать статус подключения Garmin"""
    user_id = callback.from_user.id
    
    try:
        connection = await garmin_connector.get_garmin_connection(user_id)
        
        if connection:
            text = f"""✅ <b>Garmin подключен</b>

📈 <b>Статус синхронизации:</b>
- Последняя синхронизация: {connection.get('last_sync_date', 'еще не было')}
- Ошибок подключения: {connection.get('sync_errors', 0)}

🔋 <b>Функции:</b>
- Автоматический анализ при новых данных сна
- Персональные рекомендации  
- Отслеживание трендов"""
        else:
            text = "❌ <b>Garmin не подключен</b>\n\nДля получения анализов здоровья подключите ваш аккаунт Garmin Connect."
        
        await callback.answer(text, show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка показа статуса Garmin: {e}")
        await callback.answer("❌ Ошибка получения статуса", show_alert=True)

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

<b>🤖 Как работает:</b>
• Каждые 30 минут бот проверяет новые данные сна
• При изменении времени сна создается анализ
• Рекомендации учитывают вашу анкету

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

Для работы анализа Garmin требуются детальные консультации.

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

• Автоматические анализы здоровья прекратятся
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

async def handle_garmin_test_collection(callback: types.CallbackQuery):
    """Тестовый сбор данных Garmin"""
    user_id = callback.from_user.id
    
    try:
        await callback.answer("🔄 Запускаю тестовый сбор...")
        
        from garmin_scheduler import force_user_analysis
        
        await callback.message.edit_text(
            "🔄 <b>Тестовый сбор данных запущен</b>\n\n"
            "⏳ Собираю данные Garmin...\n"
            "⏳ Проверяю изменение времени сна...\n"
            "⏳ Анализирую необходимость создания отчета...",
            parse_mode="HTML"
        )
        
        success = await force_user_analysis(user_id)
        
        if success:
            text = """✅ <b>Тестовый сбор завершен успешно!</b>

🎯 <b>Что произошло:</b>
• Собраны данные Garmin за последние дни
• Обнаружено изменение времени сна
• Создан и отправлен анализ здоровья
• Новое время сна сохранено для сравнения

💡 <b>Результат:</b> Анализ отправлен вам отдельным сообщением"""
        else:
            text = """ℹ️ <b>Тестовый сбор завершен</b>

📊 <b>Возможные причины отсутствия анализа:</b>
• Время сна не изменилось с последнего анализа
• Недостаточно данных от Garmin
• Закончились детальные консультации

💡 <b>Попробуйте:</b>
• Проверить подключение Garmin
• Дождаться новых данных сна
• Пополнить лимиты консультаций"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторить", callback_data="garmin_test_collection")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка тестового сбора: {e}")
        
        error_text = """❌ <b>Ошибка тестового сбора</b>

Произошла ошибка при сборе данных Garmin.

💡 <b>Попробуйте:</b>
• Проверить подключение Garmin
• Повторить попытку позже
• Обратиться в поддержку при повторении ошибки"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторить", callback_data="garmin_test_collection")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_garmin")]
        ])
        
        await callback.message.edit_text(error_text, reply_markup=keyboard, parse_mode="HTML")

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
        # Сохраняем подключение (БЕЗ времени и часового пояса!)
        saved = await garmin_connector.save_garmin_connection(
            user_id=user_id,
            email=email, 
            password=password
        )
        
        if saved:
            text = f"""✅ <b>Garmin подключен успешно!</b>

{result_message}

🔄 Анализ будет создаваться автоматически при появлении новых данных сна"""
            
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

# ================================
# CALLBACK DATA HANDLERS MAP
# ================================

GARMIN_CALLBACK_HANDLERS = {
    'garmin_menu': handle_garmin_menu,
    'garmin_info': handle_garmin_info,
    'garmin_connect': handle_garmin_connect,
    'garmin_status': handle_garmin_status,
    'garmin_disconnect': handle_garmin_disconnect,
    'garmin_disconnect_confirm': handle_garmin_disconnect_confirm,
    'garmin_test_collection': handle_garmin_test_collection,
    'garmin_cancel_setup': handle_garmin_cancel_setup,
    'back_to_garmin': handle_garmin_menu,
}