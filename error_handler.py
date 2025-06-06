# error_handler.py - Централизованная обработка ошибок

import logging
import asyncio
import functools
import traceback
from typing import Optional, Callable, Any
from datetime import datetime
import time
import openai
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_errors.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BotError(Exception):
    """Базовое исключение для ошибок бота"""
    def __init__(self, message: str, user_message: str = None):
        self.message = message
        self.user_message = user_message or "Произошла ошибка. Попробуйте позже."
        super().__init__(self.message)

class OpenAIError(BotError):
    """Ошибки связанные с OpenAI API"""
    pass

class FileProcessingError(BotError):
    """Ошибки обработки файлов"""
    pass

class DatabaseError(BotError):
    """Ошибки базы данных"""
    pass

def get_user_friendly_message(error: Exception, lang: str = "ru") -> str:
    """
    Возвращает понятное пользователю сообщение об ошибке
    
    Args:
        error: Исключение
        lang: Язык пользователя
        
    Returns:
        Сообщение для пользователя
    """
    messages = {
        "ru": {
            "openai_timeout": "⏱️ OpenAI не отвечает. Попробуйте через минуту.",
            "openai_rate_limit": "⏳ Слишком много запросов. Подождите немного.",
            "openai_api_error": "🤖 Проблемы с ИИ-сервисом. Попробуйте позже.",
            "openai_connection": "🌐 Нет связи с сервером ИИ. Проверьте интернет.",
            "file_too_large": "📁 Файл слишком большой для обработки.",
            "file_corrupted": "📄 Файл поврежден или не читается.",
            "database_error": "💾 Проблема с сохранением данных. Попробуйте еще раз.",
            "unknown_error": "❌ Неожиданная ошибка. Мы уже работаем над исправлением.",
            "validation_error": "⚠️ Некорректные данные. Проверьте ввод."
        },
        "en": {
            "openai_timeout": "⏱️ OpenAI is not responding. Try again in a minute.",
            "openai_rate_limit": "⏳ Too many requests. Please wait a moment.",
            "openai_api_error": "🤖 AI service issues. Please try later.",
            "openai_connection": "🌐 No connection to AI server. Check your internet.",
            "file_too_large": "📁 File too large for processing.",
            "file_corrupted": "📄 File is corrupted or unreadable.",
            "database_error": "💾 Data saving issue. Please try again.",
            "unknown_error": "❌ Unexpected error. We're working on a fix.",
            "validation_error": "⚠️ Invalid data. Please check your input."
        },
        "uk": {
            "openai_timeout": "⏱️ OpenAI не відповідає. Спробуйте через хвилину.",
            "openai_rate_limit": "⏳ Занадто багато запитів. Зачекайте трохи.",
            "openai_api_error": "🤖 Проблеми з ШІ-сервісом. Спробуйте пізніше.",
            "openai_connection": "🌐 Немає зв'язку з сервером ШІ. Перевірте інтернет.",
            "file_too_large": "📁 Файл занадто великий для обробки.",
            "file_corrupted": "📄 Файл пошкоджений або не читається.",
            "database_error": "💾 Проблема із збереженням даних. Спробуйте ще раз.",
            "unknown_error": "❌ Неочікувана помилка. Ми вже працюємо над виправленням.",
            "validation_error": "⚠️ Некоректні дані. Перевірте введення."
        }
    }
    
    lang_messages = messages.get(lang, messages["ru"])
    
    # Определяем тип ошибки и возвращаем соответствующее сообщение
    if isinstance(error, APITimeoutError):
        return lang_messages["openai_timeout"]
    elif isinstance(error, RateLimitError):
        return lang_messages["openai_rate_limit"]
    elif isinstance(error, APIError):
        return lang_messages["openai_api_error"]
    elif isinstance(error, APIConnectionError):
        return lang_messages["openai_connection"]
    elif isinstance(error, (FileNotFoundError, OSError)):
        return lang_messages["file_corrupted"]
    elif isinstance(error, ValueError):
        return lang_messages["validation_error"]
    elif "database" in str(error).lower():
        return lang_messages["database_error"]
    else:
        return lang_messages["unknown_error"]

