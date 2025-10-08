# garmin_ui_handlers.py - ОЧИЩЕННАЯ ВЕРСИЯ (удалены: время анализа, часовой пояс, последние данные)

import logging
import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db_postgresql import get_user_language, t
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
                text=t("garmin_connected", lang),
                callback_data="garmin_status"
            )],
            # [InlineKeyboardButton(
            #     text="🧪 Тестовый сбор данных",
            #     callback_data="garmin_test_collection"
            # )],
            [InlineKeyboardButton(
                text=t("garmin_disconnect", lang),
                callback_data="garmin_disconnect"
            )]
        ])
    else:
        # Если не подключен - показываем кнопку подключения
        buttons.extend([
            [InlineKeyboardButton(
                text=t("garmin_button_connect_now", lang),
                callback_data="garmin_connect"
            )],
            [InlineKeyboardButton(
                text=t("garmin_info", lang),
                callback_data="garmin_info"
            )]
        ])
    
    # Кнопка назад
    buttons.append([InlineKeyboardButton(
        text=t("back_to_settings", lang),
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
        text = t("garmin_menu_description", lang)

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
    lang = await get_user_language(user_id)
    
    try:
        connection = await garmin_connector.get_garmin_connection(user_id)
        
        if connection:
            text = t("garmin_status_connected", lang,
                last_sync=connection.get('last_sync_date', t("garmin_no_sync_yet", lang)),
                sync_errors=connection.get('sync_errors', 0)
            )
        else:
            text = t("garmin_status_not_connected", lang)
        
        await callback.answer(text, show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка показа статуса Garmin: {e}")
        await callback.answer(t("garmin_status_error", lang), show_alert=True)

async def handle_garmin_info(callback: types.CallbackQuery):
    """Показать информацию о возможностях Garmin"""
    lang = await get_user_language(callback.from_user.id)
    
    text = t("garmin_info_text", lang)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("garmin_button_connect_now", lang), 
            callback_data="garmin_connect"
        )],
        [InlineKeyboardButton(
            text=t("garmin_button_back", lang), 
            callback_data="back_to_garmin"
        )]
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
            text = t("garmin_limits_required", lang, **limits)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("limits_exhausted_subscription_button", lang), 
                    callback_data="subscription"
                )],
                [InlineKeyboardButton(
                    text=t("garmin_button_back", lang), 
                    callback_data="back_to_garmin"
                )]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
            return
            
    except Exception as e:
        logger.error(f"Ошибка проверки лимитов: {e}")
    
    # Если лимиты есть - продолжаем подключение
    text = t("garmin_connection_process", lang)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("cancel_button", lang), 
            callback_data="back_to_garmin"
        )]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GarminStates.waiting_for_email)
    await callback.answer()

async def handle_garmin_disconnect(callback: types.CallbackQuery):
    """Отключить Garmin"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    text = t("garmin_disconnect_confirm", lang)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("garmin_button_yes_disconnect", lang), 
            callback_data="garmin_disconnect_confirm"
        )],
        [InlineKeyboardButton(
            text=t("cancel_button", lang), 
            callback_data="back_to_garmin"
        )]
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
            text = t("garmin_disconnected_success", lang)
        else:
            text = t("garmin_disconnect_error", lang)
            
    except Exception as e:
        logger.error(f"Ошибка отключения Garmin: {e}")
        text = t("garmin_disconnect_error", lang)
    
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
        await message.answer(t("garmin_invalid_email", lang))
        return
    
    # Сохраняем email в состоянии
    await state.update_data(email=email)
    
    text = t("garmin_password_prompt", lang, email=email)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("cancel_button", lang), 
            callback_data="garmin_cancel_setup"
        )]
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
        await message.answer(t("garmin_email_not_found_error", lang))
        await state.clear()
        return
    
    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except:
        pass
    
    test_message = await message.answer(t("garmin_testing_connection", lang))
    
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
            text = t("garmin_connection_success_auto", lang, result_message=result_message)
            keyboard = await garmin_main_keyboard(lang, user_id)
        else:
            text = t("garmin_save_connection_error", lang)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("garmin_button_back", lang), 
                    callback_data="back_to_garmin"
                )]
            ])
    else:
        text = t("garmin_connection_failed_retry", lang, result_message=result_message)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t("garmin_button_try_again", lang), 
                callback_data="garmin_connect"
            )],
            [InlineKeyboardButton(
                text=t("garmin_button_back", lang), 
                callback_data="back_to_garmin"
            )]
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