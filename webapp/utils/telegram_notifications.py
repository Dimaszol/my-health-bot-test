# webapp/utils/telegram_notifications.py
# 📨 Отправка уведомлений админу в Telegram

import os
import logging

logger = logging.getLogger(__name__)

# ID админа (твой Telegram ID)
ADMIN_TELEGRAM_ID = 7374723347

# Получаем токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

try:
    if BOT_TOKEN:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        notification_bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    else:
        notification_bot = None
        logger.warning("⚠️ BOT_TOKEN не найден")
        
except ImportError:
    notification_bot = None
    logger.warning("⚠️ aiogram не установлен")


async def send_admin_notification(message: str) -> bool:
    """Отправить уведомление админу в Telegram"""
    if not notification_bot or not ADMIN_TELEGRAM_ID:
        logger.error("❌ Бот или ADMIN_TELEGRAM_ID не настроены")
        return False
    
    try:
        await notification_bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=message,
            parse_mode="HTML"
        )
        logger.info("✅ Уведомление админу отправлено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления админу")
        return False


async def notify_paid_analysis_attempt(user_id: int, user_email: str = None):
    """Уведомление о попытке нажать на платный разбор без лимита"""
    user_info = f"User ID: {user_id}"
    if user_email:
        user_info += f"\nEmail: {user_email}"
    
    message = f"🔔 <b>Попытка платного разбора без лимита</b>\n\n{user_info}"
    return await send_admin_notification(message)


async def notify_document_upload_attempt(user_id: int, user_email: str = None):
    """Уведомление о попытке загрузить документ без лимита"""
    user_info = f"User ID: {user_id}"
    if user_email:
        user_info += f"\nEmail: {user_email}"
    
    message = f"📄 <b>Попытка загрузки документа без лимита</b>\n\n{user_info}"
    return await send_admin_notification(message)