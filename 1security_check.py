# startup_check.py - Проверки при запуске бота

import os
import sys
from pathlib import Path

def check_environment():
    """Проверяет критичные настройки перед запуском"""
    
    print("🔍 Проверка окружения...")
    
    # Проверка .env файла
    if not os.path.exists('.env'):
        print("❌ ОШИБКА: файл .env не найден!")
        print("Создайте файл .env с:")
        print("BOT_TOKEN=ваш_токен")
        print("OPENAI_API_KEY=ваш_ключ")
        return False
    
    # Проверка ключей
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not bot_token:
        print("❌ ОШИБКА: BOT_TOKEN не задан в .env")
        return False
    
    if not openai_key:
        print("❌ ОШИБКА: OPENAI_API_KEY не задан в .env")
        return False
        
    # Проверка директорий
    Path("files").mkdir(exist_ok=True)
    Path("vector_store").mkdir(exist_ok=True)
    
    print("✅ Все критичные настройки в порядке")
    return True

def check_dependencies():
    """Проверяет установленные зависимости"""
    
    critical_packages = [
        'aiogram', 'openai', 'chromadb', 'aiosqlite', 
        'dotenv', 'pdf2image', 'tiktoken'
    ]
    
    missing = []
    for package in critical_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ ОШИБКА: Не установлены пакеты: {', '.join(missing)}")
        print("Установите: pip install -r requirements.txt")
        return False
    
    print("✅ Все зависимости установлены")
    return True

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    if not check_environment():
        sys.exit(1)
    print("🚀 Все проверки пройдены, можно запускать бота!")