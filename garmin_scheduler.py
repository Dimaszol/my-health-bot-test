# garmin_scheduler.py - Планировщик для сбора и анализа данных Garmin

import asyncio
import logging
from datetime import datetime, date, timedelta, time as datetime_time
from typing import List, Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from garmin_connector import garmin_connector
from garmin_analyzer import garmin_analyzer
from db_postgresql import get_db_connection, release_db_connection
from aiogram import Bot

logger = logging.getLogger(__name__)

# ================================
# ОСНОВНОЙ КЛАСС ПЛАНИРОВЩИКА
# ================================

class GarminScheduler:
    """Планировщик для ежедневного сбора и анализа данных Garmin"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
        self.is_running = False
        
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            # Добавляем основную задачу - проверка пользователей каждые 10 минут
            self.scheduler.add_job(
                func=self._check_users_for_analysis,
                trigger=CronTrigger(minute='*/10'),  # Каждые 10 минут
                id='garmin_check_users',
                name='Проверка пользователей Garmin',
                replace_existing=True
            )
            
            # Добавляем задачу очистки старых данных (раз в неделю в воскресенье в 02:00)
            self.scheduler.add_job(
                func=self._cleanup_old_data,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),  # Воскресенье 2:00
                id='garmin_cleanup',
                name='Очистка старых данных Garmin',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Garmin планировщик запущен")
            logger.info("⏰ Проверка пользователей: каждые 10 минут")
            logger.info("🧹 Очистка данных: воскресенье 02:00")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Garmin планировщика: {e}")
            raise

    async def shutdown(self):
        """Остановка планировщика"""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("🛑 Garmin планировщик остановлен")

    async def _check_users_for_analysis(self):
        """Проверить всех пользователей и выполнить анализ если нужно"""
        try:
            current_utc = datetime.utcnow()
            logger.debug(f"🔄 Проверка пользователей Garmin в {current_utc}")
            
            # Получаем всех активных пользователей Garmin
            users_to_process = await self._get_users_ready_for_analysis(current_utc)
            
            if not users_to_process:
                logger.debug("😴 Нет пользователей готовых к анализу")
                return
            
            logger.info(f"📊 Найдено {len(users_to_process)} пользователей для анализа")
            
            # Обрабатываем пользователей параллельно, но с ограничением
            semaphore = asyncio.Semaphore(3)  # Максимум 3 одновременно
            
            tasks = [
                self._process_user_with_semaphore(semaphore, user)
                for user in users_to_process
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Подсчитываем результаты
            success_count = sum(1 for r in results if r is True)
            error_count = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(f"✅ Обработано пользователей: {success_count}, ошибок: {error_count}")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в проверке пользователей: {e}")

    async def _process_user_with_semaphore(self, semaphore: asyncio.Semaphore, user: Dict) -> bool:
        """Обработать пользователя с семафором для ограничения параллелизма"""
        async with semaphore:
            return await self._process_user_analysis(user)

    async def _get_users_ready_for_analysis(self, current_utc: datetime) -> List[Dict]:
        """Получить пользователей готовых к анализу"""
        try:
            conn = await get_db_connection()
            
            # Используем asyncpg API БЕЗ cursor
            rows = await conn.fetch("""
                SELECT 
                    gc.user_id,
                    gc.notification_time,
                    gc.timezone_offset,
                    gc.timezone_name,
                    gc.last_sync_date,
                    gah.analysis_date as last_analysis_date
                FROM garmin_connections gc
                LEFT JOIN garmin_analysis_history gah ON (
                    gc.user_id = gah.user_id 
                    AND gah.analysis_date = CURRENT_DATE
                )
                WHERE gc.is_active = TRUE
                AND gc.sync_errors < 5  -- Исключаем проблемных пользователей
                AND gah.analysis_date IS NULL  -- Анализ еще не был сегодня
            """)
            
            await release_db_connection(conn)
            
            users_ready = []
            
            for row in rows:
                user_id = row['user_id']
                notification_time = row['notification_time']
                timezone_offset = row['timezone_offset']
                timezone_name = row['timezone_name']
                last_sync_date = row['last_sync_date']
                last_analysis_date = row['last_analysis_date']
                
                # Вычисляем локальное время пользователя
                user_local_time = current_utc + timedelta(minutes=timezone_offset)
                
                # Проверяем, наступило ли время уведомления
                if self._is_time_for_analysis(user_local_time.time(), notification_time):
                    users_ready.append({
                        'user_id': user_id,
                        'notification_time': notification_time,
                        'timezone_offset': timezone_offset,
                        'timezone_name': timezone_name,
                        'last_sync_date': last_sync_date,
                        'user_local_time': user_local_time
                    })
            
            return users_ready
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователей для анализа: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return []

    def _is_time_for_analysis(self, current_time: datetime_time, notification_time: datetime_time) -> bool:
        """Проверить, пора ли делать анализ (с окном в 10 минут)"""
        # Преобразуем время в минуты для удобства сравнения
        current_minutes = current_time.hour * 60 + current_time.minute
        notification_minutes = notification_time.hour * 60 + notification_time.minute
        
        # Проверяем окно в 10 минут после времени уведомления
        return notification_minutes <= current_minutes < notification_minutes + 10

    async def _process_user_analysis(self, user: Dict) -> bool:
        """Выполнить полный цикл анализа для пользователя"""
        user_id = user['user_id']
        
        try:
            logger.info(f"🔄 Начинаю анализ для пользователя {user_id}")
            
            # Шаг 1: Собираем данные за вчерашний день
            target_date = date.today() - timedelta(days=1)
            daily_data = await garmin_connector.collect_daily_data(user_id, target_date)
            
            if not daily_data:
                logger.warning(f"⚠️ Не удалось собрать данные Garmin для {user_id}")
                return False
            
            # Шаг 2: Сохраняем данные в БД
            saved = await garmin_connector.save_daily_data(daily_data)
            if not saved:
                logger.error(f"❌ Не удалось сохранить данные для {user_id}")
                return False
            
            # Шаг 3: Проверяем лимиты пользователя
            from subscription_manager import SubscriptionManager
            
            limits = await SubscriptionManager.get_user_limits(user_id)
            has_consultations = limits.get('gpt4o_queries_left', 0) > 0
            
            if not has_consultations:
                logger.info(f"⏸️ У пользователя {user_id} нет лимитов для анализа")
                
                # Отправляем уведомление о необходимости подписки
                await self._send_subscription_reminder(user_id)
                return True  # Данные собрали, но анализ не делаем
            
            # Шаг 4: Выполняем AI анализ
            analysis_result = await garmin_analyzer.create_health_analysis(user_id, daily_data)
            
            if not analysis_result:
                logger.error(f"❌ Не удалось создать анализ для {user_id}")
                return False
            
            # Шаг 5: Отправляем анализ пользователю
            await self._send_analysis_to_user(user_id, analysis_result)
            
            # Шаг 6: Тратим лимит консультации
            await SubscriptionManager.spend_limits(user_id, queries=1)
            
            logger.info(f"✅ Анализ для пользователя {user_id} завершен успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа для пользователя {user_id}: {e}")
            
            # Увеличиваем счетчик ошибок
            await self._increment_user_errors(user_id)
            return False

    async def _send_analysis_to_user(self, user_id: int, analysis_result: Dict):
        """Отправить результат анализа пользователю"""
        try:
            from db_postgresql import get_user_language, t
            
            lang = await get_user_language(user_id)
            
            # Формируем красивое сообщение
            message_text = f"""🌅 <b>Ваш ежедневный анализ здоровья</b>

