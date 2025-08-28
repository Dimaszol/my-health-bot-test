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
        notification_text = t("notifications_enabled", lang)  
        notification_callback = "toggle_med_notifications_off"
    else:
        notification_text = t("notifications_disabled", lang) 
        notification_callback = "toggle_med_notifications_on"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("edit_schedule_button", lang),
            callback_data="edit_meds"
        )],
        [InlineKeyboardButton(
            text=f"{notification_text}",
            callback_data=notification_callback
        ),
        InlineKeyboardButton(
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
    
    # Показываем оптимизированный список часовых поясов
    timezone_keyboard = InlineKeyboardMarkup(inline_keyboard=[
         # Ряд 1: Европа
        [InlineKeyboardButton(text=f"🇬🇧 {t('tz_london_gmt', lang)} (UTC+0)", callback_data="set_tz_0"),
         InlineKeyboardButton(text=f"🇪🇺 {t('tz_europe', lang)} (UTC+1)", callback_data="set_tz_60")],
        [InlineKeyboardButton(text=f"🇺🇦 {t('tz_kyiv', lang)} (UTC+2)", callback_data="set_tz_120"),
         InlineKeyboardButton(text=f"🇷🇺 {t('tz_moscow', lang)} (UTC+3)", callback_data="set_tz_180")],
        [InlineKeyboardButton(text=f"🇷🇺 {t('tz_samara', lang)} (UTC+4)", callback_data="set_tz_240"),
         InlineKeyboardButton(text=f"🇺🇿 {t('tz_tashkent', lang)} (UTC+5)", callback_data="set_tz_300")],
        
        # Ряд 2: Азия  
        [InlineKeyboardButton(text=f"🇰🇿 {t('tz_almaty', lang)} (UTC+6)", callback_data="set_tz_360"),
         InlineKeyboardButton(text=f"🇹🇭 {t('tz_bangkok', lang)} (UTC+7)", callback_data="set_tz_420")],
        [InlineKeyboardButton(text=f"🇨🇳 {t('tz_beijing', lang)} (UTC+8)", callback_data="set_tz_480"),
         InlineKeyboardButton(text=f"🇯🇵 {t('tz_tokyo', lang)} (UTC+9)", callback_data="set_tz_540")],
        [InlineKeyboardButton(text=f"🇦🇺 {t('tz_sydney', lang)} (UTC+11)", callback_data="set_tz_660"),
         InlineKeyboardButton(text=f"🇺🇸 {t('tz_usa_east', lang)} (UTC-5)", callback_data="set_tz_-300")],
        
        # Ряд 3: Америка
        [InlineKeyboardButton(text=f"🇺🇸 {t('tz_usa_central', lang)} (UTC-6)", callback_data="set_tz_-360"),
         InlineKeyboardButton(text=f"🇺🇸 {t('tz_usa_west', lang)} (UTC-8)", callback_data="set_tz_-480")],
        
        # Назад
        [InlineKeyboardButton(text=t("back_button", lang), callback_data="back_to_medications")]
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
    
    elif callback.data == "medication_timezone_settings":
        await handle_timezone_setup(callback)
    
    elif callback.data.startswith("set_tz_"):
        # Извлекаем offset из callback_data (может быть отрицательным)
        offset_str = callback.data.replace("set_tz_", "")
        offset_minutes = int(offset_str)
        
        timezone_names = {
            -480: t("tz_usa_west", await get_user_language(user_id)),       # UTC-8
            -360: t("tz_usa_central", await get_user_language(user_id)),    # UTC-6
            -300: t("tz_usa_east", await get_user_language(user_id)),       # UTC-5
            0: t("tz_london_gmt", await get_user_language(user_id)),        # UTC+0
            60: t("tz_europe", await get_user_language(user_id)),           # UTC+1
            120: t("tz_kyiv", await get_user_language(user_id)),            # UTC+2
            180: t("tz_moscow", await get_user_language(user_id)),          # UTC+3
            240: t("tz_samara", await get_user_language(user_id)),          # UTC+4
            300: t("tz_tashkent", await get_user_language(user_id)),        # UTC+5
            360: t("tz_almaty", await get_user_language(user_id)),          # UTC+6
            420: t("tz_bangkok", await get_user_language(user_id)),         # UTC+7
            480: t("tz_beijing", await get_user_language(user_id)),         # UTC+8
            540: t("tz_tokyo", await get_user_language(user_id)),           # UTC+9
            660: t("tz_sydney", await get_user_language(user_id))           # UTC+11
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