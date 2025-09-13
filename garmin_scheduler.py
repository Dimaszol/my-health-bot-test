# garmin_scheduler.py - ИСПРАВЛЕННАЯ ГИБРИДНАЯ ЛОГИКА БЕЗ ДУБЛИРОВАНИЯ

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
    """Планировщик для ежедневного сбора и анализа данных Garmin с исправленной гибридной логикой"""
    
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
            
            logger.info("✅ Исправленный гибридный планировщик Garmin запущен")
            
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
        """Проверить, пора ли делать анализ (с окном в 10 минут)"""
        current_minutes = current_time.hour * 60 + current_time.minute
        notification_minutes = notification_time.hour * 60 + notification_time.minute
        
        return notification_minutes <= current_minutes < notification_minutes + 10

    async def _process_user_analysis(self, user: Dict) -> bool:
        """🔧 ИСПРАВЛЕННАЯ ГИБРИДНАЯ ЛОГИКА: Обновляем существующую запись"""
        user_id = user['user_id']
        
        try:
            logger.info(f"🔄 Начинаю исправленный гибридный сбор для пользователя {user_id}")
            
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            logger.info(f"📅 ИСПРАВЛЕННАЯ ГИБРИДНАЯ ЛОГИКА:")
            logger.info(f"   🌅 Сегодня: {today} (получаем ТОЛЬКО сон)")
            logger.info(f"   🌙 Вчера: {yesterday} (обновляем существующую запись)")
            
            # Шаг 1: Получаем данные сна за сегодня
            today_data = await garmin_connector.collect_daily_data(user_id, today)
            if not today_data:
                logger.warning(f"⚠️ Не удалось получить сегодняшние данные для {user_id}")
                return False
                
            logger.info(f"😴 Получил данные сна за {today}")
            
            # Шаг 2: Проверяем есть ли запись за вчера в БД
            yesterday_record = await self._get_existing_record(user_id, yesterday)
            
            if yesterday_record:
                logger.info(f"📝 Найдена существующая запись за {yesterday}, обновляю...")
                # Обновляем существующую запись
                success = await self._update_yesterday_with_sleep(user_id, yesterday, today_data)
            else:
                logger.info(f"📝 Записи за {yesterday} нет, создаю гибридную...")
                # Создаем новую гибридную запись 
                success = await self._create_hybrid_record(user_id, today, yesterday)
            
            if not success:
                logger.error(f"❌ Не удалось обновить/создать гибридную запись для {user_id}")
                return False
            
            # Шаг 3: УДАЛЯЕМ запись за сегодня если она существует (избегаем дублирования)
            await self._cleanup_today_record(user_id, today)
            
            logger.info(f"✅ Гибридное обновление завершено для пользователя {user_id}")
            
            # Остальная логика анализа...
            return await self._continue_with_analysis(user_id, yesterday)
                
        except Exception as e:
            logger.error(f"❌ Ошибка исправленного гибридного анализа для пользователя {user_id}: {e}")
            return False

    async def _get_existing_record(self, user_id: int, target_date: date) -> Optional[Dict]:
        """Получить существующую запись за определенную дату"""
        try:
            conn = await get_db_connection()
            
            row = await conn.fetchrow("""
                SELECT * FROM garmin_daily_data 
                WHERE user_id = $1 AND data_date = $2
            """, user_id, target_date)
            
            await release_db_connection(conn)
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения существующей записи: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return None

    async def _update_yesterday_with_sleep(self, user_id: int, yesterday: date, today_data: Dict) -> bool:
        """Обновить существующую запись за вчера данными сна из сегодня"""
        try:
            conn = await get_db_connection()
            
            # Извлекаем ТОЛЬКО поля сна из сегодняшних данных
            sleep_fields = {
                'sleep_duration_minutes': today_data.get('sleep_duration_minutes'),
                'sleep_deep_minutes': today_data.get('sleep_deep_minutes'),
                'sleep_light_minutes': today_data.get('sleep_light_minutes'),
                'sleep_rem_minutes': today_data.get('sleep_rem_minutes'),
                'sleep_awake_minutes': today_data.get('sleep_awake_minutes'),
                'sleep_score': today_data.get('sleep_score'),
                'nap_duration_minutes': today_data.get('nap_duration_minutes'),
                'sleep_need_minutes': today_data.get('sleep_need_minutes'),
                'sleep_baseline_minutes': today_data.get('sleep_baseline_minutes')
            }
            
            # Формируем SET часть запроса только для не-NULL значений
            set_parts = []
            params = []
            param_index = 1
            
            for field, value in sleep_fields.items():
                if value is not None:
                    set_parts.append(f"{field} = ${param_index}")
                    params.append(value)
                    param_index += 1
            
            if not set_parts:
                logger.warning(f"Нет данных сна для обновления записи за {yesterday}")
                return False
            
            # Добавляем обновление timestamp
            set_parts.append(f"sync_timestamp = ${param_index}")
            params.append(datetime.now())
            param_index += 1
            
            # Добавляем условия WHERE
            params.extend([user_id, yesterday])
            
            update_query = f"""
                UPDATE garmin_daily_data 
                SET {', '.join(set_parts)}
                WHERE user_id = ${param_index-1} AND data_date = ${param_index}
            """
            
            result = await conn.execute(update_query, *params)
            await release_db_connection(conn)
            
            logger.info(f"✅ Обновлена запись за {yesterday} данными сна из сегодня")
            logger.info(f"📊 Обновлены поля: {', '.join([f for f, v in sleep_fields.items() if v is not None])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления записи за вчера: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False

    async def _create_hybrid_record(self, user_id: int, today: date, yesterday: date) -> bool:
        """Создать новую гибридную запись если записи за вчера нет"""
        try:
            # Получаем данные за оба дня
            today_data = await garmin_connector.collect_daily_data(user_id, today)
            yesterday_data = await garmin_connector.collect_daily_data(user_id, yesterday)
            
            if not today_data and not yesterday_data:
                logger.error(f"Нет данных ни за один день для {user_id}")
                return False
            
            # Объединяем данные (приоритет активности - вчера, приоритет сна - сегодня)
            combined_data = self._merge_data_intelligently(yesterday_data, today_data, yesterday)
            
            # Сохраняем объединенную запись
            success = await garmin_connector.save_daily_data(combined_data)
            
            if success:
                logger.info(f"✅ Создана новая гибридная запись за {yesterday}")
                return True
            else:
                logger.error(f"❌ Не удалось сохранить гибридную запись")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания гибридной записи: {e}")
            return False

    def _merge_data_intelligently(self, yesterday_data: Optional[Dict], today_data: Optional[Dict], base_date: date) -> Dict:
        """Умно объединить данные приоритизируя активность из вчера и сон из сегодня"""
        
        # Базируемся на данных активности (вчера)
        if yesterday_data:
            result = yesterday_data.copy()
        else:
            result = {
                'user_id': today_data.get('user_id') if today_data else None,
                'data_date': base_date,
                'sync_timestamp': datetime.now()
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
        
        # Устанавливаем правильную дату
        result['data_date'] = base_date
        result['sync_timestamp'] = datetime.now()
        
        return result

    async def _cleanup_today_record(self, user_id: int, today: date):
        """Удалить запись за сегодня чтобы избежать дублирования"""
        try:
            conn = await get_db_connection()
            
            # Проверяем есть ли запись за сегодня
            existing = await conn.fetchrow("""
                SELECT id FROM garmin_daily_data 
                WHERE user_id = $1 AND data_date = $2
            """, user_id, today)
            
            if existing:
                # Удаляем запись за сегодня
                await conn.execute("""
                    DELETE FROM garmin_daily_data 
                    WHERE user_id = $1 AND data_date = $2
                """, user_id, today)
                
                logger.info(f"🗑️ Удалена дублирующая запись за {today} (избежали дублирования)")
            else:
                logger.debug(f"Записи за {today} нет, удаление не требуется")
            
            await release_db_connection(conn)
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления записи за сегодня: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def _continue_with_analysis(self, user_id: int, analysis_date: date) -> bool:
        """Продолжить с AI анализом после гибридного сбора"""
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
            
            # Получаем финальные данные для анализа
            final_data = await self._get_existing_record(user_id, analysis_date)
            if not final_data:
                logger.error(f"❌ Не найдена финальная запись для анализа за {analysis_date}")
                return False
            
            # Запускаем AI анализ
            logger.info(f"🧠 Запускаю AI анализ для пользователя {user_id} за {analysis_date}")
            
            analysis_result = await garmin_analyzer.create_health_analysis(user_id, final_data)
            
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
        """Отправить уведомление что данные собраны, но нужна подписка для анализа"""
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
            logger.info(f"🔧 Принудительный запуск исправленного гибридного анализа для {user_id}")
            
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
    """Инициализировать планировщик Garmin"""
    global garmin_scheduler
    try:
        garmin_scheduler = GarminScheduler(bot)
        await garmin_scheduler.initialize()
        logger.info("✅ Система исправленного гибридного планировщика Garmin запущена")
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