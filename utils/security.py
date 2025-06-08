# utils/security.py - Создай этот файл

import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def safe_html_escape(text: str, max_length: int = 4000) -> str:
    """
    Безопасно экранирует HTML и ограничивает длину
    
    Args:
        text: Текст для экранирования
        max_length: Максимальная длина текста
        
    Returns:
        Безопасный HTML текст
    """
    if not text:
        return ""
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length] + "..."
        logger.warning(f"Text truncated to {max_length} characters")
    
    # Экранируем HTML теги и спецсимволы
    return html.escape(text)

async def safe_send_message(message, text: str, title: Optional[str] = None, parse_mode: str = "HTML", reply_markup=None):
    """
    Безопасная отправка сообщения с автоматическим экранированием
    
    Args:
        message: Объект сообщения aiogram
        text: Текст сообщения
        title: Заголовок (опционально)
        parse_mode: Режим парсинга
    """
    try:
        if title:
            safe_title = safe_html_escape(title, 200)
            safe_text = safe_html_escape(text, 3800)  # Оставляем место для заголовка
            final_text = f"<b>{safe_title}</b>\n\n{safe_text}"
        else:
            final_text = safe_html_escape(text, 4000)
        
        await message.answer(final_text, parse_mode=parse_mode, reply_markup=reply_markup)
        
    except Exception as e:
        # Fallback - отправляем без HTML форматирования
        logger.warning(f"HTML send failed, using plain text: {e}")
        try:
            # Убираем HTML теги и отправляем как plain text
            plain_text = html.unescape(text) if text else "Ошибка отображения"
            await message.answer(plain_text[:4000], parse_mode=None)
        except Exception as fallback_error:
            logger.error(f"Even plain text send failed: {fallback_error}")
            await message.answer("❌ Ошибка отправки сообщения")

def safe_callback_data(data: str, max_length: int = 64) -> str:
    """
    Безопасные данные для callback кнопок
    
    Args:
        data: Данные для callback
        max_length: Максимальная длина (лимит Telegram)
        
    Returns:
        Безопасные данные
    """
    if not data:
        return "error"
    
    # Убираем опасные символы
    safe_data = "".join(c for c in data if c.isalnum() or c in "_-")
    
    # Ограничиваем длину
    if len(safe_data) > max_length:
        safe_data = safe_data[:max_length]
    
    return safe_data or "error"

# Функции для быстрой замены в существующем коде
async def safe_answer(message, text: str, **kwargs):
    """Простая замена для message.answer() с защитой от XSS"""
    # Если есть parse_mode=HTML, используем безопасную функцию
    if kwargs.get('parse_mode') == 'HTML':
        await safe_send_message(message, text)
    else:
        # Для plain text просто ограничиваем длину
        safe_text = text[:4000] if text else ""
        await message.answer(safe_text, **kwargs)