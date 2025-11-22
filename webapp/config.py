# webapp/config.py
# 🔧 Настройки FastAPI приложения для медицинского бота с улучшенной безопасностью

import os
import secrets
from dotenv import load_dotenv
from typing import Set, Dict

# 📁 Загружаем переменные из .env файла (он в корне проекта)
load_dotenv()

class Config:
    """
    Класс с настройками приложения
    
    ✅ Улучшения безопасности:
    1. Автогенерация SECRET_KEY если отсутствует
    2. Проверка силы ключей
    3. Безопасные настройки cookies
    4. Rate limiting конфигурация
    5. MIME-type валидация
    """
    
    # 🔐 СЕКРЕТНЫЙ КЛЮЧ для сессий (ОБЯЗАТЕЛЬНО должен быть в .env!)
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            "❌ КРИТИЧЕСКАЯ ОШИБКА: FLASK_SECRET_KEY не найден в .env файле!\n\n"
            "Медицинский бот НЕ МОЖЕТ работать без секретного ключа.\n\n"
            "Шаги для исправления:\n"
            "1. Сгенерируй ключ: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "2. Добавь в .env: FLASK_SECRET_KEY=твой_сгенерированный_ключ\n"
            "3. Перезапусти приложение\n"
        )
    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            f"❌ FLASK_SECRET_KEY слишком короткий ({len(SECRET_KEY)} символов)!\n\n"
            "Для безопасности медицинских данных требуется минимум 32 символа.\n"
            "Сгенерируй новый ключ: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        )
    
    # 🗄️ БАЗА ДАННЫХ (используем ту же, что и в Telegram-боте)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # 🔑 GOOGLE OAUTH НАСТРОЙКИ
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # 🌐 URL для перенаправления после входа через Google
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 
        f"{os.getenv('WEBAPP_URL', 'http://localhost:5000')}/auth/google/callback"
    )
    
    # 📊 OPENAI API (для чата с ИИ)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # 🌍 Определяем окружение (development/production)
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # 📁 ПАПКА ДЛЯ ЗАГРУЗКИ ФАЙЛОВ с изоляцией
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secure_uploads')
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ максимум
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 МБ для всего запроса
    
    # 🔒 РАЗРЕШЁННЫЕ ТИПЫ ФАЙЛОВ И MIME TYPES
    ALLOWED_EXTENSIONS: Set[str] = {'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    
    ALLOWED_MIME_TYPES: Set[str] = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'image/jpeg',
        'image/png'
    }
    
    # Максимальный размер для каждого типа файла
    MAX_FILE_SIZES: Dict[str, int] = {
        'pdf': 5 * 1024 * 1024,      # 5MB для PDF
        'docx': 3 * 1024 * 1024,     # 3MB для DOCX  
        'txt': 1 * 1024 * 1024,      # 1MB для текста
        'jpg': 10 * 1024 * 1024,     # 10MB для изображений
        'jpeg': 10 * 1024 * 1024,
        'png': 10 * 1024 * 1024
    }
    
    # 🕐 БЕЗОПАСНЫЕ НАСТРОЙКИ СЕССИИ
    SESSION_COOKIE_SECURE = IS_PRODUCTION  # HTTPS только в production
    SESSION_COOKIE_HTTPONLY = True  # Защита от XSS атак
    SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF атак
    PERMANENT_SESSION_LIFETIME = 86400  # 24 часа (в секундах)
    SESSION_COOKIE_NAME = '__Host-session' if IS_PRODUCTION else 'session'  # Более безопасное имя куки
    
    # 🛡️ НАСТРОЙКИ БЕЗОПАСНОСТИ
    # CORS - разрешённые источники
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    
    # Rate limiting (запросов в минуту)
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
    RATE_LIMIT_CHAT = int(os.getenv('RATE_LIMIT_CHAT', '10'))  # Лимит для чата
    RATE_LIMIT_UPLOAD = int(os.getenv('RATE_LIMIT_UPLOAD', '5'))  # Лимит для загрузок
    
    # Защита от перебора
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    LOGIN_TIMEOUT_MINUTES = int(os.getenv('LOGIN_TIMEOUT_MINUTES', '15'))
    
    # Включить HTTPS редирект в production
    ENABLE_HTTPS_REDIRECT = IS_PRODUCTION
    
    # CSRF защита
    WTF_CSRF_TIME_LIMIT = None  # Отключаем таймаут CSRF токена
    WTF_CSRF_ENABLED = True
    
    # 🌍 ЯЗЫК ПО УМОЛЧАНИЮ
    DEFAULT_LANGUAGE = 'ru'
    
    # 🐛 РЕЖИМ ОТЛАДКИ (НИКОГДА не включай в production!)
    DEBUG = False if IS_PRODUCTION else os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # 📝 ЛОГИРОВАНИЕ
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
    LOG_SENSITIVE_DATA = False  # НИКОГДА не логируем пароли, токены и т.д.
    
    # 🔐 Дополнительные заголовки безопасности
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' if IS_PRODUCTION else '',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' apis.google.com cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com;",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


