# cumulative_counter.py
"""
📊 Накопительный счетчик сообщений для промокодов

Отслеживает общее количество сообщений пользователя с момента регистрации.
Используется для показа промокодов на определенном сообщении (например, 30-м).
"""

import logging
from typing import Optional
from db_postgresql import execute_query, fetch_one

logger = logging.getLogger(__name__)

class CumulativeCounter:
    """Менеджер накопительного счетчика сообщений"""
    
    @staticmethod
    async def increment_message_count(user_id: int) -> int:
        """
        📈 Увеличивает накопительный счетчик сообщений пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Новое значение счетчика после увеличения
        """
        try:
            # Увеличиваем счетчик в БД атомарно
            await execute_query("""
                UPDATE users 
                SET total_messages_count = COALESCE(total_messages_count, 0) + 1 
                WHERE user_id = ?
            """, (user_id,))
            
            # Получаем новое значение
            result = await fetch_one("""
                SELECT total_messages_count FROM users WHERE user_id = ?
            """, (user_id,))
            
            if result:
                new_count = result[0] if isinstance(result, tuple) else result['total_messages_count']
                return new_count
            else:
                return 0
                
        except Exception as e:
            return 0
    
    @staticmethod
    async def get_message_count(user_id: int) -> int:
        """
        📊 Получает текущий накопительный счетчик сообщений
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Текущее значение счетчика (0 если пользователь не найден)
        """
        try:
            result = await fetch_one("""
                SELECT total_messages_count FROM users WHERE user_id = ?
            """, (user_id,))
            
            if result and result[0] is not None:
                count = result[0] if isinstance(result, tuple) else result['total_messages_count']
                return count
            else:
                return 0
                
        except Exception as e:
            return 0
    
    @staticmethod
    async def reset_message_count(user_id: int) -> bool:
        """
        🔄 Сбрасывает накопительный счетчик (обычно не используется)
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если сброс успешен, False в случае ошибки
        """
        try:
            await execute_query("""
                UPDATE users SET total_messages_count = 0 WHERE user_id = ?
            """, (user_id,))
            
            return True
            
        except Exception as e:
            return False
    
    @staticmethod
    async def init_counter_for_user(user_id: int) -> bool:
        """
        🔧 Инициализирует счетчик для пользователя (если еще не инициализирован)
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если инициализация успешна, False в случае ошибки
        """
        try:
            # Проверяем, есть ли уже значение
            current_count = await CumulativeCounter.get_message_count(user_id)
            
            if current_count == 0:
                # Инициализируем счетчик
                await execute_query("""
                    UPDATE users 
                    SET total_messages_count = 0 
                    WHERE user_id = ? AND total_messages_count IS NULL
                """, (user_id,))
              
            
            return True
            
        except Exception as e:
            return False
    
    @staticmethod
    async def get_users_by_message_count(target_count: int, limit: int = 100) -> list:
        """
        🔍 Находит пользователей с определенным количеством сообщений
        
        Полезно для аналитики - кто находится на пороге показа промокода
        
        Args:
            target_count: Целевое количество сообщений
            limit: Максимальное количество результатов
            
        Returns:
            Список user_id пользователей
        """
        try:
            from db_postgresql import fetch_all
            
            results = await fetch_all("""
                SELECT user_id, total_messages_count 
                FROM users 
                WHERE total_messages_count = ?
                ORDER BY user_id
                LIMIT ?
            """, (target_count, limit))
            
            user_ids = [row['user_id'] for row in results] if results else []
            
            return user_ids
            
        except Exception as e:
            return []

# 🔧 Функции для интеграции с main.py

async def increment_and_get_total_messages(user_id: int) -> int:
    """
    🎯 ГЛАВНАЯ ФУНКЦИЯ для интеграции в main.py
    
    Увеличивает счетчик и возвращает новое значение.
    Используется в обработчике сообщений для промокодов.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Новое значение накопительного счетчика
    """
    return await CumulativeCounter.increment_message_count(user_id)

async def get_total_messages(user_id: int) -> int:
    """
    📊 Получает текущий накопительный счетчик без увеличения
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Текущее значение накопительного счетчика
    """
    return await CumulativeCounter.get_message_count(user_id)