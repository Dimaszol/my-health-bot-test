# notification_system.py - Система уведомлений о подписке

import logging
from datetime import datetime
from subscription_manager import SubscriptionManager, check_document_limit, check_gpt4o_limit
from subscription_handlers import SubscriptionHandlers, upsell_tracker
from db import get_user_language

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Система уведомлений о подписке и лимитах"""
    
    @staticmethod
    async def check_and_notify_limits(message, user_id: int, action_type: str = "message") -> bool:
        """
        Проверяет лимиты и показывает уведомления при необходимости
        
        Args:
            message: Объект сообщения для отправки уведомлений
            user_id: ID пользователя
            action_type: Тип действия ("message", "document", "image")
            
        Returns:
            bool: True если можно продолжить действие, False если лимиты исчерпаны
        """
        try:
            # Для обычных сообщений - проверяем счетчик upsell
            if action_type == "message":
                return await NotificationSystem._handle_message_upsell(message, user_id)
            
            # Для документов и изображений - проверяем лимиты
            elif action_type in ["document", "image"]:
                return await NotificationSystem._handle_document_limits(message, user_id, action_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов для пользователя {user_id}: {e}")
            return True  # В случае ошибки разрешаем действие
    
    @staticmethod
    async def _handle_message_upsell(message, user_id: int) -> bool:
        """
        Обрабатывает показ upsell для обычных сообщений
        
        Args:
            message: Объект сообщения
            user_id: ID пользователя
            
        Returns:
            bool: True (сообщения всегда разрешены)
        """
        try:
            # Проверяем есть ли GPT-4o лимиты
            has_gpt4o_limits = await check_gpt4o_limit(user_id)
            
            if not has_gpt4o_limits:
                # Увеличиваем счетчик сообщений
                upsell_tracker.increment_message_count(user_id)
                
                # Проверяем нужно ли показать upsell (каждые 5 сообщений)
                if upsell_tracker.should_show_upsell(user_id):
                    await SubscriptionHandlers.show_subscription_upsell(
                        message, user_id, reason="better_response"
                    )
            
            return True  # Сообщения всегда разрешены
            
        except Exception as e:
            logger.error(f"Ошибка обработки message upsell для пользователя {user_id}: {e}")
            return True
    
    @staticmethod
    async def _handle_document_limits(message, user_id: int, action_type: str) -> bool:
        """
        Обрабатывает проверку лимитов для документов/изображений
        
        Args:
            message: Объект сообщения
            user_id: ID пользователя  
            action_type: Тип действия ("document" или "image")
            
        Returns:
            bool: True если лимиты есть, False если исчерпаны
        """
        try:
            # Проверяем лимиты на документы
            has_document_limits = await check_document_limit(user_id)
            
            if not has_document_limits:
                # Показываем уведомление о нехватке лимитов
                await NotificationSystem._show_limits_exceeded_notification(
                    message, user_id, action_type
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов документов для пользователя {user_id}: {e}")
            return True  # В случае ошибки разрешаем действие
    
    @staticmethod
    async def _show_limits_exceeded_notification(message, user_id: int, action_type: str):
        """Обновленное уведомление о превышении лимитов"""
        try:
            lang = await get_user_language(user_id)
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            # Новые тексты без упоминания GPT-4o
            if action_type == "document":
                limit_messages = {
                    "ru": f"📄 **Лимит на документы исчерпан**\n\n📊 **Ваши текущие лимиты:**\n• Документы: {limits['documents_left']}\n• Глубокие ответы: {limits['gpt4o_queries_left']}\n\n💎 Оформите подписку для загрузки большего количества документов и получения детальных медицинских анализов!",
                    "uk": f"📄 **Ліміт на документи вичерпано**\n\n📊 **Ваші поточні ліміти:**\n• Документи: {limits['documents_left']}\n• Глибокі відповіді: {limits['gpt4o_queries_left']}\n\n💎 Оформіть підписку для завантаження більшої кількості документів та отримання детальних медичних аналізів!",
                    "en": f"📄 **Document limit exceeded**\n\n📊 **Your current limits:**\n• Documents: {limits['documents_left']}\n• Deep responses: {limits['gpt4o_queries_left']}\n\n💎 Get a subscription to upload more documents and receive detailed medical analysis!"
                }
            else:  # image
                limit_messages = {
                    "ru": f"📸 **Лимит на анализ изображений исчерпан**\n\n📊 **Ваши текущие лимиты:**\n• Документы: {limits['documents_left']}\n• Глубокие ответы: {limits['gpt4o_queries_left']}\n\n💎 Оформите подписку для анализа большего количества медицинских снимков с подробными заключениями!",
                    "uk": f"📸 **Ліміт на аналіз зображень вичерпано**\n\n📊 **Ваші поточні ліміти:**\n• Документи: {limits['documents_left']}\n• Глибокі відповіді: {limits['gpt4o_queries_left']}\n\n💎 Оформіть підписку для аналізу більшої кількості медичних знімків з детальними висновками!",
                    "en": f"📸 **Image analysis limit exceeded**\n\n📊 **Your current limits:**\n• Documents: {limits['documents_left']}\n• Deep responses: {limits['gpt4o_queries_left']}\n\n💎 Get a subscription to analyze more medical scans with detailed conclusions!"
                }
            
            await SubscriptionHandlers.show_subscription_upsell(
                message, user_id, reason="limits_exceeded"
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа уведомления о лимитах для пользователя {user_id}: {e}")
    
    @staticmethod
    async def notify_successful_purchase(user_id: int, package_id: str):
        """
        Уведомляет об успешной покупке (сбрасывает счетчики upsell)
        
        Args:
            user_id: ID пользователя
            package_id: ID купленного пакета
        """
        try:
            # Сбрасываем счетчик upsell сообщений
            upsell_tracker.reset_count(user_id)
            
            logger.info(f"Счетчик upsell сброшен для пользователя {user_id} после покупки {package_id}")
            
        except Exception as e:
            logger.error(f"Ошибка сброса счетчика upsell для пользователя {user_id}: {e}")
    
    @staticmethod
    async def check_subscription_expiry_warnings():
        """
        Проверяет приближающиеся истечения подписок и отправляет предупреждения
        (Функция для будущего использования в фоновых задачах)
        """
        try:
            # TODO: Реализовать отправку предупреждений за 3 дня до истечения
            # Пока оставляем заготовку для будущей реализации
            pass
            
        except Exception as e:
            logger.error(f"Ошибка проверки истечения подписок: {e}")

# Вспомогательные функции для интеграции в существующий код

async def should_show_document_upload(user_id: int) -> bool:
    """Проверяет можно ли показать интерфейс загрузки документа"""
    return await check_document_limit(user_id)

async def should_show_image_upload(user_id: int) -> bool:
    """Проверяет можно ли показать интерфейс загрузки изображения"""
    return await check_document_limit(user_id)

async def handle_limits_exceeded_for_upload(message, user_id: int, upload_type: str):
    """
    Обрабатывает превышение лимитов при попытке загрузки
    
    Args:
        message: Объект сообщения
        user_id: ID пользователя
        upload_type: Тип загрузки ("document" или "image")
    """
    await NotificationSystem._show_limits_exceeded_notification(
        message, user_id, upload_type
    )

async def increment_message_counter_for_upsell(user_id: int):
    """Увеличивает счетчик сообщений для upsell (если нет GPT-4o лимитов)"""
    try:
        has_gpt4o_limits = await check_gpt4o_limit(user_id)
        if not has_gpt4o_limits:
            upsell_tracker.increment_message_count(user_id)
    except Exception as e:
        logger.error(f"Ошибка увеличения счетчика upsell для пользователя {user_id}: {e}")

async def should_show_upsell_for_message(user_id: int) -> bool:
    """Проверяет нужно ли показать upsell для сообщения"""
    try:
        has_gpt4o_limits = await check_gpt4o_limit(user_id)
        if not has_gpt4o_limits:
            return upsell_tracker.should_show_upsell(user_id)
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки upsell для пользователя {user_id}: {e}")
        return False