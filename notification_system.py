# notification_system.py - Система уведомлений о подписке

import logging
from datetime import datetime
from subscription_manager import SubscriptionManager, check_document_limit, check_gpt4o_limit
from subscription_handlers import SubscriptionHandlers, upsell_tracker
from db_postgresql import get_user_language, t

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Система уведомлений о подписке и лимитах"""
    
    @staticmethod
    async def check_and_notify_limits(message, user_id: int, action_type: str) -> bool:
        """
        ✅ ИСПРАВЛЕННАЯ версия: Правильно проверяет лимиты в зависимости от типа действия
        
        Args:
            message: Объект сообщения
            user_id: ID пользователя
            action_type: Тип действия ("document" или "image")
            
        Returns:
            bool: True если лимиты есть, False если исчерпаны
        """
        try:
            if action_type == "document":
                # Для документов проверяем лимиты на документы
                has_limits = await check_document_limit(user_id)
            elif action_type == "image":
                # ✅ ИСПРАВЛЕНИЕ: Для изображений проверяем лимиты GPT-4o
                from subscription_manager import check_gpt4o_limit
                has_limits = await check_gpt4o_limit(user_id)
            else:
                # Неизвестный тип - проверяем документы по умолчанию
                has_limits = await check_document_limit(user_id)
            
            if not has_limits:
                # Показываем уведомление о нехватке лимитов
                await NotificationSystem._show_limits_exceeded_notification(
                    message, user_id, action_type
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов для пользователя")
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
            return True  # В случае ошибки разрешаем действие
    
    @staticmethod
    async def _show_limits_exceeded_notification(message, user_id: int, action_type: str):
        """Обновленное уведомление о превышении лимитов"""
        try:
            lang = await get_user_language(user_id)
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            # ✅ ДОБАВИТЬ: Отправку сообщения о лимитах
            from db_postgresql import t
            
            if action_type == "document":
                text = t("document_limit_exceeded", lang, 
                        documents_left=limits['documents_left'], 
                        gpt4o_queries_left=limits['gpt4o_queries_left'])
            else:  # image
                text = t("image_limit_exceeded", lang,
                        documents_left=limits['documents_left'], 
                        gpt4o_queries_left=limits['gpt4o_queries_left'])
            
            # ✅ ДОБАВИТЬ: Отправляем сообщение
            await message.answer(text, parse_mode="HTML")
            
            # Потом показываем кнопки подписки
            await SubscriptionHandlers.show_subscription_upsell(
                message, user_id, reason="limits_exceeded"
            )
            
        except Exception as e:
            pass
    
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
            
            
        except Exception as e:
            pass
    
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
            logger.error(f"Ошибка проверки истечения подписок")

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
        logger.error(f"Ошибка увеличения счетчика upsell для пользователя")

async def should_show_upsell_for_message(user_id: int) -> bool:
    """Проверяет нужно ли показать upsell для сообщения"""
    try:
        has_gpt4o_limits = await check_gpt4o_limit(user_id)
        if not has_gpt4o_limits:
            return upsell_tracker.should_show_upsell(user_id)
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки upsell для пользователя")
        return False