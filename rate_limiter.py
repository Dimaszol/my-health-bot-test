# rate_limiter.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с дневными лимитами

import time
import logging
import asyncio
import os
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from db_postgresql import t

logger = logging.getLogger(__name__)

def get_user_language_sync(user_id: int) -> str:
    """✅ ИСПРАВЛЕННАЯ синхронная версия для PostgreSQL"""
    try:
        import psycopg2
        
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            return "ru"
            
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else "ru"
    except Exception as e:
        logger.error(f"Ошибка получения языка для пользователя {user_id}: {e}")
        return "ru"  # Fallback

class RateLimiter:
    """
    ✅ Расширенная версия с дневными лимитами
    """
    
    def __init__(self):
        # Существующие хранилища (остаются как есть)
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.blocked_users: Dict[int, float] = {}
        self.user_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.locks_lock = asyncio.Lock()
        
        # ✅ НОВОЕ: Дневные счетчики
        self.daily_message_counts: Dict[int, Dict[str, int]] = defaultdict(dict)
        # Формат: {user_id: {"2025-07-03_message": 45, "2025-07-03_document": 2}}
        
        # Настройки лимитов
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
    
    def _get_today_key(self) -> str:
        """Получить ключ для сегодняшнего дня"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_daily_count(self, user_id: int, action_type: str) -> int:
        """Получить количество действий пользователя за сегодня"""
        today = self._get_today_key()
        user_daily = self.daily_message_counts.get(user_id, {})
        return user_daily.get(f"{today}_{action_type}", 0)
    
    def _increment_daily_count(self, user_id: int, action_type: str):
        """Увеличить счетчик действий за день"""
        today = self._get_today_key()
        if user_id not in self.daily_message_counts:
            self.daily_message_counts[user_id] = {}
        
        key = f"{today}_{action_type}"
        self.daily_message_counts[user_id][key] = self.daily_message_counts[user_id].get(key, 0) + 1
    
    async def is_blocked(self, user_id: int) -> Tuple[bool, int]:
        """Проверка блокировки (без изменений)"""
        current_time = time.time()
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            if user_id in self.blocked_users:
                unblock_time = self.blocked_users[user_id]
                if current_time < unblock_time:
                    remaining = int(unblock_time - current_time)
                    return True, remaining
                else:
                    del self.blocked_users[user_id]
                    
            return False, 0
    
    async def check_limit(self, user_id: int, action_type: str = "message") -> Tuple[bool, str]:
        """
        ✅ ОБНОВЛЕННАЯ версия с динамическими дневными лимитами на основе подписки
        """
        current_time = time.time()
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            # 1. Проверяем существующую блокировку
            if user_id in self.blocked_users:
                unblock_time = self.blocked_users[user_id]
                if current_time < unblock_time:
                    remaining = int(unblock_time - current_time)
                    lang = get_user_language_sync(user_id)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    time_str = f"{minutes} мин {seconds} сек" if minutes > 0 else f"{seconds} сек"
                    
                    try:
                        text = t("rate_limit_exceeded_time", lang, time_str=time_str)
                    except:
                        text = f"⏳ Попробуйте через {time_str}"
                    
                    return False, text
                else:
                    del self.blocked_users[user_id]
            
            # ✅ 2. НОВАЯ ПРОВЕРКА: Динамический дневной лимит на основе подписки
            daily_count = self._get_daily_count(user_id, action_type)
            daily_limit = await self._get_daily_limit_for_user(user_id, action_type)
            
            if daily_count >= daily_limit:
                lang = get_user_language_sync(user_id)
                
                # Получаем локализованное название действия
                try:
                    action_name_key = f"action_{action_type}s" if action_type != "message" else "action_messages"
                    action_name = t(action_name_key, lang)
                except:
                    # Fallback названия
                    action_names = {
                        "message": "сообщений",
                        "document": "документов", 
                        "image": "изображений",
                        "note": "заметок"
                    }
                    action_name = action_names.get(action_type, "запросов")
                
                # ✅ НОВОЕ: Проверяем тип подписки для разных сообщений
                subscription_type = await self._get_user_subscription_type(user_id)
                
                if subscription_type == 'subscription':
                    # Для подписчиков - обычное сообщение о лимите
                    try:
                        text = t("daily_limit_reached_premium", lang, 
                                daily_limit=daily_limit, action_name=action_name)
                    except:
                        text = f"📊 Дневной лимит {action_name}: {daily_limit}. Попробуйте завтра."
                else:
                    # Для бесплатных пользователей - с предложением подписки
                    try:
                        text = t("daily_limit_exceeded_free", lang, 
                                daily_limit=daily_limit, action_name=action_name)
                    except:
                        text = f"📊 Дневной лимит {action_name}: {daily_limit}. 💎 Оформите подписку для увеличения лимитов!"

                logger.warning(f"Daily limit exceeded for user {user_id}, action {action_type}: {daily_count}/{daily_limit}")
                return False, text
            
            # 3. Проверяем минутные лимиты (существующий код без изменений)
            if action_type not in self.limits:
                action_type = "message"
            
            limit_config = self.limits[action_type]
            window_start = current_time - limit_config["window"]
            
            # Очищаем старые запросы
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id] 
                if req_time > window_start
            ]
            
            # Проверяем минутный лимит
            request_count = len(self.user_requests[user_id])
            
            if request_count >= limit_config["count"]:
                # Блокируем пользователя
                self.blocked_users[user_id] = current_time + limit_config["cooldown"]
                
                lang = get_user_language_sync(user_id)
                
                # ✅ ЗАМЕНИЛИ: Получаем локализованное название действия через t()
                try:
                    if action_type == "message":
                        action_name = t("action_messages", lang)
                    elif action_type == "document":
                        action_name = t("action_documents", lang)
                    elif action_type == "image":
                        action_name = t("action_images", lang)
                    elif action_type == "note":
                        action_name = t("action_notes", lang)
                    else:
                        action_name = t("action_requests", lang)
                except:
                    # Fallback названия
                    action_names = {
                        "message": "сообщений",
                        "document": "документов",
                        "image": "изображений", 
                        "note": "заметок"
                    }
                    action_name = action_names.get(action_type, "запросов")
                
                cooldown_min = limit_config["cooldown"] // 60
                window_min = limit_config["window"] // 60
                
                try:
                    text = t("rate_limit_short", lang, 
                            count=limit_config['count'], 
                            action_name=action_name, 
                            window_min=window_min, 
                            cooldown_min=cooldown_min)
                except:
                    text = f"⏳ Лимит {action_name}: {limit_config['count']}/{window_min}мин. Подождите {cooldown_min}мин."

                logger.warning(f"Minute rate limit exceeded for user {user_id}, action {action_type}")
                return False, text

            return True, ""

    async def _get_daily_limit_for_user(self, user_id: int, action_type: str) -> int:
        """
        Получает дневной лимит для конкретного пользователя на основе его подписки
        """
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from subscription_manager import SubscriptionManager
            
            # Получаем информацию о подписке пользователя
            limits_info = await SubscriptionManager.get_user_limits(user_id)
            subscription_type = limits_info.get('subscription_type', 'free')
            
            # Определяем лимиты в зависимости от подписки
            if subscription_type == 'subscription':
                # Подписчики - щедрые лимиты
                subscription_limits = {
                    "message": 100,   # сообщений в день
                    "document": 40,   # документов в день  
                    "image": 10,      # изображений в день
                    "note": 10        # заметок в день
                }
            else:
                # Бесплатные пользователи - ограниченные лимиты
                subscription_limits = {
                    "message": 20,    # сообщений в день
                    "document": 5,    # документов в день
                    "image": 5,       # изображений в день
                    "note": 2         # заметок в день
                }
                
            return subscription_limits.get(action_type, 20)  # 20 по умолчанию
            
        except Exception as e:
            logger.error(f"Ошибка получения дневного лимита для пользователя {user_id}: {e}")
            # В случае ошибки возвращаем консервативный лимит
            return 20

    async def _get_user_subscription_type(self, user_id: int) -> str:
        """
        Получает тип подписки пользователя
        """
        try:
            from subscription_manager import SubscriptionManager
            limits_info = await SubscriptionManager.get_user_limits(user_id)
            return limits_info.get('subscription_type', 'free')
        except Exception as e:
            logger.error(f"Ошибка получения типа подписки для пользователя {user_id}: {e}")
            return 'free'
    
    async def record_request(self, user_id: int, action_type: str = "message"):
        """
        ✅ ОБНОВЛЕННАЯ версия записи запроса
        """
        current_time = time.time()
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            # Записываем для минутных лимитов
            self.user_requests[user_id].append(current_time)
            
            # ✅ НОВОЕ: Записываем для дневных лимитов
            self._increment_daily_count(user_id, action_type)
            
            logger.info(f"Request recorded: user {user_id}, action {action_type}")
    
    async def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """
        ✅ ИСПРАВЛЕННАЯ версия статистики с дневными счетчиками
        """
        current_time = time.time()
        hour_ago = current_time - 3600
        
        user_requests = self.user_requests.get(user_id, [])
        recent_requests = [req for req in user_requests if req > hour_ago]
        
        # Получаем дневные счетчики для всех типов действий
        action_types = ["message", "document", "image", "note"]
        daily_stats = {}
        
        for action_type in action_types:
            daily_count = self._get_daily_count(user_id, action_type)
            daily_limit = await self._get_daily_limit_for_user(user_id, action_type)
            daily_stats[f"daily_{action_type}"] = f"{daily_count}/{daily_limit}"
        
        return {
            "total_requests_last_hour": len(recent_requests),
            "is_blocked": user_id in self.blocked_users,
            "requests_in_memory": len(user_requests),
            **daily_stats
        }
    
    async def cleanup_old_data(self):
        """
        ✅ ОБНОВЛЕННАЯ версия очистки с удалением старых дневных данных
        """
        current_time = time.time()
        day_ago = current_time - 86400
        
        # Очищаем минутные данные (как раньше)
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
                    del self.user_requests[user_id]
                    async with self.locks_lock:
                        self.user_locks.pop(user_id, None)
        
        # ✅ НОВОЕ: Очищаем старые дневные данные (оставляем только последние 7 дней)
        today = datetime.now()
        cutoff_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        for user_id in list(self.daily_message_counts.keys()):
            user_daily = self.daily_message_counts[user_id]
            
            # Оставляем только последние 7 дней
            filtered_daily = {}
            for key, count in user_daily.items():
                if "_" in key:  # Формат "2025-07-03_message"
                    date_part = key.split("_")[0]
                    if date_part >= cutoff_date:
                        filtered_daily[key] = count
            
            if filtered_daily:
                self.daily_message_counts[user_id] = filtered_daily
            else:
                del self.daily_message_counts[user_id]
        
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

# ✅ ПУБЛИЧНЫЕ ФУНКЦИИ
async def check_rate_limit(user_id: int, action_type: str = "message") -> Tuple[bool, str]:
    """✅ ASYNC версия проверки лимитов"""
    return await rate_limiter.check_limit(user_id, action_type)

async def record_user_action(user_id: int, action_type: str = "message"):
    """✅ ASYNC версия записи действия"""
    await rate_limiter.record_request(user_id, action_type)

async def cleanup_rate_limiter():
    """Очищает старые данные rate limiter"""
    await rate_limiter.cleanup_old_data()

async def check_daily_limit(user_id: int, action_type: str = "message") -> Tuple[bool, int, int]:
    """
    ✅ ИСПРАВЛЕННАЯ версия проверки дневного лимита
    
    Returns:
        (можно_продолжить, текущий_счетчик, максимальный_лимит)
    """
    daily_count = rate_limiter._get_daily_count(user_id, action_type)
    daily_limit = await rate_limiter._get_daily_limit_for_user(user_id, action_type)
    
    return daily_count < daily_limit, daily_count, daily_limit

async def get_daily_stats(user_id: int) -> Dict[str, Dict[str, int]]:
    """
    ✅ ИСПРАВЛЕННАЯ версия получения дневной статистики
    
    Returns:
        {
            "message": {"used": 45, "limit": 100},
            "document": {"used": 2, "limit": 10},
            ...
        }
    """
    stats = {}
    action_types = ["message", "document", "image", "note"]
    
    for action_type in action_types:
        used = rate_limiter._get_daily_count(user_id, action_type)
        limit = await rate_limiter._get_daily_limit_for_user(user_id, action_type)
        stats[action_type] = {"used": used, "limit": limit}
    
    return stats

# ✅ ТОЛЬКО ДЛЯ ИНФОРМАЦИИ - ТЕСТЫ УДАЛЕНЫ
if __name__ == "__main__":
    print("🚦 Rate Limiter готов к работе!")
    print("📋 Возможности:")
    print("   • Минутные лимиты с блокировкой")
    print("   • Дневные лимиты на основе подписки")
    print("   • Автоочистка старых данных")
    print("   • Поддержка 4 типов действий: message, document, image, note")
    print("\n💡 Для тестирования создайте файл test_rate_limiter.py")