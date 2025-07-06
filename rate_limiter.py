# rate_limiter.py - УПРОЩЕННАЯ ПРАВИЛЬНАЯ ВЕРСИЯ

import time
import logging
import asyncio
import os
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from db_postgresql import t
from subscription_manager import SubscriptionManager

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
    ✅ УПРОЩЕННАЯ ПРАВИЛЬНАЯ ВЕРСИЯ:
    - Минутные лимиты ТОЛЬКО для сообщений (защита от спама GPT)
    - Остальные действия проверяются ТОЛЬКО по основным лимитам подписки
    """
    
    def __init__(self):
        # Существующие хранилища
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.blocked_users: Dict[int, float] = {}
        self.user_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.locks_lock = asyncio.Lock()
        
        # ✅ НОВОЕ: Дневные счетчики для основных лимитов
        self.daily_message_counts: Dict[int, Dict[str, int]] = defaultdict(dict)
        
        # ✅ УПРОЩЕНО: Минутные лимиты ТОЛЬКО для сообщений!
        self.message_limits = {
            "new_user": {
                "count": 15,       # 15 сообщений для новичков
                "window": 60,      # за 1 минуту
                "cooldown": 120    # блокировка на 2 минуты
            },
            "regular_user": {
                "count": 8,        # 8 сообщений для обычных
                "window": 60,      # за 1 минуту
                "cooldown": 180    # блокировка на 3 минуты
            }
        }
        
    async def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """Получить lock для пользователя (thread-safe)"""
        async with self.locks_lock:
            if user_id not in self.user_locks:
                self.user_locks[user_id] = asyncio.Lock()
            return self.user_locks[user_id]
    
    async def _is_new_user(self, user_id: int) -> bool:
        """
        🆕 Проверяет, является ли пользователь новым (зарегистрирован < 24 часов)
        """
        try:
            from db_postgresql import fetch_one
            
            result = await fetch_one("""
                SELECT created_at FROM users WHERE user_id = ?
            """, (user_id,))
            
            if not result:
                logger.info(f"👶 Пользователь {user_id} не найден в БД - считаем новым")
                return True
            
            created_at = result[0]
            
            # Обработка разных форматов даты
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    try:
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    except:
                        logger.warning(f"⚠️ Не удалось распарсить дату для пользователя {user_id}: {created_at}")
                        return True
            
            # Проверяем, прошло ли больше 24 часов
            now = datetime.now()
            if hasattr(created_at, 'replace') and created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)
            
            time_diff = now - created_at
            is_new = time_diff < timedelta(hours=24)
            
            if is_new:
                logger.info(f"👶 Пользователь {user_id} - новичок (создан {created_at}, прошло {time_diff})")
            else:
                logger.info(f"👨 Пользователь {user_id} - опытный (создан {created_at}, прошло {time_diff})")
            
            return is_new
            
        except Exception as e:
            logger.error(f"Ошибка проверки нового пользователя {user_id}: {e}")
            return True  # При ошибке считаем новым
    
    def _get_today_key(self) -> str:
        """Получить ключ для сегодняшнего дня"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_week_key(self) -> str:
        """Получить ключ для текущей недели (понедельник-воскресенье)"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        return monday.strftime("%Y-W%U")
    
    def _get_period_count(self, user_id: int, action_type: str) -> int:
        """Получить количество действий за период (день или неделю)"""
        subscription_type = self._get_subscription_type_sync(user_id)
        
        if subscription_type == 'subscription':
            # Подписчики - считаем по дням
            period_key = self._get_today_key()
        else:
            # Бесплатные - считаем по неделям
            period_key = self._get_week_key()
        
        user_data = self.daily_message_counts.get(user_id, {})
        return user_data.get(f"{period_key}_{action_type}", 0)

    def _increment_period_count(self, user_id: int, action_type: str):
        """Увеличить счетчик за период (день или неделю)"""
        subscription_type = self._get_subscription_type_sync(user_id)
        
        if user_id not in self.daily_message_counts:
            self.daily_message_counts[user_id] = {}
        
        if subscription_type == 'subscription':
            period_key = self._get_today_key()
        else:
            period_key = self._get_week_key()
        
        key = f"{period_key}_{action_type}"
        self.daily_message_counts[user_id][key] = self.daily_message_counts[user_id].get(key, 0) + 1

    def _get_subscription_type_sync(self, user_id: int) -> str:
        """Синхронная версия получения типа подписки"""
        try:
            import psycopg2
            DATABASE_URL = os.getenv("DATABASE_URL")
            if not DATABASE_URL:
                return "free"
                
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT subscription_type FROM user_limits WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else "free"
        except Exception as e:
            logger.error(f"Ошибка получения типа подписки для пользователя {user_id}: {e}")
            return "free"
    
    async def check_limit(self, user_id: int, action_type: str = "message") -> Tuple[bool, str]:
        """
        ✅ УПРОЩЕННАЯ ПРАВИЛЬНАЯ ЛОГИКА:
        - Для сообщений: минутные лимиты + основные лимиты
        - Для остального: ТОЛЬКО основные лимиты подписки
        """
        current_time = time.time()
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            # 1. Проверяем существующую блокировку (только для сообщений)
            if action_type == "message" and user_id in self.blocked_users:
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
            
            # 2. ✅ ОСНОВНЫЕ ЛИМИТЫ: Проверяем периодические лимиты (день/неделя)
            period_count = self._get_period_count(user_id, action_type)
            period_limit = await self._get_daily_limit_for_user(user_id, action_type)
            
            if period_count >= period_limit:
                lang = get_user_language_sync(user_id)
                subscription_type = self._get_subscription_type_sync(user_id)
                
                # Получаем локализованное название действия
                try:
                    action_name_key = f"action_{action_type}s" if action_type != "message" else "action_messages"
                    action_name = t(action_name_key, lang)
                except:
                    action_names = {
                        "message": "сообщений",
                        "document": "документов", 
                        "image": "изображений",
                        "note": "заметок",
                        "pills": "изменений лекарств"
                    }
                    action_name = action_names.get(action_type, "запросов")
                
                # Разные сообщения для дневных и недельных лимитов
                if subscription_type == 'subscription':
                    try:
                        text = t("daily_limit_reached_premium", lang, 
                                daily_limit=period_limit, action_name=action_name)
                    except:
                        text = f"📊 Дневной лимит {action_name}: {period_limit}. Попробуйте завтра."
                else:
                    try:
                        text = t("weekly_limit_exceeded_free", lang, 
                                weekly_limit=period_limit, action_name=action_name)
                    except:
                        text = f"📊 Недельный лимит {action_name}: {period_limit}. Обновится в понедельник."
                
                logger.warning(f"Period limit exceeded for user {user_id}, action {action_type}: {period_count}/{period_limit}")
                return False, text
            
            # 3. ✅ МИНУТНЫЕ ЛИМИТЫ: ТОЛЬКО для сообщений!
            if action_type == "message":
                is_new_user = await self._is_new_user(user_id)
                
                # Выбираем лимиты в зависимости от статуса пользователя
                if is_new_user:
                    limit_config = self.message_limits["new_user"]
                    logger.info(f"👶 Применяем льготные лимиты для нового пользователя {user_id}")
                else:
                    limit_config = self.message_limits["regular_user"]
                
                # Проверяем минутные лимиты для сообщений
                window_start = current_time - limit_config["window"]
                
                if user_id not in self.user_requests:
                    self.user_requests[user_id] = []
                    
                self.user_requests[user_id] = [
                    req_time for req_time in self.user_requests[user_id] 
                    if req_time > window_start
                ]
                
                request_count = len(self.user_requests[user_id])
                
                if request_count >= limit_config["count"]:
                    # Блокируем пользователя
                    self.blocked_users[user_id] = current_time + limit_config["cooldown"]
                    
                    lang = get_user_language_sync(user_id)
                    
                    try:
                        action_name = t("action_messages", lang)
                    except:
                        action_name = "сообщений"
                    
                    cooldown_min = limit_config["cooldown"] // 60
                    
                    # Сообщение для новых пользователей
                    if is_new_user:
                        try:
                            text = t("rate_limit_new_user", lang, 
                                    count=limit_config['count'], 
                                    action_name=action_name, 
                                    cooldown_min=cooldown_min)
                        except:
                            text = f"👶 Для новых пользователей: лимит {action_name} {limit_config['count']}. Подождите {cooldown_min} мин."
                    else:
                        try:
                            text = t("rate_limit_short", lang, 
                                    count=limit_config['count'], 
                                    action_name=action_name, 
                                    window_min=1, 
                                    cooldown_min=cooldown_min)
                        except:
                            text = f"⏳ Лимит {action_name}: {limit_config['count']}/мин. Подождите {cooldown_min}мин."

                    status = "новый" if is_new_user else "обычный"
                    logger.warning(f"Message rate limit exceeded for {status} user {user_id}")
                    return False, text

            # 4. ✅ ВСЕ ОСТАЛЬНЫЕ ДЕЙСТВИЯ: проходят без минутных проверок!
            # Документы, заметки, изображения проверяются только основными лимитами выше
            
            return True, ""

    async def _get_daily_limit_for_user(self, user_id: int, action_type: str) -> int:
        """
        Получает основные лимиты для пользователя (без изменений)
        """
        try:
            limits_info = await SubscriptionManager.get_user_limits(user_id)
            subscription_type = limits_info.get('subscription_type', 'free')
            
            if subscription_type == 'subscription':
                # Подписчики - ДНЕВНЫЕ лимиты
                subscription_limits = {                     
                    "message": 100,   # сообщений в день                     
                    "document": 40,   # документов в день                       
                    "image": 10,      # изображений в день                     
                    "note": 10,       # заметок в день
                    "pills": 10,      # изменений лекарств в день                
                    "summary": 15
                }             
            else:                 
                # Бесплатные пользователи - НЕДЕЛЬНЫЕ лимиты                 
                subscription_limits = {                     
                    "message": 50,    # сообщений в НЕДЕЛЮ                     
                    "document": 10,   # документов в НЕДЕЛЮ                     
                    "image": 15,      # изображений в НЕДЕЛЮ                     
                    "note": 5,        # заметок в НЕДЕЛЮ
                    "pills": 5,       # изменений лекарств в НЕДЕЛЮ               
                    "summary": 5
                }
                
            return subscription_limits.get(action_type, 20)
            
        except Exception as e:
            logger.error(f"Ошибка получения лимита для пользователя {user_id}: {e}")
            return 20
    
    async def record_request(self, user_id: int, action_type: str = "message"):
        """
        Записывает запрос пользователя
        """
        current_time = time.time()
        user_lock = await self._get_user_lock(user_id)
        
        async with user_lock:
            # Записываем для минутных лимитов (только сообщения)
            if action_type == "message":
                self.user_requests[user_id].append(current_time)
            
            # Записываем для периодических лимитов (все действия)
            self._increment_period_count(user_id, action_type)
            
            logger.info(f"Request recorded: user {user_id}, action {action_type}")
    
    def reset_user_counters(self, user_id: int):
        """🧹 ВРЕМЕННАЯ ФУНКЦИЯ: Сбросить счетчики пользователя"""
        if user_id in self.daily_message_counts:
            del self.daily_message_counts[user_id]
        if user_id in self.user_requests:
            del self.user_requests[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        logger.info(f"🧹 Счетчики пользователя {user_id} сброшены")
    
    async def cleanup_old_data(self):
        """Очистка старых данных"""
        current_time = time.time()
        day_ago = current_time - 86400
        
        # Очищаем минутные данные
        users_to_process = list(self.user_requests.keys())
        
        for user_id in users_to_process:
            user_lock = await self._get_user_lock(user_id)
            
            async with user_lock:
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
        
        # Очищаем старые дневные данные
        today = datetime.now()
        cutoff_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        for user_id in list(self.daily_message_counts.keys()):
            user_daily = self.daily_message_counts[user_id]
            
            filtered_daily = {}
            for key, count in user_daily.items():
                if "_" in key:
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

def reset_user_counters(user_id: int):
    """🧹 ВРЕМЕННАЯ ФУНКЦИЯ: Сбросить счетчики пользователя для отладки"""
    rate_limiter.reset_user_counters(user_id)

# ✅ СОВМЕСТИМОСТЬ: Оставляем старые функции
async def check_daily_limit(user_id: int, action_type: str = "message") -> Tuple[bool, int, int]:
    daily_count = rate_limiter._get_period_count(user_id, action_type)
    daily_limit = await rate_limiter._get_daily_limit_for_user(user_id, action_type)
    return daily_count < daily_limit, daily_count, daily_limit

async def get_daily_stats(user_id: int) -> Dict[str, Dict[str, int]]:
    stats = {}
    action_types = ["message", "document", "image", "note", "pills", "summary"]
    
    for action_type in action_types:
        used = rate_limiter._get_period_count(user_id, action_type)
        limit = await rate_limiter._get_daily_limit_for_user(user_id, action_type)
        stats[action_type] = {"used": used, "limit": limit}
    
    return stats

if __name__ == "__main__":
    print("🚦 Rate Limiter готов к работе!")
    print("📋 Правильная логика:")
    print("   • Минутные лимиты ТОЛЬКО для сообщений (защита от спама GPT)")
    print("   • Остальные действия - только основные лимиты подписки")
    print("   • Льготы для новых пользователей (24 часа)")
    print("   • Автоочистка старых данных")