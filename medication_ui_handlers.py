# medication_ui_handlers.py - Обработчики интерфейса для уведомлений о лекарствах

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db_postgresql import get_user_language, t, format_medications_schedule
from medication_notifications import get_user_notification_settings, toggle_user_medication_notifications, set_user_medication_timezone

# ================================
# 1. ОБНОВЛЕННАЯ КЛАВИАТУРА ДЛЯ ЛЕКАРСТВ
# ================================

async def medications_keyboard_with_notifications(lang: str, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для раздела лекарств с кнопками уведомлений"""
    
    # Получаем настройки уведомлений
    settings = await get_user_notification_settings(user_id)
    
    # Определяем текст кнопки уведомлений
    if settings['enabled']:
        notification_text = t("notifications_enabled", lang)  # "🔔 Вкл"
        notification_callback = "toggle_med_notifications_off"
    else:
        notification_text = t("notifications_disabled", lang)  # "🔕 Выкл"
        notification_callback = "toggle_med_notifications_on"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("edit_schedule_button", lang),
            callback_data="edit_meds"
        )],
        [InlineKeyboardButton(
            text=f"{t('notifications_label', lang)}: {notification_text}",
            callback_data=notification_callback
        )],
        [InlineKeyboardButton(
            text=t("timezone_settings", lang),
            callback_data="medication_timezone_settings"
        )]
    ])
    
    return keyboard

# ================================
# 2. ОБРАБОТЧИКИ CALLBACK'ОВ
# ================================

async def handle_toggle_medication_notifications(callback: types.CallbackQuery):
    """Обработчик переключения уведомлений о лекарствах"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # Переключаем уведомления
        new_state = await toggle_user_medication_notifications(user_id)
        
        if new_state:
            status_text = t("notifications_enabled_success", lang)
            # Если уведомления включены, предлагаем настроить часовой пояс
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("setup_timezone", lang),
                    callback_data="medication_timezone_setup"
                )],
                [InlineKeyboardButton(
                    text=t("back_to_medications", lang),
                    callback_data="back_to_medications"
                )]
            ])
            await callback.message.edit_text(
                f"{status_text}\n\n{t('timezone_setup_suggestion', lang)}",
                reply_markup=keyboard
            )
        else:
            status_text = t("notifications_disabled_success", lang)
            await callback.message.edit_text(status_text)
            
            # Возвращаемся к меню лекарств через 2 секунды
            import asyncio
            await asyncio.sleep(2)
            await show_medications_with_notifications(callback.message, user_id, edit=True)
    
    except Exception as e:
        await callback.message.edit_text(t("notifications_toggle_error", lang))
    
    await callback.answer()

async def handle_timezone_setup(callback: types.CallbackQuery):
    """Обработчик настройки часового пояса"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Показываем популярные часовые пояса
    timezone_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Москва (UTC+3)", callback_data="set_tz_180")],
        [InlineKeyboardButton(text="🇺🇦 Киев (UTC+2)", callback_data="set_tz_120")],
        [InlineKeyboardButton(text="🇰🇿 Алматы (UTC+6)", callback_data="set_tz_360")],
        [InlineKeyboardButton(text="🇺🇿 Ташкент (UTC+5)", callback_data="set_tz_300")],
        [InlineKeyboardButton(text="🇩🇪 Берлин (UTC+1)", callback_data="set_tz_60")],
        [InlineKeyboardButton(text="🇬🇧 Лондон (UTC+0)", callback_data="set_tz_0")],
        [InlineKeyboardButton(text="🏠 " + t("manual_timezone", lang), callback_data="manual_timezone")],
        [InlineKeyboardButton(text=t("back", lang), callback_data="back_to_medications")]
    ])
    
    await callback.message.edit_text(
        t("select_timezone", lang),
        reply_markup=timezone_keyboard
    )
    await callback.answer()

async def handle_timezone_set(callback: types.CallbackQuery, offset_minutes: int, timezone_name: str):
    """Обработчик установки конкретного часового пояса"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        await set_user_medication_timezone(user_id, offset_minutes, timezone_name)
        
        # Показываем подтверждение с красивым форматированием
        hours = offset_minutes // 60
        
        if hours == 0:
            offset_display = "±0"
        elif hours > 0:
            offset_display = f"+{hours}"
        else:
            offset_display = str(hours)
        
        await callback.message.edit_text(
            t("timezone_set_success", lang, timezone=timezone_name, offset=offset_display),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("back_to_medications", lang),
                    callback_data="back_to_medications"
                )]
            ])
        )
        
    except Exception as e:
        await callback.message.edit_text(t("timezone_set_error", lang))
    
    await callback.answer()

