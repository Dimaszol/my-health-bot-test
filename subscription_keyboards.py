# subscription_keyboards.py - Клавиатуры для системы подписок

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from stripe_config import StripeConfig
from typing import Optional

def subscription_main_menu(lang: str, current_subscription: Optional[str] = None) -> InlineKeyboardMarkup:
    """✅ УПРОЩЕННАЯ версия - показывает кнопку отмены если есть ЛЮБАЯ подписка"""
    
    texts = {
        "ru": {
            "title": "💎 Выберите подписку:",
            "monthly": "/месяц",
            "one_time": "разово",
            "current": "✅ Активная",
            "limits": "📊 Мои лимиты",
            "cancel": "❌ Отменить подписку",
            "back": "⬅️ Назад"
        },
        "uk": {
            "title": "💎 Оберіть підписку:",
            "monthly": "/місяць", 
            "one_time": "разово",
            "current": "✅ Активна",
            "limits": "📊 Мої ліміти",
            "cancel": "❌ Скасувати підписку",
            "back": "⬅️ Назад"
        },
        "en": {
            "title": "💎 Choose subscription:",
            "monthly": "/month",
            "one_time": "one-time",
            "current": "✅ Active",
            "limits": "📊 My limits", 
            "cancel": "❌ Cancel subscription",
            "back": "⬅️ Back"
        }
    }
    
    t = texts.get(lang, texts["ru"])
    
    buttons = []
    
    # Получаем пакеты из конфигурации
    packages = StripeConfig.get_all_packages()
    
    for package_id, package_info in packages.items():
        # Формируем красивое описание
        if package_info['type'] == 'subscription':
            price_text = f"{package_info['price_display']}{t['monthly']}"
        else:
            price_text = f"{package_info['price_display']} {t['one_time']}"
        
        button_text = f"{package_info['user_friendly_name']} — {price_text}"
        
        # ✅ УПРОЩЕНИЕ: Проверяем активную подписку
        if current_subscription == package_id:
            # У пользователя есть эта подписка
            button_text = f"✅ {button_text}"
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
    
    # Дополнительные кнопки
    additional_buttons = []
    additional_buttons.append(InlineKeyboardButton(text=t["limits"], callback_data="show_limits"))
    
    # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Показываем кнопку отмены если есть ЛЮБАЯ активная подписка
    if current_subscription is not None:
        additional_buttons.append(InlineKeyboardButton(text=t["cancel"], callback_data="cancel_subscription"))
    
    if len(additional_buttons) == 2:
        buttons.append(additional_buttons)
    else:
        for btn in additional_buttons:
            buttons.append([btn])
    
    buttons.append([InlineKeyboardButton(text=t["back"], callback_data="back_to_settings")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def purchase_confirmation_keyboard(package_id: str, lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения покупки
    
    Args:
        package_id: ID пакета для покупки
        lang: Язык интерфейса
    """
    
    texts = {
        "ru": {
            "confirm": "💳 Оплатить",
            "cancel": "❌ Отмена"
        },
        "uk": {
            "confirm": "💳 Сплатити", 
            "cancel": "❌ Скасувати"
        },
        "en": {
            "confirm": "💳 Pay",
            "cancel": "❌ Cancel"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["confirm"], callback_data=f"confirm_purchase_{package_id}")],
        [InlineKeyboardButton(text=t["cancel"], callback_data="subscription_menu")]
    ])

def subscription_upsell_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для уведомлений о подписке (когда закончились лимиты)
    
    Args:
        lang: Язык интерфейса
    """
    
    texts = {
        "ru": {
            "subscribe": "💎 Оформить подписку",
            "later": "⏭ Позже"
        },
        "uk": {
            "subscribe": "💎 Оформити підписку",
            "later": "⏭ Пізніше"
        },
        "en": {
            "subscribe": "💎 Get subscription", 
            "later": "⏭ Later"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["subscribe"], callback_data="subscription_menu")],
        [InlineKeyboardButton(text=t["later"], callback_data="dismiss_upsell")]
    ])

def cancel_subscription_confirmation(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения отмены подписки
    
    Args:
        lang: Язык интерфейса
    """
    
    texts = {
        "ru": {
            "confirm": "⚠️ Да, отменить",
            "cancel": "✅ Нет, оставить"
        },
        "uk": {
            "confirm": "⚠️ Так, скасувати",
            "cancel": "✅ Ні, залишити"
        },
        "en": {
            "confirm": "⚠️ Yes, cancel",
            "cancel": "✅ No, keep it"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["confirm"], callback_data="confirm_cancel_subscription")],
        [InlineKeyboardButton(text=t["cancel"], callback_data="subscription_menu")]
    ])

def payment_processing_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    Клавиатура при обработке платежа
    
    Args:
        lang: Язык интерфейса
    """
    
    texts = {
        "ru": {
            "back": "⬅️ Назад к подпискам"
        },
        "uk": {
            "back": "⬅️ Назад до підписок"
        },
        "en": {
            "back": "⬅️ Back to subscriptions"
        }
    }
    
    t = texts.get(lang, texts["en"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["back"], callback_data="subscription_menu")]
    ])

# Вспомогательные функции для получения информации о пакетах

def get_package_description(package_id: str, lang: str) -> str:
    """Получает красивое описание пакета для подтверждения покупки"""
    
    package_info = StripeConfig.get_package_info(package_id)
    if not package_info:
        return "Package not found"
    
    # Тексты для разных языков
    texts = {
        "ru": {
            "subscription_desc": f"🔄 Подписка с автопродлением каждый месяц",
            "one_time_desc": f"📅 Разовая покупка на 30 дней",
            "features_title": "📋 Что входит:",
            "price_label": "💰 Стоимость:"
        },
        "uk": {
            "subscription_desc": f"🔄 Підписка з автопродовженням щомісяця",
            "one_time_desc": f"📅 Разова покупка на 30 днів", 
            "features_title": "📋 Що входить:",
            "price_label": "💰 Вартість:"
        },
        "en": {
            "subscription_desc": f"🔄 Subscription with monthly auto-renewal",
            "one_time_desc": f"📅 One-time purchase for 30 days",
            "features_title": "📋 What's included:",
            "price_label": "💰 Price:"
        }
    }
    
    t = texts.get(lang, texts["ru"])
    
    # Формируем описание
    description_parts = []
    
    # Заголовок
    description_parts.append(f"**{package_info['user_friendly_name']}**")
    
    # Цена
    if package_info['type'] == 'subscription':
        price_text = f"{package_info['price_display']}/month"
        type_desc = t["subscription_desc"]
    else:
        price_text = package_info['price_display']
        type_desc = t["one_time_desc"]
    
    description_parts.append(f"{t['price_label']} {price_text}")
    description_parts.append(type_desc)
    description_parts.append("")  # Пустая строка
    
    # Особенности
    description_parts.append(t["features_title"])
    features = package_info.get('features', {}).get(lang, [])
    for feature in features:
        description_parts.append(f"✅ {feature}")
    
    return "\n".join(description_parts)