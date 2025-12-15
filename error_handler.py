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

# Настройка логирования - НЕ ЛОКАЛИЗУЕТСЯ (это для разработчиков)
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
        self.message = message  # ЭТО В ЛОГИ - не локализуется
        self.user_message = user_message or "Произошла ошибка. Попробуйте позже."  # ЭТО ВИДИТ ПОЛЬЗОВАТЕЛЬ - нужна локализация
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
    ✅ ТОЛЬКО ДЛЯ ПОЛЬЗОВАТЕЛЯ - нужна локализация
    Возвращает понятное пользователю сообщение об ошибке
    """
    try:
        from db_postgresql import t
        
        # ✅ ЭТИ СООБЩЕНИЯ ВИДИТ ПОЛЬЗОВАТЕЛЬ - локализуем
        if isinstance(error, APITimeoutError):
            return t("error_openai_timeout", lang)
        elif isinstance(error, RateLimitError):
            return t("error_openai_rate_limit", lang)
        elif isinstance(error, APIError):
            return t("error_openai_api_error", lang)
        elif isinstance(error, APIConnectionError):
            return t("error_openai_connection", lang)
        elif isinstance(error, (FileNotFoundError, OSError)):
            return t("error_file_corrupted", lang)
        elif isinstance(error, ValueError):
            return t("error_validation_error", lang)
        elif "database" in str(error).lower():
            return t("error_database_error", lang)
        else:
            return t("error_unknown_error", lang)
            
    except ImportError:
        # ✅ FALLBACK для пользователя - локализуем
        fallback_messages = {
            "ru": "❌ Произошла ошибка. Попробуйте позже.",
            "en": "❌ An error occurred. Please try again later.",
            "uk": "❌ Сталася помилка. Спробуйте пізніше.",
            "de": "❌ Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
        }
        return fallback_messages.get(lang, fallback_messages["ru"])

def safe_openai_call(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для безопасных вызовов OpenAI API
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
                    logger.warning(f"OpenAI timeout on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    
                except RateLimitError as e:
                    last_error = e
                    logger.warning(f"Rate limit на попытке {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * 2)
                    
                except APIConnectionError as e:
                    last_error = e
                    logger.error(f"Ошибка соединения с OpenAI на попытке {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
                except APIError as e:
                    last_error = e
                    logger.error(f"OpenAI API error на попытке {attempt + 1}")
                    break
                    
                except Exception as e:
                    last_error = e
                    logger.error(f"Unexpected error in {func.__name__}")
                    break
            
            # ✅ А ВОТ ЭТО видит пользователь - локализуем через get_user_friendly_message
            raise OpenAIError(
                f"OpenAI API недоступен: {last_error}",  # ЭТО В ЛОГИ
                get_user_friendly_message(last_error)     # ✅ ЭТО ПОЛЬЗОВАТЕЛЮ
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
                    # ❌ ЭТО ЛОГИ - НЕ локализуем
                    logger.error(f"Ошибка в асинхронной функции {func.__name__} на попытке {attempt + 1}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            
            # ❌ ЭТО ЛОГИ - НЕ локализуем
            logger.error(f"Все попытки вызова {func.__name__} исчерпаны")
            
            # ✅ ЭТО ПОЛЬЗОВАТЕЛЮ - локализуем
            raise BotError(
                f"Функция {func.__name__} недоступна",  # ЭТО В ЛОГИ
                get_user_friendly_message(last_error)   # ✅ ЭТО ПОЛЬЗОВАТЕЛЮ
            )
        
        return wrapper
    return decorator

def handle_telegram_errors(func: Callable) -> Callable:
    """
    ✅ Декоратор для обработки ошибок в Telegram handlers
    Отправляет ЛОКАЛИЗОВАННЫЕ сообщения пользователю
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
            
        except BotError as e:
            # ❌ ЭТО ЛОГИ - НЕ локализуем
            logger.error(f"BotError в {func.__name__}: {e.message}")
            
            # Получаем message object и user_id
            message = None
            user_id = None
            
            for arg in args:
                if hasattr(arg, 'answer'):
                    message = arg
                    user_id = getattr(arg, 'from_user', {}).id if hasattr(arg, 'from_user') else None
                    break
                elif hasattr(arg, 'message') and hasattr(arg.message, 'answer'):
                    message = arg.message
                    user_id = getattr(arg, 'from_user', {}).id if hasattr(arg, 'from_user') else None
                    break
            
            if message:
                try:
                    # ✅ ПОЛУЧАЕМ ЯЗЫК для локализованного сообщения ПОЛЬЗОВАТЕЛЮ
                    try:
                        from db_postgresql import get_user_language
                        lang = await get_user_language(user_id) if user_id else "ru"
                    except:
                        lang = "ru"
                    
                    # ✅ ЭТО СООБЩЕНИЕ ВИДИТ ПОЛЬЗОВАТЕЛЬ - уже локализовано
                    await message.answer(e.user_message)
                    
                except Exception as send_error:
                    # ❌ ЭТО ЛОГИ - НЕ локализуем
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
            
        except Exception as e:
            # ❌ ЭТО ЛОГИ - НЕ локализуем
            logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            logger.error(f"Unexpected error in {func.__name__}")
            
            # Получаем message object и user_id для ПОЛЬЗОВАТЕЛЯ
            message = None
            user_id = None
            
            for arg in args:
                if hasattr(arg, 'answer'):
                    message = arg
                    user_id = getattr(arg, 'from_user', {}).id if hasattr(arg, 'from_user') else None
                    break
                elif hasattr(arg, 'message') and hasattr(arg.message, 'answer'):
                    message = arg.message
                    user_id = getattr(arg, 'from_user', {}).id if hasattr(arg, 'from_user') else None
                    break
            
            if message:
                try:
                    # ✅ ЛОКАЛИЗОВАННОЕ сообщение для ПОЛЬЗОВАТЕЛЯ
                    try:
                        from db_postgresql import get_user_language, t
                        lang = await get_user_language(user_id) if user_id else "ru"
                        error_message = t("error_unexpected_general", lang)
                    except:
                        # Fallback сообщения для ПОЛЬЗОВАТЕЛЯ
                        fallback_messages = {
                            "ru": "❌ Произошла неожиданная ошибка. Попробуйте позже.",
                            "en": "❌ An unexpected error occurred. Please try again later.",
                            "uk": "❌ Сталася неочікувана помилка. Спробуйте пізніше.",
                            "de": "❌ Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
                        }
                        error_message = fallback_messages["ru"]
                    
                    # ✅ ЭТО ВИДИТ ПОЛЬЗОВАТЕЛЬ
                    await message.answer(error_message)
                except Exception:
                    pass
    
    return wrapper

def check_openai_health() -> bool:
    """
    Проверяет доступность OpenAI API
    """
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return True
        
    except Exception as e:
        # ❌ ЭТО ЛОГИ - НЕ локализуем
        logger.error(f"OpenAI API недоступен")
        return False

def log_error_with_context(error: Exception, context: dict = None):
    
    context = context or {}
    
    error_info = {
        "timestamp": datetime.now(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    }
    
    # ❌ ЭТО ЛОГИ - НЕ локализуем
    logger.error(f"Детальная ошибка: {error_info}")
    
    if isinstance(error, (DatabaseError, APIError)):
        # ❌ ЭТО ЛОГИ - НЕ локализуем
        logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: {error_info}")
