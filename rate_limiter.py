# rate_limiter.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с правильными async вызовами

import time
import logging
import asyncio
from typing import Dict, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

def get_user_language_sync(user_id: int) -> str:
    """Синхронная версия для rate limiter"""
    import sqlite3
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else "ru"
    except:
        return "ru"  # Fallback

# ЗАМЕНИ ВЕСЬ КЛАСС RateLimiter в rate_limiter.py на этот:

class RateLimiter:
    """
    ✅ ИСПРАВЛЕННАЯ версия без race conditions
    """
    
    def __init__(self):
        # Хранилище запросов
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.blocked_users: Dict[int, float] = {}
        
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Отдельный lock для каждого пользователя
        self.user_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.locks_lock = asyncio.Lock()  # Для безопасной работы с user_locks
        
        # Настройки лимитов (те же что были)
        self.limits = {
            "message": {"count": 10, "window": 60, "cooldown": 30},
            "document": {"count": 3, "window": 300, "cooldown": 120},
            "image": {"count": 3, "window": 600, "cooldown": 300},
            "note": {"count": 5, "window": 300, "cooldown": 60}
        }
    
    async def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """Получить lock для пользователя (thread-safe)"""
        async with self.locks_lock:
            if user_id not in self.user_locks:
                self.user_locks[user_id] = asyncio.Lock()
            return self.user_locks[user_id]
    
    async def is_blocked(self, user_id: int) -> Tuple[bool, int]:
        """
        ✅ ASYNC версия проверки блокировки
        """
        current_time = time.time()
        
        # Получаем lock для этого пользователя
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            if user_id in self.blocked_users:
                unblock_time = self.blocked_users[user_id]
                if current_time < unblock_time:
                    remaining = int(unblock_time - current_time)
                    return True, remaining
                else:
                    # Время блокировки истекло
                    del self.blocked_users[user_id]
                    
            return False, 0
    
    async def check_limit(self, user_id: int, action_type: str = "message") -> Tuple[bool, str]:
        """
        ✅ ИСПРАВЛЕННАЯ версия без race condition
        """
        current_time = time.time()
        
        # ✅ АТОМАРНАЯ ОПЕРАЦИЯ для каждого пользователя
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            # Проверяем блокировку
            if user_id in self.blocked_users:
                unblock_time = self.blocked_users[user_id]
                if current_time < unblock_time:
                    remaining = int(unblock_time - current_time)
                    lang = get_user_language_sync(user_id)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    time_str = f"{minutes} мин {seconds} сек" if minutes > 0 else f"{seconds} сек"
                    
                    messages = {
                        "ru": f"⏳ Превышен лимит запросов. Попробуйте через {time_str}",
                        "en": f"⏳ Rate limit exceeded. Try again in {time_str}",
                        "uk": f"⏳ Перевищено ліміт запитів. Спробуйте через {time_str}"
                    }
                    return False, messages.get(lang, messages["ru"])
                else:
                    del self.blocked_users[user_id]
            
            # Получаем настройки
            if action_type not in self.limits:
                action_type = "message"
            
            limit_config = self.limits[action_type]
            window_start = current_time - limit_config["window"]
            
            # Очищаем старые запросы
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id] 
                if req_time > window_start
            ]
            
            # Проверяем лимит
            request_count = len(self.user_requests[user_id])
            
            if request_count >= limit_config["count"]:
                # Блокируем пользователя
                self.blocked_users[user_id] = current_time + limit_config["cooldown"]
                
                lang = get_user_language_sync(user_id)
                
                action_names = {
                    "ru": {"message": "сообщений", "document": "документов", "image": "изображений", "note": "заметок"},
                    "en": {"message": "messages", "document": "documents", "image": "images", "note": "notes"},
                    "uk": {"message": "повідомлень", "document": "документів", "image": "зображень", "note": "нотаток"}
                }
                
                cooldown_min = limit_config["cooldown"] // 60
                window_min = limit_config["window"] // 60
                action_name = action_names.get(lang, action_names["ru"]).get(action_type, "запросов")
                
                messages = {
                    "ru": f"🚫 Превышен лимит: максимум {limit_config['count']} {action_name} за {window_min} мин. Попробуйте через {cooldown_min} мин.",
                    "en": f"🚫 Rate limit exceeded: max {limit_config['count']} {action_name} per {window_min} min. Try again in {cooldown_min} min.",
                    "uk": f"🚫 Перевищено ліміт: максимум {limit_config['count']} {action_name} за {window_min} хв. Спробуйте через {cooldown_min} хв."
                }
                
                logger.warning(f"Rate limit exceeded for user {user_id}, action {action_type}")
                return False, messages.get(lang, messages["ru"])
            
            return True, ""
    
    async def record_request(self, user_id: int, action_type: str = "message"):
        """
        ✅ ИСПРАВЛЕННАЯ версия записи запроса
        """
        current_time = time.time()
        
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            self.user_requests[user_id].append(current_time)
            logger.info(f"Request recorded: user {user_id}, action {action_type}")
    
    def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """
        Получает статистику пользователя (СИНХРОННАЯ - для простоты)
        """
        current_time = time.time()
        hour_ago = current_time - 3600
        
        user_requests = self.user_requests.get(user_id, [])
        recent_requests = [req for req in user_requests if req > hour_ago]
        
        return {
            "total_requests_last_hour": len(recent_requests),
            "is_blocked": user_id in self.blocked_users,
            "requests_in_memory": len(user_requests)
        }
    
    async def cleanup_old_data(self):
        """
        ✅ ASYNC версия очистки данных
        """
        current_time = time.time()
        day_ago = current_time - 86400
        
        # Очищаем по одному пользователю за раз
        users_to_process = list(self.user_requests.keys())
        
        for user_id in users_to_process:
            user_lock = await self._get_user_lock(user_id)
            
            async with user_lock:
                # Очищаем старые запросы
                recent_requests = [
                    req for req in self.user_requests[user_id] 
                    if req > day_ago
                ]
                
                if recent_requests:
                    self.user_requests[user_id] = recent_requests
                else:
                    # Удаляем пользователя без запросов
                    del self.user_requests[user_id]
                    # Также удаляем его lock
                    async with self.locks_lock:
                        self.user_locks.pop(user_id, None)
        
        # Очищаем истёкшие блокировки
        expired_blocks = [
            user_id for user_id, unblock_time in self.blocked_users.items()
            if current_time > unblock_time
        ]
        for user_id in expired_blocks:
            del self.blocked_users[user_id]
            
        logger.info(f"Cleanup completed: removed expired data")