async def show_medications_with_notifications(message: types.Message, user_id: int, edit: bool = False):
    """Показать раздел лекарств с уведомлениями"""
    lang = await get_user_language(user_id)
    
    # Получаем график лекарств
    schedule_text = await format_medications_schedule(user_id)
    if not schedule_text:
        schedule_text = t("schedule_empty", lang)
    
    # Получаем настройки уведомлений
    settings = await get_user_notification_settings(user_id)
    
    # Формируем информацию об уведомлениях
    if settings['enabled']:
        hours = settings['timezone_offset'] // 60
        
        # Красиво показываем часовой пояс
        if hours == 0:
            offset_display = "±0"
        elif hours > 0:
            offset_display = f"+{hours}"
        else:
            offset_display = str(hours)
            
        notification_info = t("notifications_status_enabled", lang, 
                             timezone=settings['timezone_name'], 
                             offset=offset_display)
    else:
        notification_info = t("notifications_status_disabled", lang)
    
    full_text = f"""🗓 <b>{t('your_schedule', lang)}</b>

<pre>{schedule_text}</pre>

📱 <b>{t('notifications_title', lang)}</b>
{notification_info}"""
    
    keyboard = await medications_keyboard_with_notifications(lang, user_id)
    
    if edit:
        await message.edit_text(full_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(full_text, reply_markup=keyboard, parse_mode="HTML")

# ================================
# 3. ОБРАБОТЧИК ДЛЯ MAIN.PY
# ================================

async def handle_medication_callbacks(callback: types.CallbackQuery):
    """Центральный обработчик callback'ов для лекарств"""
    
    if callback.data in ["toggle_med_notifications_on", "toggle_med_notifications_off"]:
        await handle_toggle_medication_notifications(callback)
    
    elif callback.data == "medication_timezone_settings":  # не "setup"
        await handle_timezone_setup(callback)
    
    elif callback.data.startswith("set_tz_"):
        offset_minutes = int(callback.data.split("_")[-1])
        timezone_names = {
            180: "Москва",
            120: "Киев", 
            360: "Алматы",
            300: "Ташкент",
            60: "Берлин",
            0: "Лондон"
        }
        timezone_name = timezone_names.get(offset_minutes, "Manual")
        await handle_timezone_set(callback, offset_minutes, timezone_name)
    
    elif callback.data == "back_to_medications":
        await show_medications_with_notifications(callback.message, callback.from_user.id, edit=True)
    
    elif callback.data == "turn_off_med_notifications":
        # Пользователь хочет отключить уведомления из самого уведомления
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        try:
            # Отключаем уведомления
            await toggle_user_medication_notifications(user_id)
            
            # Показываем подтверждение
            await callback.message.edit_text(
                t("notifications_turned_off_from_reminder", lang),
                reply_markup=None
            )
            await callback.answer(t("notifications_disabled_success", lang), show_alert=True)
            
        except Exception as e:
            await callback.answer(t("notifications_toggle_error", lang), show_alert=True)
    
    elif callback.data == "medication_settings":
        await show_medications_with_notifications(callback.message, callback.from_user.id, edit=True)

# ================================
# 4. ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕГО ОБРАБОТЧИКА
# ================================

# Эта функция заменяет существующий обработчик show_medications_schedule в main.py
async def show_medications_schedule_updated(message: types.Message):
    """Обновленный обработчик показа графика лекарств"""
    user_id = message.from_user.id
    await show_medications_with_notifications(message, user_id)