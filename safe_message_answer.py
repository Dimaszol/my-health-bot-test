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
        # 📊 ЛОГИРУЕМ ПОПЫТКУ ОТПРАВКИ
        msg_type = "ERROR" if is_error else "RESPONSE"
        logger.info(f"📤 [SEND-{msg_type}] Отправляем пользователю {user_id}")
        logger.debug(f"📝 [SEND-{msg_type}] Длина: {len(text)} символов")
        
        # 🚨 ПРОВЕРЯЕМ ДЛИНУ СООБЩЕНИЯ
        if len(text) > 4096:
            logger.warning(f"⚠️ [SEND-{msg_type}] Длинное сообщение - разбиваем на части")
            return await _send_long_message(message, text, parse_mode, **kwargs)
        
        # 🚨 ПРОВЕРЯЕМ НА ПУСТОЕ СООБЩЕНИЕ
        if not text or text.strip() == "":
            logger.error(f"❌ [SEND-{msg_type}] Пустое сообщение для пользователя {user_id}")
            text = "❌ Произошла техническая ошибка. Попробуйте еще раз."
            parse_mode = None
        
        # 📤 ОТПРАВЛЯЕМ СООБЩЕНИЕ
        sent_message = await message.answer(
            text=text,
            parse_mode=parse_mode,
            **kwargs
        )
        
        # ✅ УСПЕХ
        logger.info(f"✅ [SEND-{msg_type}] Отправлено пользователю {user_id}, ID: {sent_message.message_id}")
        return True
        
    except Exception as e:
        # ❌ ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОШИБКИ
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"❌ [SEND-{msg_type}] Ошибка для пользователя {user_id}: {error_type}: {error_msg}")
        logger.error(f"📋 [SEND-{msg_type}] Текст: {repr(text[:200])}")
        logger.error(f"📋 [SEND-{msg_type}] Traceback:\n{traceback.format_exc()}")
        
        # 🔍 АНАЛИЗИРУЕМ ОШИБКИ TELEGRAM
        if "Forbidden" in error_msg:
            logger.error(f"🚫 [SEND-{msg_type}] Пользователь {user_id} заблокировал бота")
        elif "Bad Request" in error_msg or "Entity" in error_msg:
            logger.error(f"🔧 [SEND-{msg_type}] Проблема с HTML разметкой")
            
            # Пробуем без разметки
            try:
                logger.info(f"🔄 [SEND-{msg_type}] Повтор без HTML разметки...")
                await message.answer(text=text, parse_mode=None)
                logger.info(f"✅ [SEND-{msg_type}] Отправлено без разметки пользователю {user_id}")
                return True
            except Exception as e2:
                logger.error(f"❌ [SEND-{msg_type}] Даже без разметки ошибка: {e2}")
        
        # 🚨 ПОСЛЕДНЯЯ ПОПЫТКА - ПРОСТОЕ УВЕДОМЛЕНИЕ
        try:
            await message.answer(
                text="❌ Произошла техническая ошибка. Мы работаем над исправлением.",
                parse_mode=None
            )
            logger.info(f"✅ [SEND-{msg_type}] Уведомление об ошибке отправлено пользователю {user_id}")
        except Exception as e3:
            logger.error(f"💥 [SEND-{msg_type}] Критическая ошибка - не удалось отправить даже уведомление: {e3}")
        
        return False

async def _send_long_message(message, text, parse_mode=None, **kwargs):
    """Отправка длинного сообщения частями"""
    user_id = message.from_user.id
    chunk_size = 4000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    logger.info(f"📋 [SEND] Разбиваем на {len(chunks)} частей для пользователя {user_id}")
    
    for i, chunk in enumerate(chunks):
        try:
            if i == 0:
                await message.answer(text=chunk, parse_mode=parse_mode, **kwargs)
            else:
                await message.answer(text=chunk, parse_mode=None)
            
            logger.info(f"✅ [SEND] Часть {i+1}/{len(chunks)} отправлена")
            
            if i < len(chunks) - 1:
                import asyncio
                await asyncio.sleep(0.3)
                
        except Exception as e:
            logger.error(f"❌ [SEND] Ошибка части {i+1}: {e}")
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