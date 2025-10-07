# garmin_connector.py - Модуль для работы с Garmin Connect API (ОБНОВЛЕННАЯ ВЕРСИЯ)

import os
import json
import asyncio
import logging
from datetime import time, datetime, date, timedelta
from typing import Dict, Optional, List, Any
from cryptography.fernet import Fernet # type: ignore
from garminconnect import Garmin # type: ignore
from dotenv import load_dotenv

# Импортируем функции для работы с БД
from db_postgresql import get_db_connection, release_db_connection

load_dotenv()
logger = logging.getLogger(__name__)

# ================================
# КОНСТАНТЫ ДЛЯ РАБОТЫ СО СНОМ
# ================================

# Список полей ТОЛЬКО ночного сна (БЕЗ дневного сна nap_duration_minutes)
NIGHT_SLEEP_FIELDS = [
    'sleep_duration_minutes',      # Общая длительность сна
    'sleep_deep_minutes',          # Глубокий сон
    'sleep_light_minutes',         # Легкий сон
    'sleep_rem_minutes',           # REM-фаза (быстрый сон)
    'sleep_awake_minutes',         # Время бодрствования во сне
    'sleep_score',                 # Оценка качества сна
    'sleep_need_minutes',          # Потребность во сне
    'sleep_baseline_minutes',      # Базовая норма сна
    'sleep_periods_15min'          # Периоды сна по 15 минут
]

# ================================
# ШИФРОВАНИЕ ДАННЫХ GARMIN
# ================================

def get_encryption_key():
    """Получить ключ шифрования из переменных окружения"""
    key = os.getenv("GARMIN_ENCRYPTION_KEY")
    if not key:
        # Генерируем новый ключ если не существует
        key = Fernet.generate_key().decode()
        logger.warning(f"Создан новый ключ шифрования: {key}")
        logger.warning("Добавьте в .env: GARMIN_ENCRYPTION_KEY=" + key)
    return key.encode() if isinstance(key, str) else key

def encrypt_data(data: str) -> str:
    """Зашифровать строку"""
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Ошибка шифрования: {e}")
        return data

def decrypt_data(encrypted_data: str) -> str:
    """Расшифровать строку"""
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Ошибка расшифровки: {e}")
        return encrypted_data

# ================================
# КЛАСС ПОДКЛЮЧЕНИЯ К GARMIN
# ================================

