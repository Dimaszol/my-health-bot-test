# rate_limiter.py - ОБНОВЛЕННАЯ ВЕРСИЯ с дневными лимитами

import time
import logging
import asyncio
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

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
        # Формат: {user_id: {"2025-06-12": 45, "2025-06-11": 98}}
        
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
                    
                    messages = {
                        "ru": f"⏳ Превышен лимит запросов. Попробуйте через {time_str}",
                        "en": f"⏳ Rate limit exceeded. Try again in {time_str}",
                        "uk": f"⏳ Перевищено ліміт запитів. Спробуйте через {time_str}"
                    }
                    return False, messages.get(lang, messages["ru"])
                else:
                    del self.blocked_users[user_id]
            
            # ✅ 2. НОВАЯ ПРОВЕРКА: Динамический дневной лимит на основе подписки
            daily_count = self._get_daily_count(user_id, action_type)
            daily_limit = await self._get_daily_limit_for_user(user_id, action_type)
            
            if daily_count >= daily_limit:
                lang = get_user_language_sync(user_id)
                
                action_names = {
                    "ru": {
                        "message": "сообщений", 
                        "document": "документов", 
                        "image": "изображений", 
                        "note": "заметок"
                    },
                    "en": {
                        "message": "messages", 
                        "document": "documents", 
                        "image": "images", 
                        "note": "notes"
                    },
                    "uk": {
                        "message": "повідомлень", 
                        "document": "документів", 
                        "image": "зображень", 
                        "note": "нотаток"
                    }
                }
                
                action_name = action_names.get(lang, action_names["ru"]).get(action_type, "запросов")
                
                # ✅ НОВОЕ: Проверяем тип подписки для разных сообщений
                subscription_type = await self._get_user_subscription_type(user_id)
                
                if subscription_type == 'subscription':
                    # Для подписчиков - обычное сообщение о лимите
                    messages = {
                        "ru": f"😴 **Достигнут дневной лимит**\n\nВы использовали максимум: {daily_limit} {action_name} в день.\n\n🌅 Завтра в 00:00 лимиты обновятся!",
                        "en": f"😴 **Daily limit reached**\n\nYou've used the maximum: {daily_limit} {action_name} per day.\n\n🌅 Tomorrow at 00:00 limits will reset!",
                        "uk": f"😴 **Досягнуто денний ліміт**\n\nВи використали максимум: {daily_limit} {action_name} на день.\n\n🌅 Завтра о 00:00 ліміти оновляться!"
                    }
                else:
                    # Для бесплатных пользователей - с предложением подписки
                    messages = {
                        "ru": f"😴 **Дневной лимит исчерпан**\n\nВы достигли лимита: {daily_limit} {action_name} в день.\n\n🌅 Завтра в 00:00 я снова буду готов помочь!\n💎 Или оформите подписку для увеличения лимитов до 100 сообщений в день",
                        "en": f"😴 **Daily limit exceeded**\n\nYou've reached the limit: {daily_limit} {action_name} per day.\n\n🌅 Tomorrow at 00:00 I'll be ready to help again!\n💎 Or get a subscription to increase limits to 100 messages per day",
                        "uk": f"😴 **Денний ліміт вичерпано**\n\nВи досягли ліміту: {daily_limit} {action_name} на день.\n\n🌅 Завтра о 00:00 я знову буду готовий допомогти!\n💎 Або оформіть підписку для збільшення лімітів до 100 повідомлень на день"
                    }
                
                logger.warning(f"Daily limit exceeded for user {user_id}, action {action_type}: {daily_count}/{daily_limit}")
                return False, messages.get(lang, messages["ru"])
            
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
                
                logger.warning(f"Minute rate limit exceeded for user {user_id}, action {action_type}")
                return False, messages.get(lang, messages["ru"])
            
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
                    "message": 100,   # 100 сообщений в день
                    "document": 50,   # 50 документов в день  
                    "image": 50,      # 50 изображений в день
                    "note": 30        # 30 заметок в день
                }
            else:
                # Бесплатные пользователи - ограниченные лимиты
                subscription_limits = {
                    "message": 20,    # 20 сообщений в день
                    "document": 5,    # 5 документов в день
                    "image": 5,       # 5 изображений в день
                    "note": 2        # 2 заметок в день
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
    
    def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """
        ✅ ОБНОВЛЕННАЯ версия статистики с дневными счетчиками
        """
        current_time = time.time()
        hour_ago = current_time - 3600
        
        user_requests = self.user_requests.get(user_id, [])
        recent_requests = [req for req in user_requests if req > hour_ago]
        
        # Получаем дневные счетчики
        daily_stats = {}
        for action_type in self.daily_limits.keys():
            daily_count = self._get_daily_count(user_id, action_type)
            daily_limit = self.daily_limits[action_type]
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
                if "_" in key:  # Формат "2025-06-12_message"
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

# Создаём глобальный экземпляр (остается как есть)
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
async def cleanup_rate_limiter():
    """Очищает старые данные rate limiter"""
    await rate_limiter.cleanup_old_data()

# ✅ НОВАЯ ФУНКЦИЯ: Проверка дневного лимита отдельно
async def check_daily_limit(user_id: int, action_type: str = "message") -> Tuple[bool, int, int]:
    """
    Проверяет только дневной лимит без блокировки
    
    Returns:
        (можно_продолжить, текущий_счетчик, максимальный_лимит)
    """
    daily_count = rate_limiter._get_daily_count(user_id, action_type)
    daily_limit = rate_limiter.daily_limits.get(action_type, 100)
    
    return daily_count < daily_limit, daily_count, daily_limit

# ✅ НОВАЯ ФУНКЦИЯ: Получение дневной статистики
def get_daily_stats(user_id: int) -> Dict[str, Dict[str, int]]:
    """
    Получает дневную статистику пользователя
    
    Returns:
        {
            "message": {"used": 45, "limit": 100},
            "document": {"used": 2, "limit": 10},
            ...
        }
    """
    stats = {}
    for action_type, limit in rate_limiter.daily_limits.items():
        used = rate_limiter._get_daily_count(user_id, action_type)
        stats[action_type] = {"used": used, "limit": limit}
    
    return stats

# Пример использования и тестирования
if __name__ == "__main__":
    import asyncio
    
    async def test_daily_limits():
        """Тестирование дневных лимитов"""
        print("🧪 Тестирование дневных лимитов...")
        
        test_user = 123456
        
        # Тест: отправляем много сообщений
        print(f"📊 Тестируем лимит сообщений (100/день):")
        
        for i in range(105):  # Больше лимита
            allowed, message = await check_rate_limit(test_user, "message")
            if allowed:
                await record_user_action(test_user, "message")
                if i % 20 == 0:  # Показываем каждые 20 сообщений
                    can_continue, used, limit = await check_daily_limit(test_user, "message")
                    print(f"  Сообщение {i+1}: ✅ ({used}/{limit})")
            else:
                print(f"  Сообщение {i+1}: ❌ {message}")
                break
        
        # Показываем финальную статистику
        daily_stats = get_daily_stats(test_user)
        print(f"\n📈 Финальная статистика:")
        for action, stats in daily_stats.items():
            print(f"  {action}: {stats['used']}/{stats['limit']}")
        
        print("✅ Тест завершен!")

    # Запускаем тест
    # asyncio.run(test_daily_limits())