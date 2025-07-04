# subscription_keyboards.py - Клавиатуры для системы подписок

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from stripe_config import StripeConfig
from typing import Optional
from db_postgresql import t

def subscription_main_menu(lang: str, current_subscription: Optional[str] = None) -> InlineKeyboardMarkup:
    """✅ ОБНОВЛЕННАЯ версия БЕЗ кнопки Мои лимиты"""
    
    buttons = []
    
    # Получаем пакеты из конфигурации
    packages = StripeConfig.get_all_packages()
    
    for package_id, package_info in packages.items():
        # Используем функцию локализации вместо прямого поля
        package_name = StripeConfig.get_localized_package_name(package_id, lang)
        
        # Формируем красивое описание
        if package_info['type'] == 'subscription':
            price_text = f"{package_info['price_display']}{t('subscription_monthly', lang)}"
        else:
            price_text = f"{package_info['price_display']} {t('subscription_one_time', lang)}"
        
        # Используем локализованное название
        button_text = f"{package_name} — {price_text}"
        
        # Проверяем активную подписку
        if current_subscription == package_id:
            # У пользователя есть эта подписка
            button_text = f"{t('subscription_current_active', lang)} {button_text}"
            buttons.append([InlineKeyboardButton(
                text=button_text, 
                callback_data="subscription_current"
            )])
        else:
            # Обычная кнопка покупки
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"buy_{package_id}"
            )])
       
    # Кнопка отмены подписки (если есть активная подписка)
    if current_subscription is not None:
        buttons.append([InlineKeyboardButton(text=t("subscription_cancel", lang), callback_data="cancel_subscription")])
    
    # Кнопка назад
    buttons.append([InlineKeyboardButton(text=t("subscription_back", lang), callback_data="back_to_settings")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def purchase_confirmation_keyboard(package_id: str, lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения покупки
    
    Args:
        package_id: ID пакета для покупки
        lang: Язык интерфейса
    """
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("purchase_confirm_pay", lang), callback_data=f"confirm_purchase_{package_id}")],
        [InlineKeyboardButton(text=t("purchase_cancel", lang), callback_data="subscription_menu")]
    ])

def subscription_upsell_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для уведомлений о подписке (когда закончились лимиты)
    
    Args:
        lang: Язык интерфейса
    """
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("upsell_get_subscription", lang), callback_data="subscription_menu")],
        [InlineKeyboardButton(text=t("upsell_later", lang), callback_data="dismiss_upsell")]
    ])

def cancel_subscription_confirmation(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения отмены подписки
    
    Args:
        lang: Язык интерфейса
    """
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("cancel_confirm_yes", lang), callback_data="confirm_cancel_subscription")],
        [InlineKeyboardButton(text=t("cancel_confirm_no", lang), callback_data="subscription_menu")]
    ])

def payment_processing_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура при обработке платежа
    
    Args:
        lang: Язык интерфейса
    """
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("payment_back_to_subscriptions", lang), callback_data="subscription_menu")]
    ])

# Вспомогательные функции для получения информации о пакетах

def get_package_description(package_id: str, lang: str) -> str:
    """Получает красивое описание пакета для подтверждения покупки"""
    
    package_info = StripeConfig.get_package_info(package_id)
    if not package_info:
        return t("package_not_found", lang)
    
    # Формируем описание
    description_parts = []
    
    # ✅ ИСПРАВЛЕНО: Используем локализованное название
    package_name = StripeConfig.get_localized_package_name(package_id, lang)
    description_parts.append(f"**{package_name}**")
    
    # Цена
    if package_info['type'] == 'subscription':
        price_text = f"{package_info['price_display']}/month"
        type_desc = t("package_subscription_desc", lang)
    else:
        price_text = package_info['price_display']
        type_desc = t("package_one_time_desc", lang)
    
    description_parts.append(f"{t('package_price_label', lang)} {price_text}")
    description_parts.append(type_desc)
    description_parts.append("")  # Пустая строка
    
    # ✅ ИСПРАВЛЕНО: Используем локализованные особенности
    description_parts.append(t("package_features_title", lang))
    features = StripeConfig.get_localized_package_features(package_id, lang)
    for feature in features:
        description_parts.append(f"✅ {feature}")
    
    return "\n".join(description_parts)