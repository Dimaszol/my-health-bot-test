import logging
import traceback
from typing import Union, Optional
from aiogram import types

logger = logging.getLogger(__name__)

async def send_safe_message(
    message: types.Message, 
    text: str, 
    parse_mode: Optional[str] = "HTML",
    is_error: bool = False,
    **kwargs
) -> bool:
    """
    🛡️ УНИВЕРСАЛЬНАЯ БЕЗОПАСНАЯ ОТПРАВКА СООБЩЕНИЙ
    
    Args:
        message: Telegram message объект
        text: Текст для отправки
        parse_mode: Режим разметки (HTML, Markdown, None)
        is_error: True если это сообщение об ошибке
        **kwargs: Дополнительные параметры
        
    Returns:
        bool: True если отправлено успешно
    """
    
    user_id = message.from_user.id
    
    try:
        # 🚨 ПРОВЕРЯЕМ ДЛИНУ СООБЩЕНИЯ
        if len(text) > 4096:
            return await _send_long_message(message, text, parse_mode, **kwargs)
        
        # 🚨 ПРОВЕРЯЕМ НА ПУСТОЕ СООБЩЕНИЕ
        if not text or text.strip() == "":
            logger.error(f"❌ Empty message for user_id={user_id}")
            text = "❌ Произошла техническая ошибка. Попробуйте еще раз."
            parse_mode = None
        
        # 📤 ОТПРАВЛЯЕМ СООБЩЕНИЕ
        sent_message = await message.answer(
            text=text,
            parse_mode=parse_mode,
            **kwargs
        )
        
        return True
        
    except Exception as e:
        # ❌ МИНИМАЛЬНОЕ ЛОГИРОВАНИЕ ОШИБКИ (БЕЗ МЕДИЦИНСКИХ ДАННЫХ)
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"❌ Send failed: user_id={user_id}, error={error_type}")
        
        # 🔍 АНАЛИЗИРУЕМ ОШИБКИ TELEGRAM
        if "Forbidden" in error_msg:
            logger.error(f"🚫 User blocked bot: user_id={user_id}")
        elif "Bad Request" in error_msg or "Entity" in error_msg:
            # Пробуем без разметки
            try:
                await message.answer(text=text, parse_mode=None)
                return True
            except Exception:
                pass
        
        # 🚨 ПОСЛЕДНЯЯ ПОПЫТКА - ПРОСТОЕ УВЕДОМЛЕНИЕ
        try:
            await message.answer(
                text="❌ Произошла техническая ошибка. Мы работаем над исправлением.",
                parse_mode=None
            )
        except Exception as e3:
            logger.error(f"💥 Critical: Cannot send any message to user_id={user_id}")
        
        return False

async def _send_long_message(message, text, parse_mode=None, **kwargs):
    """Отправка длинного сообщения частями"""
    user_id = message.from_user.id
    chunk_size = 4000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    for i, chunk in enumerate(chunks):
        try:
            if i == 0:
                await message.answer(text=chunk, parse_mode=parse_mode, **kwargs)
            else:
                await message.answer(text=chunk, parse_mode=None)
            
            if i < len(chunks) - 1:
                import asyncio
                await asyncio.sleep(0.3)
                
        except Exception as e:
            logger.error(f"❌ Long message chunk failed: user_id={user_id}, chunk={i+1}/{len(chunks)}")
            return False
    
    return True

# 🎯 СПЕЦИАЛЬНАЯ ФУНКЦИЯ ДЛЯ ОШИБОК (упрощает замену в коде)
async def send_error_message(message: types.Message, error_text: str) -> bool:
    """
    Отправка сообщения об ошибке (без HTML разметки для безопасности)
    
    Args:
        message: Telegram message объект  
        error_text: Текст ошибки (уже переведенный)
        
    Returns:
        bool: True если отправлено успешно
    """
    return await send_safe_message(
        message=message, 
        text=error_text, 
        parse_mode=None,  # Без разметки для ошибок
        is_error=True
    )

# 🎯 СПЕЦИАЛЬНАЯ ФУНКЦИЯ ДЛЯ ОБЫЧНЫХ ОТВЕТОВ
async def send_response_message(message: types.Message, response_text: str) -> bool:
    """
    Отправка обычного ответа (с HTML разметкой)
    
    Args:
        message: Telegram message объект
        response_text: Текст ответа
        
    Returns:
        bool: True если отправлено успешно
    """
    return await send_safe_message(
        message=message, 
        text=response_text, 
        parse_mode="HTML",
        is_error=False
    )