{analysis_result['analysis_text']}

📊 <b>Оценка здоровья:</b> {analysis_result.get('health_score', 'N/A')}/100

💡 <b>Рекомендации:</b>
{analysis_result.get('recommendations', 'Продолжайте следить за здоровьем!')}

📈 <b>Тренды:</b>
• 😴 Сон: {analysis_result.get('sleep_trend', 'стабильно')}
• 🏃 Активность: {analysis_result.get('activity_trend', 'стабильно')}
• 😰 Стресс: {analysis_result.get('stress_trend', 'стабильно')}

<i>Данные за {analysis_result.get('analysis_date', 'вчера')}</i>"""

            await self.bot.send_message(user_id, message_text, parse_mode="HTML")
            
            # Добавляем кнопки для дополнительных действий
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Показать данные", callback_data="garmin_show_data")],
                [InlineKeyboardButton(text="⚙️ Настройки Garmin", callback_data="garmin_menu")]
            ])
            
            await self.bot.send_message(
                user_id, 
                "Нужно что-то настроить?", 
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки анализа пользователю {user_id}: {e}")

    async def _send_subscription_reminder(self, user_id: int):
        """Напомнить пользователю о необходимости подписки"""
        try:
            from db_postgresql import get_user_language, t
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            lang = await get_user_language(user_id)
            
            text = """📊 <b>Данные Garmin собраны!</b>

⚠️ Для получения AI анализа нужны детальные консультации.

📈 <b>Собранные данные:</b>
• Сон, активность, пульс
• Body Battery и стресс  
• Готовы к анализу

