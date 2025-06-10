# stripe_config.py - Конфигурация Stripe для медицинского бота

import os
import stripe
import logging
from typing import Dict, Any, Optional
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
    
    # Пакеты подписок (цены в центах!)
    SUBSCRIPTION_PACKAGES = {
        "basic_sub": {
            "name": "Basic Subscription",
            "price_cents": 399,
            "price_display": "$3.99/month",
            "documents": 5,
            "gpt4o_queries": 100,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": "price_1RXp3eCS4n1EZxNVbn0G3WsQ",  # Заменить на реальный
            # ✅ НОВЫЕ пользовательские описания
            "user_friendly_name": "Basic Subscription",
            "features": {
                "ru": [
                    "5 загруженных документов или снимков",
                    "100 глубоких медицинских ответов",
                    "Приоритетная обработка ИИ"
                ],
                "uk": [
                    "5 завантажених документів або знімків", 
                    "100 глибоких медичних відповідей",
                    "Пріоритетна обробка ШІ"
                ],
                "en": [
                    "5 uploaded documents or scans",
                    "100 deep medical responses", 
                    "Priority AI processing"
                ]
            }
        },
        "premium_sub": {
            "name": "Premium Subscription", 
            "price_cents": 999,
            "price_display": "$9.99/month",
            "documents": 20,
            "gpt4o_queries": 400,
            "type": "subscription",
            "duration_days": 30,
            "stripe_price_id": "price_1RXp4qCS4n1EZxNVjJX9xNgf",  # Заменить на реальный
            "user_friendly_name": "Premium Subscription",
            "features": {
                "ru": [
                    "20 загруженных документов или снимков",
                    "400 глубоких медицинских ответов",
                    "Приоритетная обработка ИИ",
                    "Расширенный анализ снимков"
                ],
                "uk": [
                    "20 завантажених документів або знімків",
                    "400 глибоких медичних відповідей", 
                    "Пріоритетна обробка ШІ",
                    "Розширений аналіз знімків"
                ],
                "en": [
                    "20 uploaded documents or scans",
                    "400 deep medical responses",
                    "Priority AI processing", 
                    "Advanced scan analysis"
                ]
            }
        },
        "extra_pack": {
            "name": "Extra Pack",
            "price_cents": 199,
            "price_display": "$1.99",
            "documents": 3,
            "gpt4o_queries": 30,
            "type": "one_time",
            "duration_days": 30,
            "user_friendly_name": "Extra Pack",
            "features": {
                "ru": [
                    "3 загруженных документа или снимка",
                    "30 глубоких медицинских ответов",
                    "Действует 30 дней"
                ],
                "uk": [
                    "3 завантажених документи або знімки",
                    "30 глибоких медичних відповідей",
                    "Діє 30 днів"
                ],
                "en": [
                    "3 uploaded documents or scans", 
                    "30 deep medical responses",
                    "Valid for 30 days"
                ]
            }
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