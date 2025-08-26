# medication_notifications.py - Система уведомлений о приеме лекарств

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db_postgresql import get_db_connection, release_db_connection, get_user_language, t
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class MedicationNotificationSystem:
    """Система уведомлений о приеме лекарств"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        self.user_timezones: Dict[int, str] = {}  # Кэш часовых поясов
        
    async def initialize(self):
        """Инициализация системы"""
        try:
            # 1. Создаем таблицы если их нет
            await self._create_notification_tables()
            
            # 2. Загружаем настройки пользователей
            await self._load_user_timezones()
            
            # 3. Запускаем планировщик
            self.scheduler.start()
            
            # 4. Добавляем задачу проверки каждую минуту
            self.scheduler.add_job(
                self._check_medication_reminders,
                CronTrigger(minute='*'),  # Каждую минуту
                id='medication_check',
                replace_existing=True
            )
            
            logger.info("✅ Система уведомлений о лекарствах запущена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации системы уведомлений: {e}")
    
    async def _create_notification_tables(self):
        """Создание таблиц для уведомлений"""
        conn = await get_db_connection()
        try:
            await conn.execute("""
                -- Настройки уведомлений пользователей
                CREATE TABLE IF NOT EXISTS notification_settings (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                    notifications_enabled BOOLEAN DEFAULT TRUE,
                    timezone_offset INTEGER DEFAULT 0,  -- Смещение в минутах от UTC
                    timezone_name TEXT DEFAULT 'UTC',
                    last_timezone_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- История отправленных уведомлений (чтобы не спамить)
                CREATE TABLE IF NOT EXISTS notification_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    medication_name TEXT NOT NULL,
                    notification_time TIMESTAMP NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, medication_name, notification_time)
                );
                
                -- Индексы для производительности
                CREATE INDEX IF NOT EXISTS idx_notification_history_user_time 
                    ON notification_history(user_id, notification_time);
            """)
        finally:
            await release_db_connection(conn)
    
    async def _load_user_timezones(self):
        """Загрузка часовых поясов пользователей"""
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT user_id, timezone_offset, timezone_name 
                FROM notification_settings 
                WHERE notifications_enabled = TRUE
            """)
            
            for row in rows:
                self.user_timezones[row['user_id']] = {
                    'offset': row['timezone_offset'],
                    'name': row['timezone_name']
                }
                
        finally:
            await release_db_connection(conn)
    
    async def _check_medication_reminders(self):
        """Проверка и отправка напоминаний о лекарствах"""
        try:
            current_utc = datetime.now(timezone.utc)
            
            # Получаем пользователей с включенными уведомлениями
            conn = await get_db_connection()
            try:
                users = await conn.fetch("""
                    SELECT DISTINCT u.user_id, ns.timezone_offset, ns.timezone_name
                    FROM users u
                    JOIN notification_settings ns ON u.user_id = ns.user_id
                    JOIN medications m ON u.user_id = m.user_id
                    WHERE ns.notifications_enabled = TRUE
                """)
                
                for user in users:
                    await self._check_user_medications(
                        user['user_id'], 
                        user['timezone_offset'],
                        current_utc
                    )
                    
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки напоминаний: {e}")
    
    async def _check_user_medications(self, user_id: int, timezone_offset: int, current_utc: datetime):
        """Проверка лекарств конкретного пользователя"""
        try:
            # Вычисляем местное время пользователя
            user_local_time = current_utc + timedelta(minutes=timezone_offset)
            current_time_str = user_local_time.strftime("%H:%M")
            
            # Получаем лекарства пользователя на текущее время
            conn = await get_db_connection()
            try:
                medications = await conn.fetch("""
                    SELECT name, time, label 
                    FROM medications 
                    WHERE user_id = $1 AND time = $2
                """, user_id, current_time_str)
                
                if medications:
                    # Проверяем, не отправляли ли уже уведомление
                    today_start = user_local_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    notification_time = today_start.replace(
                        hour=int(current_time_str.split(':')[0]),
                        minute=int(current_time_str.split(':')[1])
                    )
                    
                    # Проверяем историю уведомлений
                    already_sent = await conn.fetchrow("""
                        SELECT id FROM notification_history 
                        WHERE user_id = $1 
                        AND notification_time = $2
                        AND DATE(sent_at) = CURRENT_DATE
                    """, user_id, notification_time)
                    
                    if not already_sent:
                        await self._send_medication_reminder(user_id, medications, notification_time)
                        
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки лекарств пользователя {user_id}: {e}")
    
    async def _send_medication_reminder(self, user_id: int, medications: list, notification_time: datetime):
        """Отправка напоминания о лекарствах"""
        try:
            lang = await get_user_language(user_id)
            
            # Формируем список лекарств
            med_list = []
            for med in medications:
                label = med['label'] if med['label'] else med['time']
                med_list.append(f"💊 {med['name']} ({label})")
            
            # Текст уведомления
            if len(medications) == 1:
                title = t("medication_reminder_single", lang)
            else:
                title = t("medication_reminder_multiple", lang)
            
            message_text = f"{title}\n\n" + "\n".join(med_list)
            
            # Кнопка для отключения уведомлений
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("turn_off_notifications", lang),
                    callback_data="turn_off_med_notifications"
                )]
            ])
            
            # Отправляем уведомление
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Записываем в историю
            await self._log_notification(user_id, medications, notification_time)
            
            logger.info(f"✅ Отправлено напоминание пользователю {user_id} о {len(medications)} лекарствах")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")
    
    async def _log_notification(self, user_id: int, medications: list, notification_time: datetime):
        """Логирование отправленного уведомления"""
        conn = await get_db_connection()
        try:
            for med in medications:
                await conn.execute("""
                    INSERT INTO notification_history (user_id, medication_name, notification_time)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, medication_name, notification_time) DO NOTHING
                """, user_id, med['name'], notification_time)
        finally:
            await release_db_connection(conn)
    
    async def set_user_timezone(self, user_id: int, timezone_offset: int, timezone_name: str = "Unknown"):
        """Установка часового пояса пользователя"""
        conn = await get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO notification_settings (user_id, timezone_offset, timezone_name, last_timezone_update)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET 
                    timezone_offset = EXCLUDED.timezone_offset,
                    timezone_name = EXCLUDED.timezone_name,
                    last_timezone_update = CURRENT_TIMESTAMP
            """, user_id, timezone_offset, timezone_name)
            
            # Обновляем кэш
            self.user_timezones[user_id] = {
                'offset': timezone_offset,
                'name': timezone_name
            }
            
        finally:
            await release_db_connection(conn)
    
    async def toggle_notifications(self, user_id: int) -> bool:
        """Переключение уведомлений пользователя"""
        conn = await get_db_connection()
        try:
            # Получаем текущее состояние
            current = await conn.fetchrow("""
                SELECT notifications_enabled FROM notification_settings WHERE user_id = $1
            """, user_id)
            
            if current:
                new_state = not current['notifications_enabled']
            else:
                new_state = True
            
            # Обновляем состояние
            await conn.execute("""
                INSERT INTO notification_settings (user_id, notifications_enabled)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET 
                    notifications_enabled = EXCLUDED.notifications_enabled
            """, user_id, new_state)
            
            return new_state
            
        finally:
            await release_db_connection(conn)
    
    async def get_notification_settings(self, user_id: int) -> Dict:
        """Получение настроек уведомлений пользователя"""
        conn = await get_db_connection()
        try:
            settings = await conn.fetchrow("""
                SELECT notifications_enabled, timezone_offset, timezone_name
                FROM notification_settings 
                WHERE user_id = $1
            """, user_id)
            
            if settings:
                return {
                    'enabled': settings['notifications_enabled'],
                    'timezone_offset': settings['timezone_offset'],
                    'timezone_name': settings['timezone_name']
                }
            else:
                return {
                    'enabled': False,
                    'timezone_offset': 0,
                    'timezone_name': 'UTC'
                }
                
        finally:
            await release_db_connection(conn)
    
    async def shutdown(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Система уведомлений остановлена")

# Глобальная переменная для системы уведомлений
notification_system: Optional[MedicationNotificationSystem] = None

async def initialize_medication_notifications(bot: Bot):
    """Инициализация системы уведомлений"""
    global notification_system
    notification_system = MedicationNotificationSystem(bot)
    await notification_system.initialize()

async def shutdown_medication_notifications():
    """Остановка системы уведомлений"""
    global notification_system
    if notification_system:
        await notification_system.shutdown()

# Вспомогательные функции для использования в обработчиках

async def toggle_user_medication_notifications(user_id: int) -> bool:
    """Переключить уведомления для пользователя"""
    global notification_system
    if notification_system:
        return await notification_system.toggle_notifications(user_id)
    return False

async def set_user_medication_timezone(user_id: int, offset_minutes: int, timezone_name: str = "Manual"):
    """Установить часовой пояс пользователя"""
    global notification_system
    if notification_system:
        await notification_system.set_user_timezone(user_id, offset_minutes, timezone_name)

async def get_user_notification_settings(user_id: int) -> Dict:
    """Получить настройки уведомлений пользователя"""
    global notification_system
    if notification_system:
        return await notification_system.get_notification_settings(user_id)
    return {'enabled': False, 'timezone_offset': 0, 'timezone_name': 'UTC'}