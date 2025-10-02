# garmin_scheduler.py - ПРОСТАЯ ЛОГИКА ПО ВРЕМЕНИ СНА

import asyncio
import logging
from datetime import datetime, date, timedelta
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
    """Планировщик с простой логикой: каждые 30 минут сравниваем время сна"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
        self.is_running = False
        
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            # Каждые 30 минут собираем данные у всех пользователей
            self.scheduler.add_job(
                func=self._collect_and_analyze_all_users,
                trigger=CronTrigger(minute='*/30'),  # Каждые 30 минут
                id='garmin_collect_every_30min',
                name='Сбор данных Garmin каждые 30 минут',
                replace_existing=True
            )
            
            # Очистка старых данных (раз в неделю)
            self.scheduler.add_job(
                func=self._cleanup_old_data,
                trigger=CronTrigger(day_of_week=6, hour=2, minute=0),
                id='garmin_cleanup',
                name='Очистка старых данных Garmin',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Простой планировщик Garmin запущен")
            logger.info("   🔄 Сбор данных: каждые 30 минут")
            logger.info("   🧠 Логика: сравнение времени сна")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации планировщика Garmin: {e}")
            raise

    async def shutdown(self):
        """Остановка планировщика"""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("🛑 Garmin планировщик остановлен")

    async def _collect_and_analyze_all_users(self):
        """
        ГЛАВНАЯ ФУНКЦИЯ: Каждые 30 минут собираем данные у всех пользователей
        и проверяем изменение времени сна
        """
        try:
            logger.info("🔄 Запуск сбора данных каждые 30 минут...")
            
            # Получаем ВСЕХ активных пользователей Garmin
            conn = await get_db_connection()
            users = await conn.fetch("""
                SELECT user_id 
                FROM garmin_connections 
                WHERE is_active = TRUE
            """)
            await release_db_connection(conn)
            
            if not users:
                logger.info("👥 Нет активных пользователей Garmin")
                return
            
            logger.info(f"👥 Собираем данные у {len(users)} пользователей")
            
            analysis_count = 0
            
            for user_row in users:
                user_id = user_row['user_id']
                
                try:
                    # Собираем данные и проверяем сон
                    analyzed = await self._collect_and_check_sleep(user_id)
                    
                    if analyzed:
                        analysis_count += 1
                    
                    # Пауза между пользователями (безопасность API)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки пользователя {user_id}: {e}")
                    continue
            
            if analysis_count > 0:
                logger.info(f"✅ Проведено {analysis_count} новых анализов")
            else:
                logger.debug("💤 Нет пользователей с изменившимся сном")
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка сбора данных: {e}")

    async def _collect_and_check_sleep(self, user_id: int) -> bool:
        """
        Собрать данные пользователя и проверить изменение сна
        ИСПРАВЛЕНИЕ: Сохраняем время сна ВСЕГДА, даже если нет лимитов
        
        Returns:
            True если провели анализ, False если нет
        """
        try:
            # 1. СОБИРАЕМ ДАННЫЕ ГИБРИДНО
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            logger.debug(f"Гибридный сбор данных для пользователя {user_id}")
            
            # Собираем данные за вчера (активность) и сегодня (сон)
            yesterday_data = await garmin_connector.collect_daily_data(user_id, yesterday)
            today_data = await garmin_connector.collect_daily_data(user_id, today)
            
            # Создаем гибридную запись
            hybrid_data = self._create_hybrid_record(yesterday_data, today_data, yesterday)
            
            # Получаем время сна из гибридных данных
            current_sleep_minutes = hybrid_data.get('sleep_duration_minutes')
            
            if not current_sleep_minutes or current_sleep_minutes < 60:
                logger.debug(f"Нет данных сна для пользователя {user_id}")
                return False
            
            # 2. ПРОВЕРЯЕМ ИЗМЕНЕНИЕ ВРЕМЕНИ СНА
            sleep_changed = await self._check_sleep_duration_changed(user_id, current_sleep_minutes)
            
            if not sleep_changed:
                logger.debug(f"Сон не изменился для пользователя {user_id} ({current_sleep_minutes} мин)")
                return False
            
            # Логируем что получилось в гибридной записи
            self._log_hybrid_result(user_id, hybrid_data, yesterday, today)
            
            # 3. ПРОВЕРЯЕМ ЛИМИТЫ
            logger.info(f"🧠 Новый сон у пользователя {user_id}: {current_sleep_minutes} мин")
            
            from subscription_manager import SubscriptionManager
            sub_manager = SubscriptionManager()
            
            user_limits = await sub_manager.get_user_limits(user_id)
            gpt4o_left = user_limits.get('gpt4o_queries_left', 0)
            
            # 🔥 ИСПРАВЛЕНИЕ: Сохраняем время сна СРАЗУ, ДО проверки лимитов
            # Это предотвратит повторные уведомления
            await self._save_analyzed_sleep_duration(user_id, current_sleep_minutes)
            logger.debug(f"💾 Сохранили новое время сна: {current_sleep_minutes} мин")
            
            # 4. ПРОВЕРЯЕМ ЕСТЬ ЛИ ЛИМИТЫ
            if gpt4o_left <= 0:
                logger.info(f"⚠️ У пользователя {user_id} закончились консультации")
                await self._send_data_collected_notification(user_id)
                return False
            
            # 5. СОЗДАЁМ АНАЛИЗ (только если есть лимиты)
            analysis_date = yesterday
            daily_data = hybrid_data
            
            analysis_success = await self._create_and_send_analysis(user_id, analysis_date, daily_data)
            
            if analysis_success:
                # Списываем лимит
                await sub_manager.spend_limits(user_id, queries=1)
                logger.info(f"✅ Анализ создан и отправлен пользователю {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Не удалось создать анализ для пользователя {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки пользователя {user_id}: {e}")
            return False

    async def _check_sleep_duration_changed(self, user_id: int, current_sleep_minutes: int) -> bool:
        """Проверить, изменилось ли время сна"""
        try:
            conn = await get_db_connection()
            
            result = await conn.fetchrow("""
                SELECT last_analyzed_sleep_duration 
                FROM garmin_users_sleep_tracking 
                WHERE user_id = $1
            """, user_id)
            
            await release_db_connection(conn)
            
            if not result:
                # Первый анализ для пользователя
                logger.info(f"🆕 Первый сон для пользователя {user_id}: {current_sleep_minutes} мин")
                return True
            
            last_duration = result['last_analyzed_sleep_duration']
            
            if current_sleep_minutes != last_duration:
                logger.info(f"🔄 Сон изменился у пользователя {user_id}: {last_duration} → {current_sleep_minutes} мин")
                return True
            
            # Сон не изменился
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки изменения сна: {e}")
            return False

    def _create_hybrid_record(self, yesterday_data: Optional[Dict], today_data: Optional[Dict], base_date: date) -> Dict:
        """Создать гибридную запись: активность из вчера + сон из сегодня (из старого кода)"""
        
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
        result['sync_timestamp'] = datetime.now()
        
        return result

    def _log_hybrid_result(self, user_id: int, hybrid_data: Dict, yesterday: date, today: date):
        """Логировать результат гибридного сбора (из старого кода)"""
        
        logger.info(f"📋 ГИБРИДНАЯ ЛОГИКА для пользователя {user_id}:")
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

    async def _save_analyzed_sleep_duration(self, user_id: int, sleep_minutes: int):
        """Сохранить время проанализированного сна"""
        try:
            conn = await get_db_connection()
            
            await conn.execute("""
                INSERT INTO garmin_users_sleep_tracking (user_id, last_analyzed_sleep_duration, last_analysis_time)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    last_analyzed_sleep_duration = EXCLUDED.last_analyzed_sleep_duration,
                    last_analysis_time = NOW()
            """, user_id, sleep_minutes)
            
            await release_db_connection(conn)
            
            logger.debug(f"💾 Сохранено время сна {sleep_minutes} мин для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения времени сна: {e}")

    async def _send_data_collected_notification(self, user_id: int):
        """Отправить уведомление что данные собраны, но нужна подписка (из старого кода)"""
        try:
            from db_postgresql import get_user_language, t
            lang = await get_user_language(user_id)
            message = t("garmin_data_collected_reminder", lang)
            await self.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
            logger.info(f"📤 Отправлено напоминание о лимитах пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")

    async def _create_and_send_analysis(self, user_id: int, analysis_date: date, daily_data: dict) -> bool:
        """Создать и отправить анализ"""
        try:
            # Используем ваш существующий анализатор
            analysis_result = await garmin_analyzer.create_health_analysis(user_id, daily_data)
            
            # ИСПРАВЛЕНИЕ: проверяем что анализ создался (ваш анализатор возвращает другой формат)
            if not analysis_result:
                logger.warning(f"Не удалось создать анализ для пользователя {user_id}")
                return False
            
            # Получаем текст анализа из результата
            analysis_text = analysis_result.get('analysis_text') or analysis_result.get('text') or str(analysis_result)
            
            if not analysis_text or analysis_text == 'Анализ недоступен':
                logger.warning(f"Пустой анализ для пользователя {user_id}")
                return False
            
            # Безопасная обработка HTML (как в вашем старом коде)
            from gpt import safe_telegram_text
            safe_analysis = safe_telegram_text(analysis_text)
            
            if len(safe_analysis) > 3500:
                safe_analysis = safe_analysis[:3500] + "...\n\n📊 Полный анализ сохранен в истории."
            
            sleep_minutes = daily_data.get('sleep_duration_minutes', 0)
            hours = sleep_minutes // 60
            minutes = sleep_minutes % 60
            
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🩺 <b>Ваш ежедневный анализ здоровья</b>\n\n📅 Дата: {analysis_date.strftime('%d.%m.%Y')}\n⏰ Продолжительность сна: {hours}ч {minutes}мин\n\n{safe_analysis}",
                parse_mode='HTML'
            )
            
            logger.info(f"📤 Анализ отправлен пользователю {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания/отправки анализа для {user_id}: {e}")
            return False

    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            logger.info("🧹 Начинаю очистку старых данных Garmin")
            conn = await get_db_connection()
            
            cutoff_daily = date.today() - timedelta(days=90)
            cutoff_analysis = date.today() - timedelta(days=365)
            
            # Очищаем основные данные
            await conn.execute("DELETE FROM garmin_daily_data WHERE data_date < $1", cutoff_daily)
            await conn.execute("DELETE FROM garmin_analysis_history WHERE analysis_date < $1", cutoff_analysis)
            
            # Очищаем отслеживание сна старше 30 дней
            cutoff_sleep = date.today() - timedelta(days=30)
            await conn.execute("DELETE FROM garmin_users_sleep_tracking WHERE last_analysis_time::date < $1", cutoff_sleep)
            
            await release_db_connection(conn)
            logger.info(f"✅ Очистка завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых данных: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)

    async def force_user_analysis(self, user_id: int) -> bool:
        """Принудительно запустить анализ для пользователя (для тестирования)"""
        try:
            logger.info(f"🔧 Принудительный анализ для пользователя {user_id}")
            
            # Проверяем, что пользователь активен
            conn = await get_db_connection()
            user_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM garmin_connections 
                    WHERE user_id = $1 AND is_active = TRUE
                )
            """, user_id)
            await release_db_connection(conn)
            
            if not user_exists:
                logger.warning(f"Пользователь {user_id} не найден или не активен")
                return False
            
            # ИСПРАВЛЕНИЕ: используем нашу логику без повторных вызовов
            result = await self._collect_and_check_sleep(user_id)
            
            if result:
                logger.info(f"✅ Принудительный анализ выполнен для пользователя {user_id}")
                return True
            else:
                # Проверим причину почему анализ не прошел
                conn = await get_db_connection()
                sleep_tracking = await conn.fetchrow("""
                    SELECT last_analyzed_sleep_duration, last_analysis_time 
                    FROM garmin_users_sleep_tracking 
                    WHERE user_id = $1
                """, user_id)
                await release_db_connection(conn)
                
                if sleep_tracking:
                    logger.info(f"💤 Сон не изменился у пользователя {user_id} (последний: {sleep_tracking['last_analyzed_sleep_duration']} мин)")
                else:
                    logger.info(f"❌ Нет данных сна для пользователя {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка принудительного анализа для {user_id}: {e}")
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
                    COUNT(*) FILTER (WHERE sync_errors >= 5) as error_users
                FROM garmin_connections
            """)
            
            # Статистика отслеживания сна
            sleep_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as users_with_sleep_tracking,
                    COUNT(*) FILTER (WHERE last_analysis_time::date = CURRENT_DATE) as analyzed_today
                FROM garmin_users_sleep_tracking
            """)
            
            await release_db_connection(conn)

            return {
                'is_running': self.is_running,
                'logic': 'simple_duration_comparison',
                'check_frequency': '30_minutes',
                'total_users': user_stats['total_users'] if user_stats else 0,
                'active_users': user_stats['active_users'] if user_stats else 0,
                'error_users': user_stats['error_users'] if user_stats else 0,
                'users_with_sleep_tracking': sleep_stats['users_with_sleep_tracking'] if sleep_stats else 0,
                'analyzed_today': sleep_stats['analyzed_today'] if sleep_stats else 0,
                'next_check': self._get_next_job_time('garmin_collect_every_30min'),
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
        logger.info("✅ Простая система Garmin запущена")
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