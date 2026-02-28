# stripe_config.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с полной локализацией

import os
import stripe
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Инициализация Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeConfig:
    """Конфигурация и константы для Stripe"""
    
    # Ключи из .env
    PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    SECRET_KEY = os.getenv("STRIPE_SECRET_KEY") 
    WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    # ✅ НОВОЕ: Price ID из переменных окружения (БЕЗ fallback)
    BASIC_PRICE_ID = os.getenv("STRIPE_BASIC_PRICE_ID")
    PREMIUM_PRICE_ID = os.getenv("STRIPE_PREMIUM_PRICE_ID")
    BASIC_EUR_PRICE_ID = os.getenv("STRIPE_BASIC_EUR_PRICE_ID")
    BASIC_GBP_PRICE_ID = os.getenv("STRIPE_BASIC_GBP_PRICE_ID")
    PREMIUM_EUR_PRICE_ID = os.getenv("STRIPE_PREMIUM_EUR_PRICE_ID")
    PREMIUM_GBP_PRICE_ID = os.getenv("STRIPE_PREMIUM_GBP_PRICE_ID")

    # Проверка что переменные заданы
    if not BASIC_PRICE_ID or not PREMIUM_PRICE_ID:
        raise ValueError("❌ STRIPE_BASIC_PRICE_ID и STRIPE_PREMIUM_PRICE_ID должны быть заданы в .env")

    if not BASIC_EUR_PRICE_ID or not BASIC_GBP_PRICE_ID or not PREMIUM_EUR_PRICE_ID or not PREMIUM_GBP_PRICE_ID:
        raise ValueError("❌ Все мультивалютные Price ID должны быть заданы в .env")
    
    # 💱 МАППИНГ: plan → currency → price_id  
    STRIPE_PRICES = {
        "basic_sub": {
            "USD": BASIC_PRICE_ID,
            "EUR": BASIC_EUR_PRICE_ID,
            "GBP": BASIC_GBP_PRICE_ID,
        },
        "premium_sub": {
            "USD": PREMIUM_PRICE_ID,
            "EUR": PREMIUM_EUR_PRICE_ID,
            "GBP": PREMIUM_GBP_PRICE_ID,
        }
    }
    # URL для возврата после оплаты
    # Telegram URLs
    TELEGRAM_SUCCESS_URL = os.getenv("TELEGRAM_SUCCESS_URL", "https://t.me/PulsebookBot")
    TELEGRAM_CANCEL_URL = os.getenv("TELEGRAM_CANCEL_URL", "https://t.me/PulsebookBot")

    # Web URLs - fallback на продакшн
    WEB_SUCCESS_URL = os.getenv("WEB_SUCCESS_URL", "https://pulsebook.health/dashboard?payment_success=true")
    WEB_CANCEL_URL = os.getenv("WEB_CANCEL_URL", "https://pulsebook.health/dashboard?payment_cancelled=true")
    
    # ✅ ИСПРАВЛЕННЫЕ пакеты подписок с правильной локализацией
    SUBSCRIPTION_PACKAGES = {
        "basic_sub": {
            "name": "Basic Subscription",
            "price_cents": 399,
            "price_display": "$3.99",
            "documents": 5,
            "gpt4o_queries": 50,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": BASIC_PRICE_ID,
            "user_friendly_name_key": "package_basic_name",  # ✅ КЛЮЧ ЛОКАЛИЗАЦИИ
            "features_keys": [  # ✅ КЛЮЧИ ВМЕСТО ЗАХАРДКОЖЕННОГО ТЕКСТА
                "package_basic_feature_1",
                "package_basic_feature_2", 
                "package_basic_feature_3"
            ]
        },
        "premium_sub": {
            "name": "Premium Subscription", 
            "price_cents": 999,
            "price_display": "$9.99",
            "documents": 20,
            "gpt4o_queries": 200,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": PREMIUM_PRICE_ID,
            "user_friendly_name_key": "package_premium_name",  # ✅ КЛЮЧ ЛОКАЛИЗАЦИИ
            "features_keys": [  # ✅ КЛЮЧИ ВМЕСТО ЗАХАРДКОЖЕННОГО ТЕКСТА
                "package_premium_feature_1",
                "package_premium_feature_2",
                "package_premium_feature_3"
            ]
        },
        "extra_pack": {
            "name": "Extra Pack",
            "price_cents": 199,
            "price_display": "$1.99",
            "documents": 2,
            "gpt4o_queries": 20 ,
            "type": "one_time",
            "duration_days": 30,
            "user_friendly_name_key": "package_extra_name",  # ✅ КЛЮЧ ЛОКАЛИЗАЦИИ
            "features_keys": [  # ✅ КЛЮЧИ ВМЕСТО ЗАХАРДКОЖЕННОГО ТЕКСТА
                "package_extra_feature_1",
                "package_extra_feature_2",
                "package_extra_feature_3"
            ]
        }
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Проверяет наличие всех необходимых ключей"""
        required_keys = [cls.PUBLISHABLE_KEY, cls.SECRET_KEY]
        
        missing_keys = [key for key in required_keys if not key]
        
        if missing_keys:
            logger.error("Отсутствуют ключи Stripe")
            return False
            
        logger.info("Конфигурация Stripe корректна")
        return True
    
    @classmethod
    def get_package_info(cls, package_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о пакете по ID"""
        return cls.SUBSCRIPTION_PACKAGES.get(package_id)
    
    @classmethod
    def get_all_packages(cls) -> Dict[str, Dict[str, Any]]:
        """Возвращает все доступные пакеты"""
        return cls.SUBSCRIPTION_PACKAGES.copy()
    
    @classmethod
    def get_localized_package_name(cls, package_id: str, lang: str) -> str:
        """✅ НОВАЯ ФУНКЦИЯ: Получает локализованное название пакета"""
        try:
            from db_postgresql import t
            
            package_info = cls.get_package_info(package_id)
            if not package_info:
                return "Unknown Package"
            
            name_key = package_info.get("user_friendly_name_key")
            if name_key:
                return t(name_key, lang)
            
            # Fallback на английское название
            return package_info.get("name", "Unknown Package")
            
        except Exception as e:
            logger.error(f"Ошибка локализации названия пакета")
            # Fallback на английское название
            package_info = cls.get_package_info(package_id)
            return package_info.get("name", "Unknown Package") if package_info else "Unknown Package"
    
    @classmethod
    def get_localized_package_features(cls, package_id: str, lang: str) -> List[str]:
        """✅ НОВАЯ ФУНКЦИЯ: Получает локализованный список особенностей пакета"""
        try:
            from db_postgresql import t
            
            package_info = cls.get_package_info(package_id)
            if not package_info:
                return []
            
            features_keys = package_info.get("features_keys", [])
            localized_features = []
            
            for feature_key in features_keys:
                try:
                    localized_feature = t(feature_key, lang)
                    localized_features.append(localized_feature)
                except:
                    continue
            
            return localized_features
            
        except Exception as e:
            logger.error(f"Ошибка локализации особенностей пакета")
            return []
    
    @classmethod  
    def get_package_display_text(cls, package_id: str, lang: str) -> str:
        """✅ НОВАЯ ФУНКЦИЯ: Получает полное описание пакета для отображения"""
        try:
            from db_postgresql import t
            
            package_info = cls.get_package_info(package_id)
            if not package_info:
                return t("package_not_found", lang)
            
            # Получаем локализованное название
            name = cls.get_localized_package_name(package_id, lang)
            
            # Формируем цену с типом
            if package_info['type'] == 'subscription':
                price_text = f"{package_info['price_display']}/{t('subscription_monthly_short', lang)}"
            else:
                price_text = f"{package_info['price_display']} {t('subscription_one_time_short', lang)}"
            
            # Получаем особенности
            features = cls.get_localized_package_features(package_id, lang)
            
            # Формируем итоговый текст
            text_parts = [
                f"**{name}** — {price_text}",
                ""
            ]
            
            if features:
                text_parts.append(t("package_features_title", lang))
                for feature in features:
                    text_parts.append(f"✅ {feature}")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Ошибка формирования описания пакета")
            
            # Fallback описание
            package_info = cls.get_package_info(package_id)
            if package_info:
                return f"{package_info['name']} — {package_info['price_display']}"
            return "Package information unavailable"
        
    @classmethod
    def get_price_id_for_currency(cls, package_id: str, currency: str) -> Optional[str]:
        """
        Получает Price ID для конкретной валюты
        
        Args:
            package_id: 'basic_sub' или 'premium_sub'
            currency: 'USD', 'EUR', 'GBP'
            
        Returns:
            Price ID из Stripe или None
        """
        return cls.STRIPE_PRICES.get(package_id, {}).get(currency)

# Функция для проверки при запуске
def check_stripe_setup() -> bool:
    """Проверяет настройку Stripe при запуске бота"""
    
    if not StripeConfig.validate_config():
        logger.warning("Stripe configuration not found or invalid")
        return False
    
    try:
        # Тестовый запрос к Stripe API
        stripe.Account.retrieve()
        logger.info("Stripe API connection successful")
        return True
        
    except stripe.error.AuthenticationError:
        logger.error("Invalid Stripe API key")
        return False
        
    except Exception as e:
        logger.error(f"Stripe connection error: {e}")
        return False