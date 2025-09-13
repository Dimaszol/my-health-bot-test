# garmin_scheduler.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с подробными логами

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
        """🔧 ИСПРАВЛЕННАЯ ФУНКЦИЯ: Выполнить полный цикл анализа для пользователя"""
        user_id = user['user_id']
        
        try:
            logger.info(f"🔄 Начинаю анализ для пользователя {user_id}")
            
            # 🔧 ГЛАВНОЕ ИСПРАВЛЕНИЕ: Собираем данные за СЕГОДНЯШНИЙ день
            # Потому что Garmin записывает сон в день пробуждения, а не засыпания
            old_target_date = date.today() - timedelta(days=1)  # Старая логика
            new_target_date = date.today()  # НОВАЯ ЛОГИКА
            
            logger.info(f"📅 ИЗМЕНЕНИЕ ЛОГИКИ для пользователя {user_id}:")
            logger.info(f"   • Старая дата: {old_target_date} (запрашивали вчера)")
            logger.info(f"   • Новая дата: {new_target_date} (запрашиваем сегодня)")
            logger.info(f"   • Причина: Garmin записывает сон в день пробуждения")
            
            # Используем НОВУЮ логику
            target_date = new_target_date
            
            logger.info(f"🔍 Собираю данные Garmin за {target_date} для пользователя {user_id}")
            
            daily_data = await garmin_connector.collect_daily_data(user_id, target_date)
            
            if not daily_data:
                logger.warning(f"⚠️ Не удалось собрать данные Garmin для {user_id} за {target_date}")
                return False
            
            # 📊 ПОДРОБНЫЙ ЛОГ СОБРАННЫХ ДАННЫХ (временно для отладки)
            logger.info(f"📊 СОБРАННЫЕ ДАННЫЕ для пользователя {user_id}:")
            
            # Основные показатели
            if daily_data.get('steps'):
                logger.info(f"   🚶 Шаги: {daily_data['steps']}")
            else:
                logger.info(f"   🚶 Шаги: ❌ НЕТ ДАННЫХ")
            
            # Анализ сна - ключевой показатель
            if daily_data.get('sleep_duration_minutes'):
                sleep_hours = daily_data['sleep_duration_minutes'] // 60
                sleep_mins = daily_data['sleep_duration_minutes'] % 60
                logger.info(f"   😴 ОСНОВНОЙ СОН: ✅ {sleep_hours}ч {sleep_mins}м")
            else:
                logger.info(f"   😴 ОСНОВНОЙ СОН: ❌ НЕТ ДАННЫХ")
            
            if daily_data.get('nap_duration_minutes'):
                logger.info(f"   🛌 Дневной сон: ✅ {daily_data['nap_duration_minutes']}м")
            else:
                logger.info(f"   🛌 Дневной сон: ❌ нет")
            
            # Остальные показатели
            if daily_data.get('resting_heart_rate'):
                logger.info(f"   ❤️ Пульс покоя: ✅ {daily_data['resting_heart_rate']} уд/мин")
            else:
                logger.info(f"   ❤️ Пульс покоя: ❌ НЕТ ДАННЫХ")
            
            if daily_data.get('stress_avg'):
                logger.info(f"   😰 Средний стресс: ✅ {daily_data['stress_avg']}")
            else:
                logger.info(f"   😰 Средний стресс: ❌ НЕТ ДАННЫХ")
            
            if daily_data.get('body_battery_max'):
                logger.info(f"   🔋 Body Battery макс: ✅ {daily_data['body_battery_max']}%")
            else:
                logger.info(f"   🔋 Body Battery: ❌ НЕТ ДАННЫХ")
            
            # Качество данных
            completeness = daily_data.get('data_completeness_score', 0)
            logger.info(f"   📈 Полнота данных: {completeness:.1f}%")
            
            # Подсчет собранных показателей
            collected_metrics = []
            if daily_data.get('steps'): collected_metrics.append('шаги')
            if daily_data.get('sleep_duration_minutes'): collected_metrics.append('основной_сон')
            if daily_data.get('nap_duration_minutes'): collected_metrics.append('дневной_сон')
            if daily_data.get('resting_heart_rate'): collected_metrics.append('пульс')
            if daily_data.get('stress_avg'): collected_metrics.append('стресс')
            if daily_data.get('body_battery_max'): collected_metrics.append('энергия')
            
            logger.info(f"   ✅ Собрано показателей: {len(collected_metrics)}")
            logger.info(f"   📋 Показатели: {', '.join(collected_metrics)}")
            
            # Диагноз качества сбора данных
            if not daily_data.get('sleep_duration_minutes') and daily_data.get('nap_duration_minutes'):
                logger.info(f"   🔍 ДИАГНОЗ: Есть дневной сон, НЕТ основного сна")
                logger.info(f"   💡 ВЕРОЯТНАЯ ПРИЧИНА: Основной сон записан в другой день")
                logger.info(f"   ✅ РЕШЕНИЕ ПРИМЕНЕНО: Используем date.today() вместо вчерашнего дня")
            
            # Шаг 2: Сохраняем данные в БД
            logger.info(f"💾 Сохраняю данные в БД для пользователя {user_id}")
            saved = await garmin_connector.save_daily_data(daily_data)
            if not saved:
                logger.error(f"❌ Не удалось сохранить данные для {user_id}")
                return False
            
            logger.info(f"✅ Данные сохранены в БД для пользователя {user_id}")
            
            # Шаг 3: Проверяем лимиты пользователя
            logger.info(f"🔍 Проверяю лимиты консультаций для пользователя {user_id}")
            from subscription_manager import SubscriptionManager
            sub_manager = SubscriptionManager()

            # ИСПРАВЛЕНО: используем правильный метод
            user_limits = await sub_manager.get_user_limits(user_id)
            gpt4o_left = user_limits.get('gpt4o_queries_left', 0)

            logger.info(f"💎 У пользователя {user_id} осталось консультаций: {gpt4o_left}")

            if gpt4o_left <= 0:
                logger.info(f"⚠️ У пользователя {user_id} закончились детальные консультации")
                logger.info(f"📊 Данные собраны успешно, но AI анализ недоступен")
                
                # Отправляем уведомление о том, что данные собраны, но анализ недоступен
                await self._send_data_collected_notification(user_id)
                return True  # Данные собрали успешно, просто без анализа

            # Шаг 4: Запускаем AI анализ
            logger.info(f"🧠 Запускаю AI анализ для пользователя {user_id}")
            logger.info(f"📅 Дата для анализа: {target_date}")

            analysis_result = await garmin_analyzer.create_health_analysis(
                analysis_result = await garmin_analyzer.create_health_analysis(user_id, daily_data)
            )

            if analysis_result:
                logger.info(f"✅ AI анализ для пользователя {user_id} завершен успешно")
                logger.info(f"📄 Длина анализа: {len(analysis_result.get('analysis_text', ''))} символов")
                
                # Отправляем анализ пользователю
                await self._send_analysis_notification(user_id, analysis_result)
                
                # ИСПРАВЛЕНО: Списываем лимит правильным методом
                await sub_manager.spend_limits(user_id, queries=1)
                
                return True
            else:
                logger.error(f"❌ Не удалось создать AI анализ для {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа для пользователя {user_id}: {e}")
            logger.exception("Полная трассировка ошибки:")  # Показывает stack trace
            return False

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
            
            # Ограничиваем длину сообщения (Telegram лимит ~4000 символов)
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
            
            # Удаляем ежедневные данные старше 3 месяцев
            cutoff_daily = date.today() - timedelta(days=90)
            
            # Удаляем анализы старше 1 года
            cutoff_analysis = date.today() - timedelta(days=365)
            
            # Выполняем очистку
            await conn.execute("""
                DELETE FROM garmin_daily_data 
                WHERE data_date < $1
            """, cutoff_daily)
            
            await conn.execute("""
                DELETE FROM garmin_analysis_history 
                WHERE analysis_date < $1
            """, cutoff_analysis)
            
            await release_db_connection(conn)

            logger.info(f"✅ Очистка завершена: удалены данные старше {cutoff_daily} и анализы старше {cutoff_analysis}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых данных: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def force_user_analysis(self, user_id: int) -> bool:
        """Принудительно запустить анализ для пользователя (для тестирования)"""
        try:
            logger.info(f"🔧 Принудительный запуск анализа для {user_id}")
            
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
            
            # Конвертируем asyncpg.Record в dict
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
            
            # Статистика пользователей
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                    COUNT(*) FILTER (WHERE sync_errors >= 5) as error_users,
                    COUNT(*) FILTER (WHERE last_sync_date = CURRENT_DATE) as synced_today
                FROM garmin_connections
            """)
            
            # Статистика данных за сегодня
            data_today = await conn.fetchval("""
                SELECT COUNT(*) FROM garmin_daily_data 
                WHERE sync_timestamp::date = CURRENT_DATE
            """)
            
            # Статистика анализов за сегодня
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