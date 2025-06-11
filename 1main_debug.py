# main_debug.py - Диагностическая версия для поиска проблемы

import asyncio
import os
import sys
import traceback
from datetime import datetime
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def print_step(step_name, status="start"):
    """Печатает информацию о шаге выполнения"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "start":
        print(f"🔄 [{timestamp}] Начинаем: {step_name}")
    elif status == "success":
        print(f"✅ [{timestamp}] Успешно: {step_name}")
    elif status == "error":
        print(f"❌ [{timestamp}] Ошибка: {step_name}")
    elif status == "warning":
        print(f"⚠️ [{timestamp}] Предупреждение: {step_name}")

async def check_basic_setup():
    """Проверяем базовые настройки"""
    print_step("Проверка базовых настроек")
    
    # Проверяем BOT_TOKEN
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print_step("BOT_TOKEN отсутствует в .env", "error")
        return False
    print_step("BOT_TOKEN найден", "success")
    
    # Проверяем OPENAI_API_KEY
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print_step("OPENAI_API_KEY отсутствует", "warning")
    else:
        print_step("OPENAI_API_KEY найден", "success")
    
    return True

async def check_bot_connection():
    """Проверяем подключение к Telegram"""
    print_step("Проверка подключения к Telegram")
    
    try:
        bot_token = os.getenv("BOT_TOKEN")
        bot = Bot(token=bot_token)
        
        # Проверяем подключение
        me = await bot.get_me()
        print_step(f"Подключение к Telegram успешно - @{me.username}", "success")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print_step(f"Ошибка подключения к Telegram: {e}", "error")
        return False

async def check_stripe_setup():
    """Проверяем настройки Stripe"""
    print_step("Проверка настроек Stripe")
    
    try:
        # Импортируем функцию проверки Stripe
        from main import check_stripe_setup
        
        if check_stripe_setup():
            print_step("Stripe настроен корректно", "success")
        else:
            print_step("Stripe не настроен", "warning")
        return True
        
    except ImportError as e:
        print_step(f"Не удалось импортировать функцию check_stripe_setup: {e}", "error")
        return False
    except Exception as e:
        print_step(f"Ошибка проверки Stripe: {e}", "error")
        return False

async def check_webhook_server():
    """Проверяем возможность запуска webhook сервера"""
    print_step("Проверка webhook сервера")
    
    try:
        # Пробуем импортировать модуль
        from webhook_subscription_handler import start_webhook_server
        print_step("Модуль webhook_subscription_handler импортирован", "success")
        
        # Создаем временный бот для теста
        bot_token = os.getenv("BOT_TOKEN")
        bot = Bot(token=bot_token)
        
        # НЕ запускаем сервер, только проверяем возможность создания
        print_step("Webhook сервер готов к запуску", "success")
        
        await bot.session.close()
        return True
        
    except ImportError as e:
        print_step(f"Не удалось импортировать webhook_subscription_handler: {e}", "error")
        return False
    except Exception as e:
        print_step(f"Ошибка проверки webhook: {e}", "error")
        return False

async def check_user_state_manager():
    """Проверяем user state manager"""
    print_step("Проверка user state manager")
    
    try:
        from user_state_manager import user_state_manager
        print_step("User state manager импортирован", "success")
        return True
        
    except ImportError as e:
        print_step(f"Не удалось импортировать user_state_manager: {e}", "error")
        return False
    except Exception as e:
        print_step(f"Ошибка user_state_manager: {e}", "error")
        return False

async def check_database():
    """Проверяем базу данных"""
    print_step("Проверка базы данных")
    
    try:
        # Пробуем импортировать функции БД
        from db_pool import initialize_db_pool, close_db_pool
        print_step("Модули БД импортированы", "success")
        
        # Проверяем файл базы данных
        if os.path.exists("users.db"):
            print_step("Файл базы данных найден", "success")
        else:
            print_step("Файл базы данных не найден", "warning")
        
        # НЕ инициализируем пул, только проверяем импорт
        return True
        
    except ImportError as e:
        print_step(f"Не удалось импортировать модули БД: {e}", "error")
        return False
    except Exception as e:
        print_step(f"Ошибка проверки БД: {e}", "error")
        return False

async def check_openai_api():
    """Проверяем OpenAI API"""
    print_step("Проверка OpenAI API")
    
    try:
        from gpt import check_openai_status
        
        # Проверяем статус API
        is_available = await check_openai_status()
        
        if is_available:
            print_step("OpenAI API доступен", "success")
        else:
            print_step("OpenAI API недоступен", "warning")
        
        return True
        
    except ImportError as e:
        print_step(f"Не удалось импортировать модуль gpt: {e}", "error")
        return False
    except Exception as e:
        print_step(f"Ошибка проверки OpenAI: {e}", "error")
        return False

async def check_handlers():
    """Проверяем импорты обработчиков"""
    print_step("Проверка обработчиков сообщений")
    
    try:
        # Пробуем импортировать все необходимые модули
        modules_to_check = [
            "registration",
            "documents", 
            "keyboards",
            "locales",
            "error_handler"
        ]
        
        for module in modules_to_check:
            try:
                __import__(module)
                print_step(f"Модуль {module} импортирован", "success")
            except ImportError as e:
                print_step(f"Не удалось импортировать {module}: {e}", "error")
                return False
        
        return True
        
    except Exception as e:
        print_step(f"Ошибка проверки обработчиков: {e}", "error")
        return False

async def run_full_diagnosis():
    """Запускаем полную диагностику"""
    print("🔍 Начинаем полную диагностику медицинского бота...")
    print("=" * 60)
    
    checks = [
        ("Базовые настройки", check_basic_setup),
        ("Подключение к Telegram", check_bot_connection),
        ("Настройки Stripe", check_stripe_setup),
        ("Webhook сервер", check_webhook_server),
        ("User State Manager", check_user_state_manager),
        ("База данных", check_database),
        ("OpenAI API", check_openai_api),
        ("Обработчики", check_handlers)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print("\n" + "-" * 40)
        try:
            result = await check_func()
            results[check_name] = result
        except Exception as e:
            print_step(f"Критическая ошибка в {check_name}: {e}", "error")
            print(f"Полная ошибка:\n{traceback.format_exc()}")
            results[check_name] = False
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in results.items():
        status = "✅ ПРОЙДЕНО" if result else "❌ ОШИБКА"
        print(f"{status} - {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("💡 Проблема может быть в логике main.py")
        print("🔧 Попробуйте запустить основной бот с дополнительным логированием")
    else:
        print("⚠️ НАЙДЕНЫ ПРОБЛЕМЫ!")
        print("🔧 Исправьте ошибки выше перед запуском основного бота")
    
    return all_passed

async def main():
    """Главная функция диагностики"""
    try:
        await run_full_diagnosis()
    except KeyboardInterrupt:
        print("\n🛑 Диагностика остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка диагностики: {e}")
        print(f"Полная ошибка:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())