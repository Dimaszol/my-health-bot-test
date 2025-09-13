# garmin_scheduler.py - ПРОСТАЯ ГИБРИДНАЯ ЛОГИКА

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

class GarminScheduler:
    """Планировщик для ежедневного сбора и анализа данных Garmin с простой гибридной логикой"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
        self.is_running = False
        
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            self.scheduler.add_job(
                func=self._check_users_for_analysis,
                trigger=CronTrigger(minute='*/10'),
                id='garmin_check_users',
                name='Проверка пользователей Garmin',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self._cleanup_old_data,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
                id='garmin_cleanup',
                name='Очистка старых данных Garmin',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Простой гибридный планировщик Garmin запущен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации планировщика Garmin: {e}")
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
            users_to_process = await self._get_users_ready_for_analysis(current_utc)
            
            if not users_to_process:
                return
            
            logger.info(f"📊 Найдено {len(users_to_process)} пользователей для анализа")
            
            semaphore = asyncio.Semaphore(3)
            tasks = [
                self._process_user_with_semaphore(semaphore, user)
                for user in users_to_process
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            error_count = sum(1 for r in results if isinstance(r, Exception))
            
            logger.info(f"✅ Обработано пользователей: {success_count}, ошибок: {error_count}")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в проверке пользователей: {e}")

    async def _process_user_with_semaphore(self, semaphore: asyncio.Semaphore, user: Dict) -> bool:
        """Обработать пользователя с семафором"""
        async with semaphore:
            return await self._process_user_analysis(user)

    async def _get_users_ready_for_analysis(self, current_utc: datetime) -> List[Dict]:
        """Получить пользователей готовых к анализу"""
        try:
            conn = await get_db_connection()
            
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
                AND gc.sync_errors < 5
                AND gah.analysis_date IS NULL
            """)
            
            await release_db_connection(conn)
            
            users_ready = []
            
            for row in rows:
                user_id = row['user_id']
                notification_time = row['notification_time']
                timezone_offset = row['timezone_offset']
                timezone_name = row['timezone_name']
                last_sync_date = row['last_sync_date']
                
                user_local_time = current_utc + timedelta(minutes=timezone_offset)
                
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
        """Проверить, пора ли делать анализ"""
        current_minutes = current_time.hour * 60 + current_time.minute
        notification_minutes = notification_time.hour * 60 + notification_time.minute
        
        return notification_minutes <= current_minutes < notification_minutes + 10

    async def _process_user_analysis(self, user: Dict) -> bool:
        """🔧 ПРОСТАЯ ГИБРИДНАЯ ЛОГИКА: Создаем одну запись за вчера с гибридными данными"""
        user_id = user['user_id']
        
        try:
            logger.info(f"🔄 Начинаю простой гибридный сбор для пользователя {user_id}")
            
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            logger.info(f"📅 ПРОСТАЯ ГИБРИДНАЯ ЛОГИКА:")
            logger.info(f"   🌙 Базовая дата: {yesterday} (все данные записываем сюда)")
            logger.info(f"   🏃 Активность: из данных за {yesterday}")
            logger.info(f"   😴 Сон: из данных за {today}")
            
            # Шаг 1: Получаем данные за вчера (активность)
            logger.info(f"📊 Получаю данные активности за {yesterday}...")
            yesterday_data = await garmin_connector.collect_daily_data(user_id, yesterday)
            
            # Шаг 2: Получаем данные за сегодня (только для сна)
            logger.info(f"😴 Получаю данные сна за {today}...")
            today_data = await garmin_connector.collect_daily_data(user_id, today)
            
            if not yesterday_data and not today_data:
                logger.error(f"❌ Не удалось получить данные ни за один день для {user_id}")
                return False
            
            # Шаг 3: Создаем гибридную запись
            hybrid_data = self._create_hybrid_record(yesterday_data, today_data, yesterday)
            
            # Шаг 4: Логируем результат
            self._log_hybrid_result(user_id, hybrid_data, yesterday, today)
            
            # Шаг 5: Сохраняем ТОЛЬКО гибридную запись
            logger.info(f"💾 Сохраняю гибридную запись за {yesterday}")
            saved = await garmin_connector.save_daily_data(hybrid_data)
            
            if not saved:
                logger.error(f"❌ Не удалось сохранить гибридную запись для {user_id}")
                return False
            
            logger.info(f"✅ Гибридная запись за {yesterday} сохранена успешно")
            
            # Продолжаем с анализом
            return await self._continue_with_analysis(user_id, yesterday, hybrid_data)
                
        except Exception as e:
            logger.error(f"❌ Ошибка простого гибридного анализа для пользователя {user_id}: {e}")
            return False

    def _create_hybrid_record(self, yesterday_data: Optional[Dict], today_data: Optional[Dict], base_date: date) -> Dict:
        """Создать гибридную запись: активность из вчера + сон из сегодня"""
        
        # Базируемся на данных за вчера (активность)
        if yesterday_data:
            result = yesterday_data.copy()
        else:
            # Если нет данных за вчера, создаем пустую структуру
            result = {
                'user_id': today_data.get('user_id') if today_data else None,
                'data_date': base_date,
                'steps': None,
                'calories': None,
                'distance_meters': None
            }
        
        # Перезаписываем ТОЛЬКО данные сна из сегодняшних данных
        if today_data:
            sleep_fields = [
                'sleep_duration_minutes', 'sleep_deep_minutes', 'sleep_light_minutes',
                'sleep_rem_minutes', 'sleep_awake_minutes', 'sleep_score',
                'nap_duration_minutes', 'sleep_need_minutes', 'sleep_baseline_minutes'
            ]
            
            for field in sleep_fields:
                if today_data.get(field) is not None:
                    result[field] = today_data[field]
        
        # Устанавливаем правильную дату и время синхронизации
        result['data_date'] = base_date
        result['sync_timestamp'] = datetime.now().isoformat()
        
        return result

    def _log_hybrid_result(self, user_id: int, hybrid_data: Dict, yesterday: date, today: date):
        """Логировать результат гибридного сбора"""
        
        logger.info(f"📋 РЕЗУЛЬТАТ ПРОСТОЙ ГИБРИДНОЙ ЛОГИКИ для пользователя {user_id}:")
        logger.info(f"   📅 Запись создана за: {hybrid_data.get('data_date')}")
        
        # Показываем откуда взяты данные
        if hybrid_data.get('steps'):
            logger.info(f"   🚶 ШАГИ: ✅ {hybrid_data['steps']} (из {yesterday})")
        else:
            logger.info(f"   🚶 ШАГИ: ❌ НЕТ ДАННЫХ (проверяли {yesterday})")
        
        if hybrid_data.get('sleep_duration_minutes'):
            sleep_hours = hybrid_data['sleep_duration_minutes'] // 60
            sleep_mins = hybrid_data['sleep_duration_minutes'] % 60
            logger.info(f"   😴 СОН: ✅ {sleep_hours}ч {sleep_mins}м (из {today})")
        else:
            logger.info(f"   😴 СОН: ❌ НЕТ ДАННЫХ (проверяли {today})")
        
        if hybrid_data.get('resting_heart_rate'):
            logger.info(f"   ❤️ ПУЛЬС: ✅ {hybrid_data['resting_heart_rate']} уд/мин")
        
        if hybrid_data.get('stress_avg'):
            logger.info(f"   😰 СТРЕСС: ✅ {hybrid_data['stress_avg']}")
        
        if hybrid_data.get('body_battery_max'):
            logger.info(f"   🔋 ЭНЕРГИЯ: ✅ {hybrid_data['body_battery_max']}%")
        
        # Подсчет успешности
        key_metrics = ['steps', 'sleep_duration_minutes', 'resting_heart_rate']
        available_metrics = sum(1 for metric in key_metrics if hybrid_data.get(metric))
        
        logger.info(f"   📊 КЛЮЧЕВЫХ МЕТРИК: {available_metrics}/{len(key_metrics)}")
        
        if available_metrics >= 2:
            logger.info(f"   🎉 ОТЛИЧНО: Гибридная логика работает успешно!")
        else:
            logger.info(f"   ⚠️ ПРОБЛЕМА: Недостаточно данных")

    async def _continue_with_analysis(self, user_id: int, analysis_date: date, data: Dict) -> bool:
        """Продолжить с AI анализом"""
        try:
            # Проверяем лимиты пользователя
            from subscription_manager import SubscriptionManager
            sub_manager = SubscriptionManager()
            
            user_limits = await sub_manager.get_user_limits(user_id)
            gpt4o_left = user_limits.get('gpt4o_queries_left', 0)
            
            if gpt4o_left <= 0:
                logger.info(f"⚠️ У пользователя {user_id} закончились консультации")
                await self._send_data_collected_notification(user_id)
                return True
            
            # Запускаем AI анализ
            logger.info(f"🧠 Запускаю AI анализ для пользователя {user_id} за {analysis_date}")
            
            analysis_result = await garmin_analyzer.create_health_analysis(user_id, data)
            
            if analysis_result:
                logger.info(f"✅ AI анализ завершен успешно для пользователя {user_id}")
                await self._send_analysis_notification(user_id, analysis_result)
                await sub_manager.spend_limits(user_id, queries=1)
                return True
            else:
                logger.error(f"❌ Не удалось создать AI анализ для {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка продолжения анализа: {e}")
            return False

    async def _send_data_collected_notification(self, user_id: int):
        """Отправить уведомление что данные собраны, но нужна подписка"""
        try:
            from locales import get_text
            message = get_text(user_id, "garmin_data_collected_reminder")
            await self.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
            logger.info(f"📤 Отправлено напоминание о лимитах пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")

    async def _send_analysis_notification(self, user_id: int, analysis_result: Dict):
        """Отправить результат анализа пользователю"""
        try:
            analysis_text = analysis_result.get('analysis_text', 'Анализ не удалось получить')
            if len(analysis_text) > 3500:
                analysis_text = analysis_text[:3500] + "...\n\n📊 Полный анализ сохранен в истории."
            
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🩺 <b>Ваш ежедневный анализ здоровья</b>\n\n{analysis_text}",
                parse_mode='HTML'
            )
            logger.info(f"📤 Отправлен анализ пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки анализа пользователю {user_id}: {e}")

    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            logger.info("🧹 Начинаю очистку старых данных Garmin")
            conn = await get_db_connection()
            
            cutoff_daily = date.today() - timedelta(days=90)
            cutoff_analysis = date.today() - timedelta(days=365)
            
            await conn.execute("DELETE FROM garmin_daily_data WHERE data_date < $1", cutoff_daily)
            await conn.execute("DELETE FROM garmin_analysis_history WHERE analysis_date < $1", cutoff_analysis)
            
            await release_db_connection(conn)
            logger.info(f"✅ Очистка завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых данных: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def force_user_analysis(self, user_id: int) -> bool:
        """Принудительно запустить анализ для пользователя"""
        try:
            logger.info(f"🔧 Принудительный запуск простого гибридного анализа для {user_id}")
            
            conn = await get_db_connection()
            row = await conn.fetchrow("""
                SELECT user_id, notification_time, timezone_offset, timezone_name, last_sync_date
                FROM garmin_connections 
                WHERE user_id = $1 AND is_active = TRUE
            """, user_id)
            await release_db_connection(conn)
            
            if not row:
                logger.warning(f"Пользователь {user_id} не найден или Garmin не подключен")
                return False
            
            user_data = {
                'user_id': row['user_id'],
                'notification_time': row['notification_time'], 
                'timezone_offset': row['timezone_offset'],
                'timezone_name': row['timezone_name'],
                'last_sync_date': row['last_sync_date'],
                'user_local_time': datetime.now()
            }
            
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
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                    COUNT(*) FILTER (WHERE sync_errors >= 5) as error_users,
                    COUNT(*) FILTER (WHERE last_sync_date = CURRENT_DATE) as synced_today
                FROM garmin_connections
            """)
            
            data_today = await conn.fetchval("SELECT COUNT(*) FROM garmin_daily_data WHERE sync_timestamp::date = CURRENT_DATE")
            analysis_today = await conn.fetchval("SELECT COUNT(*) FROM garmin_analysis_history WHERE analysis_date = CURRENT_DATE")
            
            await release_db_connection(conn)

            return {
                'is_running': self.is_running,
                'total_users': user_stats['total_users'] if user_stats else 0,
                'active_users': user_stats['active_users'] if user_stats else 0,
                'error_users': user_stats['error_users'] if user_stats else 0,
                'synced_today': user_stats['synced_today'] if user_stats else 0,
                'data_collected_today': data_today or 0,
                'analysis_completed_today': analysis_today or 0,
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

# Глобальный экземпляр
garmin_scheduler: Optional[GarminScheduler] = None

async def initialize_garmin_scheduler(bot: Bot):
    global garmin_scheduler
    try:
        garmin_scheduler = GarminScheduler(bot)
        await garmin_scheduler.initialize()
        logger.info("✅ Простая гибридная система Garmin запущена")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации планировщика Garmin: {e}")
        raise

async def shutdown_garmin_scheduler():
    global garmin_scheduler
    if garmin_scheduler:
        await garmin_scheduler.shutdown()
        logger.info("✅ Планировщик Garmin остановлен")

async def force_user_analysis(user_id: int) -> bool:
    global garmin_scheduler
    if garmin_scheduler:
        return await garmin_scheduler.force_user_analysis(user_id)
    return False

async def get_scheduler_status() -> Dict:
    global garmin_scheduler
    if garmin_scheduler:
        return await garmin_scheduler.get_scheduler_status()
    return {'error': 'Планировщик не инициализирован'}