# Создаём глобальный экземпляр
rate_limiter = RateLimiter()

async def check_rate_limit(user_id: int, action_type: str = "message") -> Tuple[bool, str]:
    """✅ ASYNC версия проверки лимитов"""
    return await rate_limiter.check_limit(user_id, action_type)

async def record_user_action(user_id: int, action_type: str = "message"):
    """✅ ASYNC версия записи действия"""
    await rate_limiter.record_request(user_id, action_type)

def get_rate_limit_stats(user_id: int) -> Dict[str, int]:
    """Получает статистику пользователя"""
    return rate_limiter.get_user_stats(user_id)

# Функция для периодической очистки (можно вызывать раз в час)
def cleanup_rate_limiter():
    """Очищает старые данные rate limiter"""
    rate_limiter.cleanup_old_data()

# Пример использования:
if __name__ == "__main__":
    # Тест rate limiter
    test_user = 123456
    
    print("🧪 Тестирование rate limiter...")
    
    # Тест обычных сообщений (лимит 15)
    for i in range(17):  # Больше лимита
        allowed, message = check_rate_limit(test_user, "message")
        if allowed:
            record_user_action(test_user, "message")
            print(f"✅ Сообщение {i+1}: разрешено")
        else:
            print(f"❌ Сообщение {i+1}: {message}")
            break
    
    # Показываем статистику
    stats = get_rate_limit_stats(test_user)
    print(f"\n📊 Статистика: {stats}")