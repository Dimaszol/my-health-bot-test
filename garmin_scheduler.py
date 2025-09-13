# garmin_scheduler.py - ГИБРИДНАЯ ЛОГИКА СБОРА ДАННЫХ

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
    """Планировщик для ежедневного сбора и анализа данных Garmin с гибридной логикой"""
    
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
                trigger=CronTrigger(minute='*/10'),
                id='garmin_check_users',
                name='Проверка пользователей Garmin',
                replace_existing=True
            )
            
            # Добавляем задачу очистки старых данных (раз в неделю в воскресенье в 02:00)
            self.scheduler.add_job(
                func=self._cleanup_old_data,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
                id='garmin_cleanup',
                name='Очистка старых данных Garmin',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Гибридный планировщик Garmin запущен")
            logger.info("⏰ Проверка пользователей: каждые 10 минут")
            logger.info("🧹 Очистка данных: воскресенье 02:00")
            
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
            logger.debug(f"🔄 Проверка пользователей Garmin в {current_utc}")
            
            users_to_process = await self._get_users_ready_for_analysis(current_utc)
            
            if not users_to_process:
                logger.debug("😴 Нет пользователей готовых к анализу")
                return
            
            logger.info(f"📊 Найдено {len(users_to_process)} пользователей для анализа")
            
            # Обрабатываем пользователей параллельно, но с ограничением
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
        """Обработать пользователя с семафором для ограничения параллелизма"""
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
        current_minutes = current_time.hour * 60 + current_time.minute
        notification_minutes = notification_time.hour * 60 + notification_time.minute
        
        return notification_minutes <= current_minutes < notification_minutes + 10

    async def _process_user_analysis(self, user: Dict) -> bool:
        """🔧 ГИБРИДНАЯ ЛОГИКА: Собираем разные данные за разные дни"""
        user_id = user['user_id']
        
        try:
            logger.info(f"🔄 Начинаю гибридный сбор данных для пользователя {user_id}")
            
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            logger.info(f"📅 ГИБРИДНАЯ ЛОГИКА СБОРА ДАННЫХ:")
            logger.info(f"   🌅 Сегодня: {today} (для сна)")
            logger.info(f"   🌙 Вчера: {yesterday} (для активности)")
            
            # 🔧 НОВЫЙ ПОДХОД: Собираем данные гибридно
            combined_data = await self._collect_hybrid_data(user_id, today, yesterday)
            
            if not combined_data:
                logger.warning(f"⚠️ Не удалось собрать гибридные данные для {user_id}")
                return False
            
            # 📊 ПОДРОБНЫЙ ЛОГ ГИБРИДНЫХ ДАННЫХ
            await self._log_hybrid_data_summary(user_id, combined_data, today, yesterday)
            
            # Сохраняем объединенные данные в БД
            logger.info(f"💾 Сохраняю гибридные данные в БД для пользователя {user_id}")
            saved = await garmin_connector.save_daily_data(combined_data)
            if not saved:
                logger.error(f"❌ Не удалось сохранить данные для {user_id}")
                return False
            
            logger.info(f"✅ Гибридные данные сохранены для пользователя {user_id}")
            
            # Проверяем лимиты пользователя
            logger.info(f"🔍 Проверяю лимиты консультаций для пользователя {user_id}")
            from subscription_manager import SubscriptionManager
            sub_manager = SubscriptionManager()
            
            user_limits = await sub_manager.get_user_limits(user_id)
            gpt4o_left = user_limits.get('gpt4o_queries_left', 0)
            logger.info(f"💎 У пользователя {user_id} осталось консультаций: {gpt4o_left}")
            
            if gpt4o_left <= 0:
                logger.info(f"⚠️ У пользователя {user_id} закончились детальные консультации")
                await self._send_data_collected_notification(user_id)
                return True
            
            # Запускаем AI анализ с использованием вчерашней даты для анализа
            # (потому что основная активность была вчера)
            logger.info(f"🧠 Запускаю AI анализ для пользователя {user_id}")
            logger.info(f"📅 Дата для анализа: {yesterday} (базовая дата)")
            
            analysis_result = await garmin_analyzer.create_health_analysis(user_id, combined_data)
            
            if analysis_result:
                logger.info(f"✅ AI анализ для пользователя {user_id} завершен успешно")
                logger.info(f"📄 Длина анализа: {len(analysis_result.get('analysis_text', ''))} символов")
                
                await self._send_analysis_notification(user_id, analysis_result)
                await sub_manager.spend_limits(user_id, queries=1)
                return True
            else:
                logger.error(f"❌ Не удалось создать AI анализ для {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка гибридного анализа для пользователя {user_id}: {e}")
            logger.exception("Полная трассировка ошибки:")
            return False

    async def _collect_hybrid_data(self, user_id: int, today: date, yesterday: date) -> Optional[Dict]:
        """🔧 КЛЮЧЕВАЯ ФУНКЦИЯ: Собираем данные гибридно"""
        
        logger.info(f"🔧 ГИБРИДНЫЙ СБОР для пользователя {user_id}:")
        
        # Шаг 1: Собираем данные сна за СЕГОДНЯ
        logger.info(f"   😴 Собираю данные сна за {today}...")
        sleep_data = await garmin_connector.collect_daily_data(user_id, today)
        
        # Шаг 2: Собираем данные активности за ВЧЕРА  
        logger.info(f"   🏃 Собираю данные активности за {yesterday}...")
        activity_data = await garmin_connector.collect_daily_data(user_id, yesterday)
        
        if not sleep_data and not activity_data:
            logger.error(f"   ❌ Не удалось собрать никаких данных")
            return None
        
        # Шаг 3: Объединяем данные умно
        logger.info(f"   🔄 Объединяю данные...")
        combined_data = self._merge_hybrid_data(sleep_data, activity_data, yesterday)
        
        return combined_data

    def _merge_hybrid_data(self, sleep_data: Optional[Dict], activity_data: Optional[Dict], base_date: date) -> Dict:
        """Объединить данные сна и активности"""
        
        # Базируемся на данных активности (вчера)
        if activity_data:
            result = activity_data.copy()
        else:
            result = {
                'user_id': sleep_data.get('user_id') if sleep_data else None,
                'data_date': base_date,
                'sync_timestamp': datetime.now()
            }
        
        # Перезаписываем ТОЛЬКО данные сна из сегодняшних данных
        if sleep_data:
            sleep_fields = [
                'sleep_duration_minutes',
                'sleep_deep_minutes', 
                'sleep_light_minutes',
                'sleep_rem_minutes',
                'sleep_awake_minutes',
                'sleep_score',
                'nap_duration_minutes',
                'sleep_need_minutes',
                'sleep_baseline_minutes'
            ]
            
            for field in sleep_fields:
                if sleep_data.get(field) is not None:
                    result[field] = sleep_data[field]
                    logger.debug(f"     ✅ Взял {field} из сегодняшних данных")
        
        # Убеждаемся что дата правильная (базовая дата = вчера)
        result['data_date'] = base_date
        
        return result

    async def _log_hybrid_data_summary(self, user_id: int, combined_data: Dict, today: date, yesterday: date):
        """Подробно логировать результат гибридного сбора"""
        
        logger.info(f"📊 РЕЗУЛЬТАТ ГИБРИДНОГО СБОРА для пользователя {user_id}:")
        logger.info(f"   📅 Базовая дата записи: {combined_data.get('data_date')}")
        
        # Анализ сна (должен быть из сегодняшних данных)
        if combined_data.get('sleep_duration_minutes'):
            sleep_hours = combined_data['sleep_duration_minutes'] // 60
            sleep_mins = combined_data['sleep_duration_minutes'] % 60
            logger.info(f"   😴 ОСНОВНОЙ СОН: ✅ {sleep_hours}ч {sleep_mins}м (из данных за {today})")
        else:
            logger.info(f"   😴 ОСНОВНОЙ СОН: ❌ НЕТ (проверяли {today})")
        
        if combined_data.get('nap_duration_minutes'):
            logger.info(f"   🛌 Дневной сон: ✅ {combined_data['nap_duration_minutes']}м")
        
        # Анализ активности (должна быть из вчерашних данных)
        if combined_data.get('steps'):
            logger.info(f"   🚶 ШАГИ: ✅ {combined_data['steps']} (из данных за {yesterday})")
        else:
            logger.info(f"   🚶 ШАГИ: ❌ НЕТ (проверяли {yesterday})")
        
        # Остальные показатели
        if combined_data.get('resting_heart_rate'):
            logger.info(f"   ❤️ Пульс: ✅ {combined_data['resting_heart_rate']} уд/мин")
        
        if combined_data.get('stress_avg'):
            logger.info(f"   😰 Стресс: ✅ среднее {combined_data['stress_avg']}")
        
        if combined_data.get('body_battery_max'):
            logger.info(f"   🔋 Body Battery: ✅ {combined_data.get('body_battery_min', '?')}-{combined_data['body_battery_max']}%")
        
        # Подсчет метрик
        metrics = []
        if combined_data.get('sleep_duration_minutes'): metrics.append('сон')
        if combined_data.get('steps'): metrics.append('шаги')
        if combined_data.get('resting_heart_rate'): metrics.append('пульс')
        if combined_data.get('stress_avg'): metrics.append('стресс')
        if combined_data.get('body_battery_max'): metrics.append('энергия')
        
        logger.info(f"   ✅ СОБРАНО МЕТРИК: {len(metrics)} ({', '.join(metrics)})")
        
        # Диагноз качества
        if len(metrics) >= 4:
            logger.info(f"   🎉 ОТЛИЧНО: Гибридный сбор работает идеально!")
        elif len(metrics) >= 2:
            logger.info(f"   👍 ХОРОШО: Основные данные собраны")
        else:
            logger.info(f"   ⚠️ ПРОБЛЕМА: Мало данных, проверить настройки")

    async def _send_data_collected_notification(self, user_id: int):
        """Отправить уведомление что данные собраны, но нужна подписка для анализа"""
        try:
            from locales import get_text
            
            message = get_text(user_id, "garmin_data_collected_reminder")
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"📤 Отправлено напоминание о лимитах пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")

    async def _send_analysis_notification(self, user_id: int, analysis_result: Dict):
        """Отправить результат анализа пользователю"""
        try:
            analysis_text = analysis_result.get('analysis_text', 'Анализ не удалось получить')
            
            # Ограничиваем длину сообщения
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
        """Очистка старых данных (запускается раз в неделю)"""
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
            logger.info(f"🔧 Принудительный запуск гибридного анализа для {user_id}")
            
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
            
            row = dict(row)
            
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
            
            data_today = await conn.fetchval("""
                SELECT COUNT(*) FROM garmin_daily_data 
                WHERE sync_timestamp::date = CURRENT_DATE
            """)
            
            analysis_today = await conn.fetchval("""
                SELECT COUNT(*) FROM garmin_analysis_history 
                WHERE analysis_date = CURRENT_DATE
            """)
            
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
        logger.info("✅ Система гибридного планировщика Garmin запущена")
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