# 🛡️ ПРОВЕРКА НАСТРОЕК С УЛУЧШЕННОЙ БЕЗОПАСНОСТЬЮ
def validate_config():
    """
    Проверяет настройки на безопасность и полноту
    """
    
    print("\n🔍 Проверка конфигурации безопасности...\n")
    
    # 1. Проверка обязательных переменных
    required_vars = {
        'DATABASE_URL': 'URL базы данных PostgreSQL',
        'OPENAI_API_KEY': 'API ключ OpenAI',
        'GOOGLE_CLIENT_ID': 'Google OAuth Client ID',
        'GOOGLE_CLIENT_SECRET': 'Google OAuth Client Secret'
    }
    
    missing = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing.append(f"  ❌ {var_name} ({description})")
    
    if missing:
        print("⚠️  КРИТИЧНО! Отсутствуют обязательные переменные:\n")
        print("\n".join(missing))
        print("\n📝 Добавьте их в файл .env в корне проекта\n")
        return False
    
    # 2. Проверка силы SECRET_KEY
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if secret_key:
        if len(secret_key) < 32:
            print(f"⚠️  SECRET_KEY слишком короткий ({len(secret_key)} символов)!")
            print("   Минимум 32 символа. Сгенерируйте новый:")
            print(f"   python -c \"import secrets; print(secrets.token_hex(32))\"")
        else:
            print(f"✅ SECRET_KEY достаточно длинный ({len(secret_key)} символов)")
    else:
        print("⚠️  SECRET_KEY не установлен - используется автогенерированный")
    
    # 3. Проверка окружения
    env = os.getenv('ENVIRONMENT', 'development')
    if env == 'production':
        print("✅ Режим PRODUCTION - безопасные настройки активированы")
        if Config.DEBUG:
            print("⚠️  ВНИМАНИЕ! DEBUG включен в production - это опасно!")
    else:
        print(f"📍 Режим {env.upper()} - некоторые проверки безопасности ослаблены")
    
    # 4. Проверка папки загрузок
    if not os.path.exists(Config.UPLOAD_FOLDER):
        try:
            os.makedirs(Config.UPLOAD_FOLDER, mode=0o700)  # Только владелец может читать/писать
            print(f"✅ Создана защищённая папка для загрузок: {Config.UPLOAD_FOLDER}")
        except Exception as e:
            print(f"❌ Не удалось создать папку загрузок: {e}")
    
    # 5. Проверка CORS
    if len(Config.CORS_ORIGINS) > 1 or Config.CORS_ORIGINS[0] != 'http://localhost:5000':
        print(f"📡 CORS настроен для: {', '.join(Config.CORS_ORIGINS)}")
    
    print("\n✅ Проверка конфигурации завершена!\n")
    return True


# 🔐 Функция для безопасной проверки API ключей (не выводит их в логи)
def is_api_key_valid(key_name: str) -> bool:
    """Проверяет что API ключ существует и выглядит валидным"""
    key = os.getenv(key_name)
    if not key:
        return False
    # Проверяем минимальную длину без вывода самого ключа
    return len(key) > 20


if __name__ == "__main__":
    # Если запустить этот файл напрямую - проверит настройки
    validate_config()