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
    
    # URL для возврата после оплаты
    SUCCESS_URL = "https://t.me/DrZolinBot"
    CANCEL_URL = "https://t.me/DrZolinBot"
    
    # ✅ ИСПРАВЛЕННЫЕ пакеты подписок с правильной локализацией
    SUBSCRIPTION_PACKAGES = {
        "basic_sub": {
            "name": "Basic Subscription",
            "price_cents": 399,
            "price_display": "$3.99",
            "documents": 5,
            "gpt4o_queries": 100,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": "price_1RXp3eCS4n1EZxNVbn0G3WsQ",  # Заменить на реальный
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
            "gpt4o_queries": 400,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": "price_1RXp4qCS4n1EZxNVjJX9xNgf",  # Заменить на реальный
            "user_friendly_name_key": "package_premium_name",  # ✅ КЛЮЧ ЛОКАЛИЗАЦИИ
            "features_keys": [  # ✅ КЛЮЧИ ВМЕСТО ЗАХАРДКОЖЕННОГО ТЕКСТА
                "package_premium_feature_1",
                "package_premium_feature_2",
                "package_premium_feature_3",
                "package_premium_feature_4"
            ]
        },
        "extra_pack": {
            "name": "Extra Pack",
            "price_cents": 199,
            "price_display": "$1.99",
            "documents": 3,
            "gpt4o_queries": 30,
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
            logger.error("❌ Отсутствуют ключи Stripe в .env файле")
            return False
            
        logger.info("✅ Конфигурация Stripe корректна")
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
            logger.error(f"Ошибка локализации названия пакета {package_id}: {e}")
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
                    # Если ключ не найден, пропускаем
                    logger.warning(f"Ключ локализации {feature_key} не найден для языка {lang}")
                    continue
            
            return localized_features
            
        except Exception as e:
            logger.error(f"Ошибка локализации особенностей пакета {package_id}: {e}")
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
            logger.error(f"Ошибка формирования описания пакета {package_id}: {e}")
            
            # Fallback описание
            package_info = cls.get_package_info(package_id)
            if package_info:
                return f"{package_info['name']} — {package_info['price_display']}"
            return "Package information unavailable"

# Функция для проверки при запуске
def check_stripe_setup() -> bool:
    """Проверяет настройку Stripe при запуске бота"""
    print("🔍 Проверка настройки Stripe...")
    
    if not StripeConfig.validate_config():
        print("❌ Stripe не настроен. Проверьте .env файл")
        return False
    
    try:
        # Тестовый запрос к Stripe API
        stripe.Account.retrieve()
        print("✅ Соединение с Stripe API успешно")
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Неверный Stripe API ключ")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Stripe: {e}")
        return False

if __name__ == "__main__":
    # Тест конфигурации
    success = check_stripe_setup()
    if success:
        print("\n📦 Доступные пакеты:")
        for pkg_id, pkg_info in StripeConfig.get_all_packages().items():
            print(f"  • {pkg_info['name']}: {pkg_info['price_display']}")
    else:
        print("\n💡 Добавьте ключи Stripe в .env файл")