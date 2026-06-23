# webapp/utils/logger.py
# 🔒 Безопасное логирование с маскированием медицинских данных

import logging
import re
from typing import Any, Dict

# Настраиваем логгер
logger = logging.getLogger('medical_bot')
logger.setLevel(logging.INFO)

# Создаём handler для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Формат логов (БЕЗ чувствительных данных)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def mask_email(email: str) -> str:
    """
    Маскирует email: user@example.com → u***r@e***.com
    """
    if not email or '@' not in email:
        return "***"
    
    parts = email.split('@')
    username = parts[0]
    domain = parts[1]
    
    if len(username) <= 2:
        masked_username = username[0] + '***'
    else:
        masked_username = username[0] + '***' + username[-1]
    
    domain_parts = domain.split('.')
    if len(domain_parts[0]) <= 2:
        masked_domain = domain_parts[0][0] + '***'
    else:
        masked_domain = domain_parts[0][0] + '***'
    
    return f"{masked_username}@{masked_domain}.{domain_parts[-1]}"


def mask_user_id(user_id: Any) -> str:
    if not user_id:
        return "***"
    
    return f"user_***{str(user_id)[-4:]}"


def mask_sensitive_text(text: str, max_length: int = 50) -> str:
    """
    Маскирует медицинский текст:
    - Оставляет первые 50 символов
    - Удаляет медицинские термины
    - Заменяет числа на ***
    """
    if not text:
        return ""
    
    # Обрезаем длинный текст
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # Маскируем числа (могут быть телефоны, даты рождения)
    text = re.sub(r'\d{3,}', '***', text)
    
    # Маскируем email если есть
    text = re.sub(r'\S+@\S+', '***@***.***', text)
    
    return text


def safe_log_info(message: str, **kwargs):
    """
    Безопасное логирование INFO с автоматической маскировкой
    
    Пример:
        safe_log_info("Пользователь вошёл", user_id=123, email="user@example.com")
        → "Пользователь вошёл | user_id=user_***123 | email=u***r@e***.com"
    """
    # Маскируем чувствительные данные
    masked_kwargs = {}
    for key, value in kwargs.items():
        if key == 'email' and value:
            masked_kwargs[key] = mask_email(str(value))
        elif key == 'user_id' and value:
            masked_kwargs[key] = mask_user_id(value)
        elif key in ['message', 'text', 'content'] and value:
            masked_kwargs[key] = mask_sensitive_text(str(value))
        else:
            masked_kwargs[key] = value
    
    # Формируем безопасное сообщение
    if masked_kwargs:
        params_str = ' | '.join([f"{k}={v}" for k, v in masked_kwargs.items()])
        full_message = f"{message} | {params_str}"
    else:
        full_message = message
    
    logger.info(full_message)


def safe_log_error(message: str, error: Exception = None, **kwargs):
    """
    Безопасное логирование ERROR
    """
    masked_kwargs = {}
    for key, value in kwargs.items():
        if key == 'email' and value:
            masked_kwargs[key] = mask_email(str(value))
        elif key == 'user_id' and value:
            masked_kwargs[key] = mask_user_id(value)
        else:
            masked_kwargs[key] = value
    
    if masked_kwargs:
        params_str = ' | '.join([f"{k}={v}" for k, v in masked_kwargs.items()])
        full_message = f"{message} | {params_str}"
    else:
        full_message = message
    
    if error:
        full_message += f" | error={type(error).__name__}: {str(error)}"
    
    logger.error(full_message)


def safe_log_warning(message: str, **kwargs):
    """
    Безопасное логирование WARNING
    """
    # То же что и safe_log_info, но с уровнем WARNING
    masked_kwargs = {}
    for key, value in kwargs.items():
        if key == 'email' and value:
            masked_kwargs[key] = mask_email(str(value))
        elif key == 'user_id' and value:
            masked_kwargs[key] = mask_user_id(value)
        elif key in ['message', 'text'] and value:
            masked_kwargs[key] = mask_sensitive_text(str(value))
        else:
            masked_kwargs[key] = value
    
    if masked_kwargs:
        params_str = ' | '.join([f"{k}={v}" for k, v in masked_kwargs.items()])
        full_message = f"{message} | {params_str}"
    else:
        full_message = message
    
    logger.warning(full_message)