class GarminConnector:
    """Класс для работы с Garmin Connect API"""
    
    def __init__(self):
        self._api_cache = {}  # Кеш подключений API

    async def save_garmin_connection(self, user_id: int, email: str, password: str) -> bool:
        """
        Сохранить данные подключения к Garmin
        УПРОЩЕННАЯ ВЕРСИЯ: без времени анализа и часового пояса
        """
        try:
            encrypted_email = encrypt_data(email)
            encrypted_password = encrypt_data(password)
            
            conn = await get_db_connection()
            
            await conn.execute("""
                INSERT INTO garmin_connections 
                (user_id, garmin_email, garmin_password, is_active, sync_errors)
                VALUES ($1, $2, $3, TRUE, 0)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    garmin_email = EXCLUDED.garmin_email,
                    garmin_password = EXCLUDED.garmin_password,
                    is_active = TRUE,
                    sync_errors = 0,
                    updated_at = NOW()
            """, user_id, encrypted_email, encrypted_password)
            
            await release_db_connection(conn)
            logger.info(f"✅ Garmin подключение сохранено для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения Garmin подключения для пользователя {user_id}: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False
        
    async def get_garmin_connection(self, user_id: int) -> Optional[Dict]:
        """Получить данные подключения к Garmin"""
        try:
            conn = await get_db_connection()
            
            result = await conn.fetchrow("""
                SELECT * FROM garmin_connections 
                WHERE user_id = $1 AND is_active = TRUE
            """, user_id)
            
            await release_db_connection(conn)
            
            if result:
                result = dict(result)
                result['garmin_email'] = decrypt_data(result['garmin_email'])
                result['garmin_password'] = decrypt_data(result['garmin_password'])
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения Garmin подключения: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return None

    async def test_garmin_connection(self, email: str, password: str) -> tuple[bool, str]:
        """Проверить подключение к Garmin"""
        try:
            api = Garmin(email, password)
            await asyncio.get_event_loop().run_in_executor(None, api.login)
            profile = await asyncio.get_event_loop().run_in_executor(None, api.get_full_name)
            return True, f"Подключение успешно! Пользователь: {profile}"
            
        except Exception as e:
            error_msg = str(e).lower()
            if "username" in error_msg or "password" in error_msg or "credentials" in error_msg:
                return False, "Неверный email или пароль"
            elif "rate limit" in error_msg:
                return False, "Превышен лимит запросов. Попробуйте позже"
            else:
                return False, f"Ошибка подключения: {str(e)}"

    async def disconnect_garmin(self, user_id: int) -> bool:
        """Отключить Garmin для пользователя"""
        try:
            conn = await get_db_connection()
            
            await conn.execute("""
                UPDATE garmin_connections 
                SET is_active = FALSE, updated_at = NOW()
                WHERE user_id = $1
            """, user_id)
            
            await release_db_connection(conn)
            
            if user_id in self._api_cache:
                del self._api_cache[user_id]
                
            logger.info(f"Garmin отключен для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отключения Garmin: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False

    async def get_garmin_api(self, user_id: int) -> Optional[Garmin]:
        """Получить API подключение к Garmin с кешированием"""
        try:
            if user_id in self._api_cache:
                return self._api_cache[user_id]
            
            connection = await self.get_garmin_connection(user_id)
            if not connection:
                return None
            
            api = Garmin(connection['garmin_email'], connection['garmin_password'])
            await asyncio.get_event_loop().run_in_executor(None, api.login)
            
            self._api_cache[user_id] = api
            return api
            
        except Exception as e:
            logger.error(f"Ошибка создания Garmin API для {user_id}: {e}")
            
            try:
                conn = await get_db_connection()
                await conn.execute("""
                    UPDATE garmin_connections 
                    SET sync_errors = sync_errors + 1, updated_at = NOW()
                    WHERE user_id = $1
                """, user_id)
                await release_db_connection(conn)
            except:
                pass
                
            return None

    async def collect_daily_data(self, user_id: int, target_date: date = None) -> Optional[Dict]:
        """ОБНОВЛЕННЫЙ сбор данных с исправлениями и дополнительными API"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
            
        try:
            api = await self.get_garmin_api(user_id)
            if not api:
                logger.warning(f"Не удалось получить Garmin API для пользователя")
                return None
            
            # Безопасное логирование
            hashed_id = hash(str(user_id)) % 10000
            logger.info(f"Расширенный сбор данных Garmin за {target_date} для #{hashed_id}")
            
            loop = asyncio.get_event_loop()
            tasks = []
            
            # Основные API
            tasks.extend([
                loop.run_in_executor(None, lambda: safe_api_call(api.get_steps_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_heart_rates, target_date.isoformat())),  
                loop.run_in_executor(None, lambda: safe_api_call(api.get_sleep_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_body_battery, target_date.isoformat(), target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_stress_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_spo2_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_respiration_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_training_readiness, target_date.isoformat()))
            ])
            
            # Дополнительные API для полного анализа (если поддерживаются)
            tasks.extend([
                loop.run_in_executor(None, lambda: safe_api_call(api.get_activities_by_date, target_date.isoformat(), target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_hrv_data, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_daily_summary, target_date.isoformat())),
                loop.run_in_executor(None, lambda: safe_api_call(api.get_training_status))
            ])
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Безопасное логирование результатов
            success_count = len([r for r in results if r is not None and not isinstance(r, Exception)])
            logger.info(f"Получено {success_count}/{len(results)} успешных ответов от Garmin API")
            
            # Распаковка результатов
            basic_results = results[:8]  # Основные 8 API
            extended_results = results[8:] if len(results) > 8 else [None, None, None, None]
            
            (steps_data, heart_data, sleep_data, battery_data, stress_data, spo2_data,
             respiration_data, readiness_data) = basic_results
             
            (activities_data, hrv_data, daily_summary, training_status) = extended_results
            
            # Формируем структурированные данные
            daily_data = {
                'user_id': user_id,
                'data_date': target_date,
                'sync_timestamp': datetime.now()
            }
            
            # ИСПРАВЛЕННЫЕ ПАРСЕРЫ
            if steps_data and not isinstance(steps_data, Exception):
                parsed = parse_steps_data_complete(steps_data)
                daily_data.update(parsed)
                logger.info(f"Шаги: {parsed.get('steps', 'нет данных')}")
            
            if heart_data and not isinstance(heart_data, Exception):
                parsed = parse_heart_data_complete(heart_data)
                daily_data.update(parsed)
                logger.info(f"Пульс: покоя {parsed.get('resting_heart_rate', '?')}, макс {parsed.get('max_heart_rate', '?')}")
            
            if sleep_data and not isinstance(sleep_data, Exception):
                parsed = parse_sleep_data_complete(sleep_data)
                daily_data.update(parsed)
                sleep_info = parsed.get('sleep_duration_minutes') or parsed.get('nap_duration_minutes')
                logger.info(f"Сон: {sleep_info} мин" if sleep_info else "Сон: нет данных")
            
            if battery_data and not isinstance(battery_data, Exception):
                parsed = parse_body_battery_complete(battery_data)
                daily_data.update(parsed)
                logger.info(f"Body Battery: {parsed.get('body_battery_min', '?')}-{parsed.get('body_battery_max', '?')}%")
            
            if stress_data and not isinstance(stress_data, Exception):
                parsed = parse_stress_data_complete(stress_data)
                daily_data.update(parsed)
                logger.info(f"Стресс: средний {parsed.get('stress_avg', '?')}, макс {parsed.get('stress_max', '?')}")
            
            # Стандартные парсеры для остальных данных
            if spo2_data and not isinstance(spo2_data, Exception):
                daily_data.update(parse_spo2_data(spo2_data))
                
            if respiration_data and not isinstance(respiration_data, Exception):
                daily_data.update(parse_respiration_data(respiration_data))
                
            if readiness_data and not isinstance(readiness_data, Exception):
                parsed = parse_training_readiness_complete(readiness_data)
                daily_data.update(parsed)
                logger.info(f"Готовность: {parsed.get('training_readiness', '?')}/100")
            
            # ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
            if activities_data and not isinstance(activities_data, Exception):
                parsed = parse_activities_data(activities_data)
                daily_data.update(parsed)
                
            if hrv_data and not isinstance(hrv_data, Exception):
                parsed = parse_hrv_data(hrv_data)
                daily_data.update(parsed)
                
            if daily_summary and not isinstance(daily_summary, Exception):
                parsed = parse_daily_summary(daily_summary)
                daily_data.update(parsed)
                
            if training_status and not isinstance(training_status, Exception):
                parsed = parse_training_status(training_status)
                daily_data.update(parsed)
            
            # Вычисляем оценку полноты данных
            daily_data['data_completeness_score'] = self._calculate_data_completeness(daily_data)
            daily_data['last_sync_quality'] = 'good' if success_count > 6 else 'partial' if success_count > 3 else 'poor'
            
            # Безопасное логирование итогов
            non_null_fields = len([k for k, v in daily_data.items() if v is not None])
            logger.info(f"Собраны расширенные данные Garmin: {non_null_fields} полей")
            
            # Сохраняем в БД
            await self.save_daily_data(daily_data)
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Ошибка расширенного сбора данных Garmin: {type(e).__name__}")
            return None

    def _calculate_data_completeness(self, daily_data: Dict) -> float:
        """Вычисляет оценку полноты собранных данных (0-100)"""
        try:
            # Ключевые поля для оценки полноты
            key_fields = [
                'steps', 'resting_heart_rate', 'max_heart_rate', 'stress_avg',
                'body_battery_max', 'training_readiness', 'sleep_duration_minutes'
            ]
            
            # Дополнительные поля (менее критичные)
            bonus_fields = [
                'avg_heart_rate', 'spo2_avg', 'respiration_avg', 'hrv_rmssd',
                'activities_count', 'calories', 'distance_meters'
            ]
            
            # Базовая оценка по ключевым полям
            key_score = sum(1 for field in key_fields if daily_data.get(field) is not None)
            base_score = (key_score / len(key_fields)) * 70  # 70% за основные поля
            
            # Бонусные баллы за дополнительные поля  
            bonus_score = sum(1 for field in bonus_fields if daily_data.get(field) is not None)
            bonus_points = (bonus_score / len(bonus_fields)) * 30  # 30% за дополнительные
            
            total_score = min(100, base_score + bonus_points)
            return round(total_score, 1)
            
        except Exception:
            return 0.0

    async def save_daily_data(self, daily_data: Dict) -> bool:
        """ОБНОВЛЕННОЕ сохранение с новыми полями"""
        try:
            conn = await get_db_connection()
            
            # Фильтруем только существующие поля таблицы
            table_fields = {
                'user_id', 'data_date', 'steps', 'calories', 'floors_climbed', 'distance_meters',
                'sleep_duration_minutes', 'sleep_deep_minutes', 'sleep_light_minutes', 
                'sleep_rem_minutes', 'sleep_awake_minutes', 'sleep_score',
                'resting_heart_rate', 'avg_heart_rate', 'max_heart_rate', 'min_heart_rate',
                'hrv_rmssd', 'stress_avg', 'stress_max', 'stress_min',
                'body_battery_max', 'body_battery_min', 'body_battery_charged', 'body_battery_drained',
                'spo2_avg', 'respiration_avg', 'training_readiness', 'vo2_max', 'fitness_age',
                'activities_count', 'activities_duration_minutes', 'activities_calories', 
                'activities_data', 'sync_timestamp', 'data_quality',
                # Новые поля
                'nap_duration_minutes', 'sleep_need_minutes', 'sleep_baseline_minutes',
                'body_battery_avg', 'body_battery_stress_events', 'body_battery_recovery_events',
                'heart_rate_measurements', 'hr_zone_rest_percent', 'resting_heart_rate_7day_avg',
                'active_periods_15min', 'sedentary_periods_15min', 'total_calories',
                'vigorous_intensity_minutes', 'moderate_intensity_minutes',
                'activities_types', 'hrv_status', 'hrv_baseline', 
                'training_readiness_status', 'training_status', 'training_load_7day',
                'data_completeness_score', 'last_sync_quality', 'body_battery_after_sleep'
            }
            
            # Отфильтровываем только те поля, которые есть в таблице
            filtered_data = {k: v for k, v in daily_data.items() 
                           if k in table_fields and v is not None}
            
            if not filtered_data:
                logger.warning("Нет данных для сохранения в БД")
                return False
            
            # Строим запрос
            fields = list(filtered_data.keys())
            values = list(filtered_data.values())
            placeholders = [f'${i+1}' for i in range(len(values))]
            
            # UPSERT запрос
            query = f"""
                INSERT INTO garmin_daily_data ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (user_id, data_date) 
                DO UPDATE SET {', '.join(f'{field} = EXCLUDED.{field}' for field in fields)}
                RETURNING id
            """
            
            result = await conn.fetchrow(query, *values)
            await release_db_connection(conn)
            
            if result:
                logger.info(f"Данные сохранены в БД (ID: {result['id']})")
                
                # ============================================
                # НОВАЯ ЛОГИКА: Переносим данные сна в предыдущий день
                # ============================================
                await self._update_previous_day_sleep(daily_data)
                
                return True
            else:
                logger.warning("Данные не были сохранены в БД")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {type(e).__name__}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False
    
    async def _update_previous_day_sleep(self, daily_data: Dict) -> bool:
        """
        Обновляет данные НОЧНОГО сна в записи предыдущего дня
        
        Логика:
        - Берем данные сна из текущего дня (например, 7 октября)
        - Переносим их в предыдущий день (6 октября)
        - Обновляем ТОЛЬКО если запись за предыдущий день УЖЕ СУЩЕСТВУЕТ
        - НЕ создаем новые записи
        
        ВАЖНО: Дневной сон (nap_duration_minutes) НЕ переносится!
        """
        try:
            # Проверяем наличие обязательных полей
            if 'user_id' not in daily_data or 'data_date' not in daily_data:
                logger.warning("Отсутствуют user_id или data_date, пропускаем обновление сна")
                return False
            
            user_id = daily_data['user_id']
            current_date = daily_data['data_date']
            
            # Вычисляем дату предыдущего дня
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date, '%Y-%m-%d').date()
            
            previous_date = current_date - timedelta(days=1)
            
            # Извлекаем ТОЛЬКО данные ночного сна из текущих данных
            sleep_data = {}
            for field in NIGHT_SLEEP_FIELDS:
                if field in daily_data and daily_data[field] is not None:
                    sleep_data[field] = daily_data[field]
            
            # Если данных сна нет - нечего обновлять
            if not sleep_data:
                logger.info("Данных ночного сна нет, пропускаем обновление предыдущего дня")
                return False
            
            # Проверяем, существует ли запись за предыдущий день
            conn = await get_db_connection()
            
            existing_record = await conn.fetchrow("""
                SELECT id FROM garmin_daily_data 
                WHERE user_id = $1 AND data_date = $2
            """, user_id, previous_date)
            
            # Если записи нет - не создаем новую, просто выходим
            if not existing_record:
                logger.info(f"Запись за {previous_date} не найдена, пропускаем обновление сна")
                await release_db_connection(conn)
                return False
            
            # Формируем SQL запрос для обновления ТОЛЬКО полей сна
            update_fields = []
            values = []
            param_index = 1
            
            for field, value in sleep_data.items():
                update_fields.append(f"{field} = ${param_index}")
                values.append(value)
                param_index += 1
            
            # Добавляем user_id и data_date в конец списка параметров
            values.append(user_id)
            values.append(previous_date)
            
            # SQL запрос: обновляем ТОЛЬКО поля сна
            update_query = f"""
                UPDATE garmin_daily_data
                SET {', '.join(update_fields)}
                WHERE user_id = ${param_index} AND data_date = ${param_index + 1}
            """
            
            # Выполняем обновление
            await conn.execute(update_query, *values)
            await release_db_connection(conn)
            
            # Безопасное логирование (без конкретных значений)
            logger.info(f"✅ Данные ночного сна ({len(sleep_data)} полей) обновлены в записи предыдущего дня")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления сна в предыдущем дне: {type(e).__name__}")
            return False

# ================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПАРСИНГА
# ================================

def safe_api_call(func, *args, **kwargs):
    """Безопасный вызов API функции"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.debug(f"API вызов не удался: {func.__name__}: {e}")
        return None

def safe_get_value(data, *keys, default=None):
    """Безопасно получить значение из вложенной структуры"""
    try:
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                current = current[key]
            else:
                return default
            if current is None:
                return default
        return current
    except:
        return default

# ================================
# ИСПРАВЛЕННЫЕ ПАРСЕРЫ ДАННЫХ
# ================================

def parse_steps_data_complete(steps_data):
    """ИСПРАВЛЕННЫЙ парсер шагов - извлекает ВСЕ данные активности"""
    result = {}
    
    try:
        if not isinstance(steps_data, list):
            return result
            
        total_steps = 0
        active_periods = 0
        sedentary_periods = 0
        sleeping_periods = 0
        calories_burned = 0
        distance_meters = 0
        floors_climbed = 0
        
        for entry in steps_data:
            if not isinstance(entry, dict):
                continue
                
            steps = safe_get_value(entry, 'steps', default=0)
            total_steps += steps
            
            # НОВОЕ: Извлекаем дополнительные данные
            calories = safe_get_value(entry, 'calories', default=0)
            distance = safe_get_value(entry, 'distance', default=0)
            floors = safe_get_value(entry, 'floorsClimbed', default=0)
            
            calories_burned += calories
            distance_meters += distance  
            floors_climbed += floors
            
            # Анализ уровня активности
            activity_level = safe_get_value(entry, 'primaryActivityLevel')
            if activity_level == 'active':
                active_periods += 1
            elif activity_level == 'sedentary':
                sedentary_periods += 1
            elif activity_level == 'sleeping':
                sleeping_periods += 1
                
        result.update({
            'steps': total_steps,
            'active_periods_15min': active_periods,
            'sedentary_periods_15min': sedentary_periods,  
            'sleep_periods_15min': sleeping_periods
        })
        
        # НОВОЕ: Добавляем дополнительные метрики если они есть
        if calories_burned > 0:
            result['calories'] = calories_burned
        if distance_meters > 0:
            result['distance_meters'] = distance_meters
        if floors_climbed > 0:
            result['floors_climbed'] = floors_climbed
            
    except Exception as e:
        logger.error(f"Ошибка парсинга шагов: {e}")
        
    return result

def parse_heart_data_complete(heart_data):
    """ИСПРАВЛЕННЫЙ парсер пульса - извлекает ВСЕ показатели"""
    result = {}
    
    try:
        if not isinstance(heart_data, dict):
            return result
            
        # Базовые показатели
        resting_hr = safe_get_value(heart_data, 'restingHeartRate')
        max_hr = safe_get_value(heart_data, 'maxHeartRate') 
        min_hr = safe_get_value(heart_data, 'minHeartRate')
        
        if resting_hr:
            result['resting_heart_rate'] = resting_hr
        if max_hr:
            result['max_heart_rate'] = max_hr
        if min_hr:
            result['min_heart_rate'] = min_hr
            
        # ИСПРАВЛЕНИЕ: Вычисляем средний пульс из массива
        heart_values = safe_get_value(heart_data, 'heartRateValues')
        if heart_values and isinstance(heart_values, list):
            valid_rates = []
            zone_counts = {'rest': 0, 'easy': 0, 'aerobic': 0, 'threshold': 0, 'max': 0}
            
            for entry in heart_values:
                if isinstance(entry, list) and len(entry) >= 2:
                    hr = entry[1]  # [timestamp, heart_rate]
                    if hr is not None and isinstance(hr, (int, float)) and hr > 40:
                        valid_rates.append(hr)
                        
                        # Зоны пульса (примерные для анализа)
                        if hr < 60:
                            zone_counts['rest'] += 1
                        elif hr < 100:
                            zone_counts['easy'] += 1
                        elif hr < 140:
                            zone_counts['aerobic'] += 1
                        elif hr < 170:
                            zone_counts['threshold'] += 1
                        else:
                            zone_counts['max'] += 1
                            
            if valid_rates:
                result['avg_heart_rate'] = sum(valid_rates) // len(valid_rates)
                result['heart_rate_measurements'] = len(valid_rates)
                
                # Время в зонах (в процентах)
                total = len(valid_rates)
                result['hr_zone_rest_percent'] = round(zone_counts['rest'] / total * 100, 1)
                result['hr_zone_aerobic_percent'] = round(zone_counts['aerobic'] / total * 100, 1)
                
        # НОВОЕ: 7-дневный средний пульс покоя  
        avg_7day_rhr = safe_get_value(heart_data, 'lastSevenDaysAvgRestingHeartRate')
        if avg_7day_rhr:
            result['resting_heart_rate_7day_avg'] = avg_7day_rhr
            
    except Exception as e:
        logger.error(f"Ошибка парсинга пульса: {e}")
        
    return result

def parse_sleep_data_complete(sleep_data):
    """ИСПРАВЛЕННЫЙ парсер данных сна - учитывает все случаи"""
    result = {}
    
    try:
        if not sleep_data:
            return result
            
        # Получаем основной объект сна
        daily_sleep = None
        if isinstance(sleep_data, dict):
            daily_sleep = sleep_data.get('dailySleepDTO')
        elif isinstance(sleep_data, list) and len(sleep_data) > 0:
            daily_sleep = sleep_data[0].get('dailySleepDTO') if isinstance(sleep_data[0], dict) else None
            
        if daily_sleep:
            # Основная длительность сна
            sleep_seconds = safe_get_value(daily_sleep, 'sleepTimeSeconds')
            if sleep_seconds and sleep_seconds > 0:
                result['sleep_duration_minutes'] = sleep_seconds // 60
            else:
                # НОВОЕ: Если основного сна нет, проверяем дневной сон
                nap_seconds = safe_get_value(daily_sleep, 'napTimeSeconds')
                if nap_seconds and nap_seconds > 0 and nap_seconds < 10800:  # Меньше 3 часов
                    result['nap_duration_minutes'] = nap_seconds // 60
                    logger.info(f"Обнаружен дневной сон: {result['nap_duration_minutes']} мин")
                    
            # Фазы сна (если есть)
            deep_seconds = safe_get_value(daily_sleep, 'deepSleepSeconds')
            if deep_seconds and deep_seconds > 0:
                result['sleep_deep_minutes'] = deep_seconds // 60
                
            light_seconds = safe_get_value(daily_sleep, 'lightSleepSeconds')  
            if light_seconds and light_seconds > 0:
                result['sleep_light_minutes'] = light_seconds // 60
                
            rem_seconds = safe_get_value(daily_sleep, 'remSleepSeconds')
            if rem_seconds and rem_seconds > 0:
                result['sleep_rem_minutes'] = rem_seconds // 60
                
            awake_seconds = safe_get_value(daily_sleep, 'awakeSleepSeconds')
            if awake_seconds and awake_seconds > 0:
                result['sleep_awake_minutes'] = awake_seconds // 60
                
            # Sleep Need (потребность во сне)
            sleep_need = safe_get_value(daily_sleep, 'sleepNeed')
            if sleep_need:
                actual_need = safe_get_value(sleep_need, 'actual')
                baseline_need = safe_get_value(sleep_need, 'baseline')  
                if actual_need:
                    result['sleep_need_minutes'] = actual_need
                if baseline_need:
                    result['sleep_baseline_minutes'] = baseline_need
                    
    except Exception as e:
        logger.error(f"Ошибка парсинга сна: {e}")
        
    return result

def parse_body_battery_complete(battery_data):
    """ИСПРАВЛЕННЫЙ парсер Body Battery - извлекает ВСЕ данные"""
    result = {}
    
    try:
        if not battery_data or not isinstance(battery_data, list):
            return result
            
        for day_data in battery_data:
            if not isinstance(day_data, dict):
                continue
                
            # ИСПРАВЛЕНИЕ: Правильно извлекаем charged/drained
            charged = safe_get_value(day_data, 'charged')
            drained = safe_get_value(day_data, 'drained')
            
            if charged is not None:
                result['body_battery_charged'] = charged
            if drained is not None:
                result['body_battery_drained'] = drained
                
            # ИСПРАВЛЕНИЕ: Извлекаем min/max из массива значений
            values_array = safe_get_value(day_data, 'bodyBatteryValuesArray')
            if values_array and isinstance(values_array, list):
                battery_levels = []
                for entry in values_array:
                    if isinstance(entry, list) and len(entry) >= 2:
                        level = entry[1]  # [timestamp, level]
                        if level is not None and isinstance(level, (int, float)):
                            battery_levels.append(level)
                            
                if battery_levels:
                    result['body_battery_max'] = max(battery_levels)
                    result['body_battery_min'] = min(battery_levels)
                    result['body_battery_avg'] = round(sum(battery_levels) / len(battery_levels), 1)
                    
            # События Body Battery (восстановление/стресс/активность)
            activity_events = safe_get_value(day_data, 'bodyBatteryActivityEvent')
            if activity_events and isinstance(activity_events, list):
                # Подсчитываем события по типам
                stress_events = len([e for e in activity_events if e.get('eventType') == 'STRESS'])
                recovery_events = len([e for e in activity_events if e.get('eventType') == 'RECOVERY'])
                activity_events_count = len([e for e in activity_events if e.get('eventType') == 'ACTIVITY'])
                
                result.update({
                    'body_battery_stress_events': stress_events,
                    'body_battery_recovery_events': recovery_events, 
                    'body_battery_activity_events': activity_events_count
                })
                
    except Exception as e:
        logger.error(f"Ошибка парсинга Body Battery: {e}")
        
    return result

def parse_stress_data_complete(stress_data):
    """ИСПРАВЛЕННЫЙ парсер стресса - извлекает ВСЕ показатели"""
    result = {}
    
    try:
        if not isinstance(stress_data, dict):
            return result
            
        # ИСПРАВЛЕНИЕ: Правильно извлекаем данные стресса
        max_stress = safe_get_value(stress_data, 'maxStressLevel')
        avg_stress = safe_get_value(stress_data, 'avgStressLevel')
        
        if max_stress is not None:
            result['stress_max'] = max_stress
        if avg_stress is not None:
            result['stress_avg'] = avg_stress
            
        # НОВОЕ: Детальный анализ стресса по времени
        stress_values = safe_get_value(stress_data, 'stressValuesArray')
        if stress_values and isinstance(stress_values, list):
            valid_stress = []
            high_stress_periods = 0
            
            for entry in stress_values:
                if isinstance(entry, list) and len(entry) >= 2:
                    stress_level = entry[1]  # [timestamp, stress_level]
                    if stress_level is not None and stress_level > 0:  # -1/-2 это отсутствие данных
                        valid_stress.append(stress_level)
                        if stress_level > 75:  # Высокий стресс
                            high_stress_periods += 1
                            
            if valid_stress:
                result['stress_min'] = min(valid_stress)
                result['stress_high_periods_count'] = high_stress_periods
                result['stress_low_periods_count'] = len([s for s in valid_stress if s < 25])
                
    except Exception as e:
        logger.error(f"Ошибка парсинга стресса: {e}")
        
    return result

def parse_training_readiness_complete(readiness_data):
    """Полный парсер готовности к тренировкам"""
    result = {}
    
    try:
        if isinstance(readiness_data, dict):
            score = safe_get_value(readiness_data, 'score')
            if score:
                result['training_readiness'] = score
                
            # НОВОЕ: Дополнительные метрики готовности
            status = safe_get_value(readiness_data, 'status')
            if status:
                result['training_readiness_status'] = status
                
            factors = safe_get_value(readiness_data, 'factors')
            if factors and isinstance(factors, dict):
                sleep_factor = safe_get_value(factors, 'sleepScore')
                hrv_factor = safe_get_value(factors, 'hrvScore') 
                stress_factor = safe_get_value(factors, 'stressScore')
                
                if sleep_factor:
                    result['readiness_sleep_factor'] = sleep_factor
                if hrv_factor:
                    result['readiness_hrv_factor'] = hrv_factor  
                if stress_factor:
                    result['readiness_stress_factor'] = stress_factor
                    
    except Exception as e:
        logger.error(f"Ошибка парсинга готовности: {e}")
        
    return result

def parse_activities_data(activities_data):
    """Парсинг данных активностей и тренировок за день"""
    result = {}
    
    try:
        if not isinstance(activities_data, list):
            return result
            
        activities_count = len(activities_data)
        total_duration = 0
        total_calories = 0
        activity_types = []
        max_intensity = 0
        
        for activity in activities_data:
            if not isinstance(activity, dict):
                continue
                
            # Длительность активности
            duration = safe_get_value(activity, 'duration', default=0)
            total_duration += duration
            
            # Калории
            calories = safe_get_value(activity, 'calories', default=0) 
            total_calories += calories
            
            # Тип активности
            activity_type = safe_get_value(activity, 'activityType')
            if activity_type:
                activity_types.append(activity_type.get('typeKey', 'unknown'))
                
            # Интенсивность
            intensity = safe_get_value(activity, 'averageRunningCadenceInStepsPerMinute', default=0)
            if intensity > max_intensity:
                max_intensity = intensity
                
        result.update({
            'activities_count': activities_count,
            'activities_duration_minutes': total_duration // 60 if total_duration else 0,
            'activities_calories': total_calories,
            'activities_types': ','.join(set(activity_types)) if activity_types else None,
            'activities_max_intensity': max_intensity if max_intensity > 0 else None
        })
        
    except Exception as e:
        logger.error(f"Ошибка парсинга активностей: {e}")
        
    return result

def parse_hrv_data(hrv_data):
    """Парсинг данных вариабельности сердечного ритма (HRV)"""
    result = {}
    
    try:
        if isinstance(hrv_data, dict):
            # Основной показатель HRV
            hrv_rmssd = safe_get_value(hrv_data, 'lastNightAvg')
            if hrv_rmssd:
                result['hrv_rmssd'] = hrv_rmssd
                
            # Статус HRV
            hrv_status = safe_get_value(hrv_data, 'status')
            if hrv_status:
                result['hrv_status'] = hrv_status
                
            # Базовый уровень HRV
            baseline = safe_get_value(hrv_data, 'baseline')
            if baseline:
                result['hrv_baseline'] = baseline
                
        elif isinstance(hrv_data, list) and len(hrv_data) > 0:
            # Берем последнее значение
            latest = hrv_data[0]
            if isinstance(latest, dict):
                result.update(parse_hrv_data(latest))
                
    except Exception as e:
        logger.error(f"Ошибка парсинга HRV: {e}")
        
    return result

def parse_daily_summary(daily_summary):
    """Парсинг общей сводки дня"""
    result = {}
    
    try:
        if not isinstance(daily_summary, dict):
            return result
            
        # Общие калории
        calories = safe_get_value(daily_summary, 'totalKilocalories')
        if calories:
            result['total_calories'] = calories
            
        # Расстояние
        distance = safe_get_value(daily_summary, 'totalDistanceMeters')
        if distance:
            result['distance_meters'] = distance
            
        # Этажи
        floors = safe_get_value(daily_summary, 'floorsAscended')
        if floors:
            result['floors_climbed'] = floors
            
        # Интенсивные минуты
        vigorous_minutes = safe_get_value(daily_summary, 'vigorousIntensityMinutes')
        moderate_minutes = safe_get_value(daily_summary, 'moderateIntensityMinutes')
        
        if vigorous_minutes:
            result['vigorous_intensity_minutes'] = vigorous_minutes
        if moderate_minutes:
            result['moderate_intensity_minutes'] = moderate_minutes
            
        # VO2 Max
        vo2_max = safe_get_value(daily_summary, 'vo2Max')
        if vo2_max:
            result['vo2_max'] = vo2_max
            
    except Exception as e:
        logger.error(f"Ошибка парсинга сводки дня: {e}")
        
    return result

def parse_training_status(training_status):
    """Парсинг статуса тренировок"""
    result = {}
    
    try:
        if not isinstance(training_status, dict):
            return result
            
        # Статус тренировок  
        status = safe_get_value(training_status, 'trainingStatusKey')
        if status:
            result['training_status'] = status
            
        # Нагрузка
        load_7day = safe_get_value(training_status, 'sevenDayTrainingLoad')
        if load_7day:
            result['training_load_7day'] = load_7day
            
        # Фитнес возраст
        fitness_age = safe_get_value(training_status, 'fitnessAge')
        if fitness_age:
            result['fitness_age'] = fitness_age
            
    except Exception as e:
        logger.error(f"Ошибка парсинга статуса тренировок: {e}")
        
    return result

# ================================
# СТАНДАРТНЫЕ ПАРСЕРЫ (без изменений)
# ================================

def parse_spo2_data(spo2_data):
    """Парсинг данных SpO2"""
    result = {}
    try:
        if isinstance(spo2_data, dict):
            result['spo2_avg'] = safe_get_value(spo2_data, 'averageSpO2')
        elif isinstance(spo2_data, list) and len(spo2_data) > 0:
            spo2_values = []
            for item in spo2_data:
                if isinstance(item, dict):
                    val = safe_get_value(item, 'value')
                    if val and val > 0:
                        spo2_values.append(val)
                elif isinstance(item, (int, float)) and item > 0:
                    spo2_values.append(item)
            
            if spo2_values:
                result['spo2_avg'] = sum(spo2_values) / len(spo2_values)
    except Exception as e:
        logger.debug(f"Ошибка парсинга SpO2: {e}")
    return result

def parse_respiration_data(respiration_data):
    """Парсинг данных дыхания"""
    result = {}
    try:
        if isinstance(respiration_data, dict):
            result['respiration_avg'] = safe_get_value(respiration_data, 'avgRespirationValue')
        elif isinstance(respiration_data, list) and len(respiration_data) > 0:
            resp_values = []
            for item in respiration_data:
                if isinstance(item, dict):
                    val = safe_get_value(item, 'value')
                    if val and val > 0:
                        resp_values.append(val)
                elif isinstance(item, (int, float)) and item > 0:
                    resp_values.append(item)
            
            if resp_values:
                result['respiration_avg'] = sum(resp_values) / len(resp_values)
    except Exception as e:
        logger.debug(f"Ошибка парсинга дыхания: {e}")
    return result

# ================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ================================

garmin_connector = GarminConnector()