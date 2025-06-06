# user_state_manager.py - Создай этот файл в корне проекта

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UserStateManager:
    """
    Менеджер состояний пользователей с автоматической очисткой
    Исправляет утечку памяти из registration.py
    """
    
    def __init__(self, ttl_minutes: int = 60):
        self.states: Dict[int, Any] = {}
        self.timestamps: Dict[int, datetime] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cleanup_task = None
        logger.info(f"UserStateManager initialized with TTL={ttl_minutes} minutes")
    
    def set_state(self, user_id: int, state: Any):
        """Установить состояние пользователя"""
        self.states[user_id] = state
        self.timestamps[user_id] = datetime.now()
        logger.debug(f"State set for user {user_id}: {type(state).__name__}")
    
    def get_state(self, user_id: int) -> Optional[Any]:
        """Получить состояние пользователя"""
        if user_id in self.states:
            # Проверяем, не истекло ли время
            if datetime.now() - self.timestamps[user_id] > self.ttl:
                self.clear_state(user_id)
                logger.debug(f"State expired and cleared for user {user_id}")
                return None
            return self.states[user_id]
        return None
    
    def clear_state(self, user_id: int):
        """Очистить состояние пользователя"""
        self.states.pop(user_id, None)
        self.timestamps.pop(user_id, None)
        logger.debug(f"State manually cleared for user {user_id}")
    
    async def start_cleanup_loop(self):
        """Запустить автоматическую очистку"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("✅ User state cleanup loop started")
    
    async def stop_cleanup_loop(self):
        """Остановить автоматическую очистку"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
            logger.info("🛑 User state cleanup loop stopped")
    
    async def _cleanup_loop(self):
        """Цикл автоматической очистки каждые 5 минут"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 минут
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired(self):
        """Очистить истекшие состояния"""
        now = datetime.now()
        expired_users = [
            user_id for user_id, timestamp in self.timestamps.items()
            if now - timestamp > self.ttl
        ]
        
        for user_id in expired_users:
            self.clear_state(user_id)
        
        if expired_users:
            logger.info(f"🧹 Cleaned up {len(expired_users)} expired user states")
    
    def get_stats(self) -> Dict[str, int]:
        """Получить статистику для мониторинга"""
        return {
            "total_states": len(self.states),
            "active_timestamps": len(self.timestamps),
            "cleanup_running": self.cleanup_task is not None
        }

# ✅ ГЛОБАЛЬНЫЙ МЕНЕДЖЕР (заменяет user_states словарь)
user_state_manager = UserStateManager(ttl_minutes=60)

# ✅ ФУНКЦИИ-ОБЕРТКИ для совместимости с существующим кодом
def set_user_state(user_id: int, state: Any):
    """Установить состояние пользователя"""
    user_state_manager.set_state(user_id, state)

def get_user_state(user_id: int) -> Optional[Any]:
    """Получить состояние пользователя"""
    return user_state_manager.get_state(user_id)

def clear_user_state(user_id: int):
    """Очистить состояние пользователя"""
    user_state_manager.clear_state(user_id)

# ✅ СЛОВАРЬ ДЛЯ СОВМЕСТИМОСТИ (чтобы не ломать существующий код)
class StateDict:
    """Объект который ведет себя как словарь, но использует UserStateManager"""
    
    def __getitem__(self, user_id: int):
        return user_state_manager.get_state(user_id)
    
    def __setitem__(self, user_id: int, value: Any):
        user_state_manager.set_state(user_id, value)
    
    def get(self, user_id: int, default=None):
        state = user_state_manager.get_state(user_id)
        return state if state is not None else default
    
    def pop(self, user_id: int, default=None):
        state = user_state_manager.get_state(user_id)
        if state is not None:
            user_state_manager.clear_state(user_id)
            return state
        return default

# ✅ СОЗДАЕМ СОВМЕСТИМЫЙ ОБЪЕКТ
user_states = StateDict()