💎 <b>Оформите подписку</b> для получения персональных рекомендаций каждое утро!"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Оформить подписку", callback_data="subscription")],
                [InlineKeyboardButton(text="📊 Посмотреть данные", callback_data="garmin_show_data")]
            ])

            await self.bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания о подписке {user_id}: {e}")

    async def _increment_user_errors(self, user_id: int):
        """Увеличить счетчик ошибок пользователя"""
        try:
            conn = await get_db_connection()
            
            await conn.execute("""
                UPDATE garmin_connections 
                SET sync_errors = sync_errors + 1, updated_at = NOW()
                WHERE user_id = $1
            """, user_id)
            
            await release_db_connection(conn)
            
        except Exception as e:
            logger.error(f"❌ Ошибка увеличения счетчика ошибок: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def _cleanup_old_data(self):
        """Очистка старых данных (старше 90 дней)"""
        try:
            logger.info("🧹 Начинаю очистку старых данных Garmin")
            
            cutoff_daily = date.today() - timedelta(days=90)
            cutoff_analysis = date.today() - timedelta(days=30)
            
            # 🔧 ИСПРАВЛЕНИЕ: Используем asyncpg
            conn = await get_db_connection()
            
            # Удаляем старые ежедневные данные
            result1 = await conn.execute("""
                DELETE FROM garmin_daily_data 
                WHERE data_date < $1
            """, cutoff_daily)
            
            # Удаляем старые анализы
            result2 = await conn.execute("""
                DELETE FROM garmin_analysis_history 
                WHERE analysis_date < $1
            """, cutoff_analysis)
            
            await release_db_connection(conn)

            logger.info(f"✅ Очистка завершена: удалено ежедневных данных, анализов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых данных: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def force_user_analysis(self, user_id: int) -> bool:
        """Принудительно запустить анализ для пользователя (для тестирования)"""
        try:
            logger.info(f"🔧 Принудительный запуск анализа для {user_id}")
            
            # 🔧 ИСПРАВЛЕНИЕ: Используем asyncpg подход
            conn = await get_db_connection()
            
            # 🔧 ИСПРАВЛЕНИЕ: fetchrow вместо execute + fetchone
            row = await conn.fetchrow("""
                SELECT user_id, notification_time, timezone_offset, timezone_name, last_sync_date
                FROM garmin_connections 
                WHERE user_id = $1 AND is_active = TRUE
            """, user_id)
            
            await release_db_connection(conn)
            
            if not row:
                logger.warning(f"Пользователь {user_id} не найден или Garmin не подключен")
                return False
            
            # 🔧 ИСПРАВЛЕНИЕ: Конвертируем asyncpg.Record в dict
            row = dict(row)
            
            user_data = {
                'user_id': row['user_id'],
                'notification_time': row['notification_time'], 
                'timezone_offset': row['timezone_offset'],
                'timezone_name': row['timezone_name'],
                'last_sync_date': row['last_sync_date'],
                'user_local_time': datetime.now()
            }
            
            # Запускаем анализ
            return await self._process_user_analysis(user_data)
            
        except Exception as e:
            logger.error(f"❌ Ошибка принудительного анализа: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False

    async def get_scheduler_status(self) -> Dict:
        """Получить статус планировщика"""
        try:
            conn = await get_db_connection()
            cursor = conn
            
            # Статистика пользователей
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                    COUNT(*) FILTER (WHERE sync_errors >= 5) as error_users,
                    COUNT(*) FILTER (WHERE last_sync_date = CURRENT_DATE) as synced_today
                FROM garmin_connections
            """)
            
            user_stats = cursor.fetchone()
            
            # Статистика данных за сегодня
            cursor.execute("""
                SELECT COUNT(*) FROM garmin_daily_data 
                WHERE sync_timestamp::date = CURRENT_DATE
            """)
            
            data_today = cursor.fetchone()[0]
            
            # Статистика анализов за сегодня
            cursor.execute("""
                SELECT COUNT(*) FROM garmin_analysis_history 
                WHERE analysis_date = CURRENT_DATE
            """)
            
            analysis_today = cursor.fetchone()[0]
            
            conn.close()
            await release_db_connection(conn)

            return {
                'is_running': self.is_running,
                'total_users': user_stats[0] if user_stats else 0,
                'active_users': user_stats[1] if user_stats else 0,
                'error_users': user_stats[2] if user_stats else 0,
                'synced_today': user_stats[3] if user_stats else 0,
                'data_collected_today': data_today,
                'analysis_completed_today': analysis_today,
                'next_check': self._get_next_job_time('garmin_check_users'),
                'next_cleanup': self._get_next_job_time('garmin_cleanup')
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса планировщика: {e}")
            return {'error': str(e)}

    def _get_next_job_time(self, job_id: str) -> Optional[str]:
        """Получить время следующего выполнения задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S UTC')
            return None
        except:
            return None

# ================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ================================

garmin_scheduler: Optional[GarminScheduler] = None

async def initialize_garmin_scheduler(bot: Bot):
    """Инициализировать планировщик Garmin"""
    global garmin_scheduler
    try:
        garmin_scheduler = GarminScheduler(bot)
        await garmin_scheduler.initialize()
        logger.info("✅ Система планировщика Garmin запущена")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации планировщика Garmin: {e}")
        raise

async def shutdown_garmin_scheduler():
    """Остановить планировщик Garmin"""
    global garmin_scheduler
    if garmin_scheduler:
        await garmin_scheduler.shutdown()
        logger.info("✅ Планировщик Garmin остановлен")

async def force_user_analysis(user_id: int) -> bool:
    """Принудительно запустить анализ для пользователя"""
    global garmin_scheduler
    if garmin_scheduler:
        return await garmin_scheduler.force_user_analysis(user_id)
    return False

async def get_scheduler_status() -> Dict:
    """Получить статус планировщика"""
    global garmin_scheduler
    if garmin_scheduler:
        return await garmin_scheduler.get_scheduler_status()
    return {'error': 'Планировщик не инициализирован'}