def safe_openai_call(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для безопасных вызовов OpenAI API
    
    Args:
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except APITimeoutError as e:
                    last_error = e
                    logger.warning(f"OpenAI timeout на попытке {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Увеличиваем задержку
                    
                except RateLimitError as e:
                    last_error = e
                    logger.warning(f"Rate limit на попытке {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * 2)  # Двойная задержка для rate limit
                    
                except APIConnectionError as e:
                    last_error = e
                    logger.error(f"Ошибка соединения с OpenAI на попытке {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
                except APIError as e:
                    last_error = e
                    logger.error(f"OpenAI API error на попытке {attempt + 1}: {e}")
                    # Для API ошибок не повторяем
                    break
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
                    logger.error(traceback.format_exc())
                    break
            
            # Если все попытки исчерпаны
            logger.error(f"Все попытки вызова {func.__name__} исчерпаны. Последняя ошибка: {last_error}")
            raise OpenAIError(
                f"OpenAI API недоступен: {last_error}",
                get_user_friendly_message(last_error)
            )
        
        return wrapper
    return decorator

def safe_async_call(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для безопасных асинхронных вызовов
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"Ошибка в асинхронной функции {func.__name__} на попытке {attempt + 1}: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            
            logger.error(f"Все попытки вызова {func.__name__} исчерпаны")
            raise BotError(f"Функция {func.__name__} недоступна", get_user_friendly_message(last_error))
        
        return wrapper
    return decorator

def handle_telegram_errors(func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок в Telegram handlers
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
            
        except BotError as e:
            # Наши кастомные ошибки - отправляем пользователю понятное сообщение
            logger.error(f"BotError в {func.__name__}: {e.message}")
            
            # Получаем message object из args
            message = None
            for arg in args:
                if hasattr(arg, 'answer'):
                    message = arg
                    break
                elif hasattr(arg, 'message') and hasattr(arg.message, 'answer'):
                    message = arg.message
                    break
            
            if message:
                try:
                    await message.answer(e.user_message)
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            
        except Exception as e:
            # Неожиданные ошибки
            logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            
            # Пытаемся отправить общее сообщение об ошибке
            message = None
            for arg in args:
                if hasattr(arg, 'answer'):
                    message = arg
                    break
                elif hasattr(arg, 'message') and hasattr(arg.message, 'answer'):
                    message = arg.message
                    break
            
            if message:
                try:
                    await message.answer("❌ Произошла неожиданная ошибка. Попробуйте позже.")
                except Exception:
                    pass  # Ничего не можем сделать
    
    return wrapper

# Функция для проверки состояния OpenAI API
def check_openai_health() -> bool:
    """
    Проверяет доступность OpenAI API
    
    Returns:
        True если API доступен
    """
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Простой тестовый запрос
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return True
        
    except Exception as e:
        logger.error(f"OpenAI API недоступен: {e}")
        return False

# Функция для логирования ошибок с контекстом
def log_error_with_context(error: Exception, context: dict = None):
    """
    Логирует ошибку с дополнительным контекстом
    
    Args:
        error: Исключение
        context: Дополнительная информация (user_id, action, etc.)
    """
    context = context or {}
    
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    }
    
    logger.error(f"Детальная ошибка: {error_info}")
    
    # Если это критическая ошибка - можно добавить отправку уведомления админу
    if isinstance(error, (DatabaseError, APIError)):
        logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: {error_info}")

# Пример использования декораторов (для справки)
if __name__ == "__main__":
    # Тест декоратора
    @safe_openai_call(max_retries=2, delay=1.0)
    def test_openai():
        raise APITimeoutError("Test timeout")
    
    try:
        test_openai()
    except OpenAIError as e:
        print(f"Поймана ошибка: {e.user_message}")