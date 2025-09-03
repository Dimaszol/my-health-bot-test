# garmin_connector.py - Модуль для работы с Garmin Connect API

import os
import json
import asyncio
import logging
from datetime import time, datetime, date, timedelta
from typing import Dict, Optional, List, Any
from cryptography.fernet import Fernet
from garminconnect import Garmin
from dotenv import load_dotenv

# Импортируем функции для работы с БД
from db_postgresql import get_db_connection, release_db_connection

load_dotenv()
logger = logging.getLogger(__name__)

# ================================
# ШИФРОВАНИЕ ДАННЫХ GARMIN
# ================================

def get_encryption_key():
    """Получить ключ шифрования из переменных окружения"""
    key = os.getenv("GARMIN_ENCRYPTION_KEY")
    if not key:
        # Генерируем новый ключ если не существует
        key = Fernet.generate_key().decode()
        logger.warning(f"⚠️ Создан новый ключ шифрования: {key}")
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

    async def save_garmin_connection(self, user_id: int, email: str, password: str, 
                                   notification_time: str = "07:00", timezone_offset: int = 0,
                                   timezone_name: str = "UTC") -> bool:
        """Сохранить данные подключения к Garmin"""
        try:
            # Конвертируем строку времени в объект time
            if isinstance(notification_time, str):
                try:
                    time_obj = time.fromisoformat(notification_time)
                except ValueError as e:
                    logger.warning(f"⚠️ Некорректный формат времени '{notification_time}', используем 07:00")
                    time_obj = time(7, 0)
            else:
                time_obj = notification_time
            
            encrypted_email = encrypt_data(email)
            encrypted_password = encrypt_data(password)
            
            conn = await get_db_connection()
            
            await conn.execute("""
                INSERT INTO garmin_connections 
                (user_id, garmin_email, garmin_password, notification_time, 
                 timezone_offset, timezone_name, is_active, sync_errors)
                VALUES ($1, $2, $3, $4, $5, $6, TRUE, 0)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    garmin_email = EXCLUDED.garmin_email,
                    garmin_password = EXCLUDED.garmin_password,
                    notification_time = EXCLUDED.notification_time,
                    timezone_offset = EXCLUDED.timezone_offset,
                    timezone_name = EXCLUDED.timezone_name,
                    is_active = TRUE,
                    sync_errors = 0,
                    updated_at = NOW()
            """, user_id, encrypted_email, encrypted_password, time_obj,
                 timezone_offset, timezone_name)
            
            await release_db_connection(conn)
            logger.info(f"✅ Garmin подключение сохранено для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения Garmin подключения для пользователя {user_id}: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
            return False
    
    async def update_notification_time(self, user_id: int, new_time_str: str) -> bool:
        """Безопасное обновление времени уведомлений"""
        try:
            try:
                time_obj = time.fromisoformat(new_time_str)
            except ValueError:
                logger.warning(f"⚠️ Некорректный формат времени от пользователя {user_id}: '{new_time_str}'")
                return False
            
            conn = await get_db_connection()
            
            result = await conn.execute("""
                UPDATE garmin_connections 
                SET notification_time = $1, updated_at = NOW()
                WHERE user_id = $2 AND is_active = TRUE
            """, time_obj, user_id)
            
            await release_db_connection(conn)
            
            if result == "UPDATE 1":
                logger.info(f"✅ Время анализа обновлено для пользователя {user_id}: {time_obj}")
                return True
            else:
                logger.warning(f"⚠️ Пользователь {user_id} не найден или Garmin не активен")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления времени для пользователя {user_id}: {e}")
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
            logger.error(f"❌ Ошибка получения Garmin подключения: {e}")
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
                
            logger.info(f"✅ Garmin отключен для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отключения Garmin: {e}")
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
            logger.error(f"❌ Ошибка создания Garmin API для {user_id}: {e}")
            
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
        """Собрать все данные за день"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
            
        try:
            api = await self.get_garmin_api(user_id)
            if not api:
                logger.warning(f"Не удалось получить Garmin API для {user_id}")
                return None
            
            logger.info(f"📊 Собираю данные Garmin за {target_date} для пользователя {user_id}")
            
            # Собираем данные параллельно
            tasks = []
            loop = asyncio.get_event_loop()
            
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_steps_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_heart_rates, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_sleep_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_body_battery, target_date.isoformat(), target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_stress_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_spo2_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_respiration_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_training_readiness, target_date.isoformat())))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            steps_data, heart_data, sleep_data, battery_data, stress_data, spo2_data, respiration_data, readiness_data = results
            
            # Формируем структурированные данные
            daily_data = {
                'user_id': user_id,
                'data_date': target_date,
                'sync_timestamp': datetime.now()
            }
            
            # Обрабатываем шаги и активность
            if steps_data and not isinstance(steps_data, Exception):
                daily_data.update(parse_steps_data(steps_data))
            
            # Обрабатываем пульс
            if heart_data and not isinstance(heart_data, Exception):
                daily_data.update(parse_heart_data(heart_data))
            
            # Обрабатываем сон
            if sleep_data and not isinstance(sleep_data, Exception):
                daily_data.update(parse_sleep_data(sleep_data))
            
            # Обрабатываем Body Battery
            if battery_data and not isinstance(battery_data, Exception):
                daily_data.update(parse_body_battery_data(battery_data))
            
            # Обрабатываем стресс
            if stress_data and not isinstance(stress_data, Exception):
                daily_data.update(parse_stress_data(stress_data))
            
            # Обрабатываем SpO2
            if spo2_data and not isinstance(spo2_data, Exception):
                daily_data.update(parse_spo2_data(spo2_data))
            
            # Обрабатываем дыхание
            if respiration_data and not isinstance(respiration_data, Exception):
                daily_data.update(parse_respiration_data(respiration_data))
            
            # Обрабатываем готовность к тренировкам
            if readiness_data and not isinstance(readiness_data, Exception):
                daily_data.update(parse_readiness_data(readiness_data))
            
            logger.info(f"✅ Собраны данные Garmin: {len([k for k,v in daily_data.items() if v is not None])} полей")
            return daily_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных Garmin для {user_id}: {e}")
            return None

    async def save_daily_data(self, daily_data: Dict) -> bool:
        """Сохранить ежедневные данные в БД"""
        try:
            conn = await get_db_connection()
            
            fields = []
            values = []
            placeholders = []
            
            for key, value in daily_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
                    placeholders.append(f'${len(placeholders) + 1}')
            
            update_fields = ', '.join([f"{field} = EXCLUDED.{field}" for field in fields if field not in ['user_id', 'data_date']])
            
            query = f"""
                INSERT INTO garmin_daily_data ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (user_id, data_date)
                DO UPDATE SET {update_fields}
            """
            
            await conn.execute(query, *values)
            await release_db_connection(conn)
            
            logger.info(f"✅ Данные Garmin сохранены в БД для пользователя {daily_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных Garmin: {e}")
            if 'conn' in locals():
                await release_db_connection(conn)
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

def parse_steps_data(steps_data):
    """Парсинг данных активности"""
    result = {}
    try:
        if isinstance(steps_data, dict):
            result['steps'] = safe_get_value(steps_data, 'totalSteps', default=0)
            result['calories'] = safe_get_value(steps_data, 'totalKilocalories', default=0)
            result['distance_meters'] = int(safe_get_value(steps_data, 'totalDistanceMeters', default=0))
            result['floors_climbed'] = safe_get_value(steps_data, 'floorsAscended', default=0)
        elif isinstance(steps_data, list) and len(steps_data) > 0:
            return parse_steps_data(steps_data[0])
    except Exception as e:
        logger.debug(f"Ошибка парсинга активности: {e}")
    return result

def parse_heart_data(heart_data):
    """Парсинг данных пульса"""
    result = {}
    try:
        if isinstance(heart_data, dict):
            result['resting_heart_rate'] = safe_get_value(heart_data, 'restingHeartRate')
            result['max_heart_rate'] = safe_get_value(heart_data, 'maxHeartRate')
            
            # Средний пульс
            avg_hr = safe_get_value(heart_data, 'averageHeartRate')
            if not avg_hr:
                hr_values = safe_get_value(heart_data, 'heartRateValues', default=[])
                if hr_values:
                    valid_rates = [val for val in hr_values if val and val > 0]
                    if valid_rates:
                        avg_hr = sum(valid_rates) // len(valid_rates)
            
            result['avg_heart_rate'] = avg_hr
            
        elif isinstance(heart_data, list) and len(heart_data) > 0:
            return parse_heart_data(heart_data[0])
    except Exception as e:
        logger.debug(f"Ошибка парсинга пульса: {e}")
    return result

def parse_sleep_data(sleep_data):
    """Парсинг данных сна"""
    result = {}
    try:
        if isinstance(sleep_data, dict):
            # Общая длительность сна
            sleep_duration = (safe_get_value(sleep_data, 'sleepTimeSeconds') or 
                            safe_get_value(sleep_data, 'totalSleepTimeSeconds') or 
                            safe_get_value(sleep_data, 'sleepTime'))
            
            if sleep_duration:
                result['sleep_duration_minutes'] = int(sleep_duration) // 60
            
            # Фазы сна
            sleep_levels = safe_get_value(sleep_data, 'sleepLevels', default=[])
            if sleep_levels:
                deep_seconds = sum(level.get('seconds', 0) for level in sleep_levels 
                                 if safe_get_value(level, 'activityLevel') == 'deep')
                light_seconds = sum(level.get('seconds', 0) for level in sleep_levels 
                                  if safe_get_value(level, 'activityLevel') == 'light')
                rem_seconds = sum(level.get('seconds', 0) for level in sleep_levels 
                                if safe_get_value(level, 'activityLevel') == 'rem')
                awake_seconds = sum(level.get('seconds', 0) for level in sleep_levels 
                                  if safe_get_value(level, 'activityLevel') == 'awake')
                
                result.update({
                    'sleep_deep_minutes': deep_seconds // 60,
                    'sleep_light_minutes': light_seconds // 60,
                    'sleep_rem_minutes': rem_seconds // 60,
                    'sleep_awake_minutes': awake_seconds // 60,
                })
            
            # Оценка сна
            sleep_score = (safe_get_value(sleep_data, 'overallSleepScore') or 
                          safe_get_value(sleep_data, 'sleepScore') or 
                          safe_get_value(sleep_data, 'score'))
            if sleep_score:
                result['sleep_score'] = sleep_score
                
        elif isinstance(sleep_data, list) and len(sleep_data) > 0:
            return parse_sleep_data(sleep_data[0])
    except Exception as e:
        logger.debug(f"Ошибка парсинга сна: {e}")
    return result

def parse_body_battery_data(battery_data):
    """Парсинг данных Body Battery"""
    result = {}
    try:
        battery_values = []
        
        if isinstance(battery_data, list):
            for item in battery_data:
                if isinstance(item, dict):
                    battery_val = (safe_get_value(item, 'charged') or 
                                 safe_get_value(item, 'batteryLevel') or 
                                 safe_get_value(item, 'value'))
                    if battery_val is not None:
                        battery_values.append(battery_val)
                elif isinstance(item, (int, float)):
                    battery_values.append(item)
        
        elif isinstance(battery_data, dict):
            values_array = safe_get_value(battery_data, 'charged', default=[])
            if values_array:
                battery_values.extend([v for v in values_array if v is not None])
            else:
                max_battery = safe_get_value(battery_data, 'maxBatteryLevel')
                if max_battery:
                    battery_values.append(max_battery)
        
        if battery_values:
            result.update({
                'body_battery_max': max(battery_values),
                'body_battery_min': min(battery_values)
            })
    except Exception as e:
        logger.debug(f"Ошибка парсинга Body Battery: {e}")
    return result

def parse_stress_data(stress_data):
    """Парсинг данных стресса"""
    result = {}
    try:
        if isinstance(stress_data, dict):
            result['stress_avg'] = safe_get_value(stress_data, 'averageStressLevel')
            result['stress_max'] = safe_get_value(stress_data, 'maxStressLevel')
            
            if not result['stress_avg']:
                stress_values_array = safe_get_value(stress_data, 'stressValuesArray', default=[])
                if stress_values_array:
                    valid_values = [val for val in stress_values_array if val is not None and val > 0]
                    if valid_values:
                        result['stress_avg'] = sum(valid_values) // len(valid_values)
                        result['stress_max'] = max(valid_values)
        
        elif isinstance(stress_data, list) and len(stress_data) > 0:
            stress_values = []
            for item in stress_data:
                if isinstance(item, dict):
                    stress_val = (safe_get_value(item, 'stressLevel') or 
                                safe_get_value(item, 'stress') or 
                                safe_get_value(item, 'value'))
                    if stress_val is not None and stress_val > 0:
                        stress_values.append(stress_val)
                elif isinstance(item, (int, float)) and item > 0:
                    stress_values.append(item)
            
            if stress_values:
                result['stress_avg'] = sum(stress_values) // len(stress_values)
                result['stress_max'] = max(stress_values)
    except Exception as e:
        logger.debug(f"Ошибка парсинга стресса: {e}")
    return result

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

def parse_readiness_data(readiness_data):
    """Парсинг данных готовности к тренировкам"""
    result = {}
    try:
        if isinstance(readiness_data, dict):
            result['training_readiness'] = safe_get_value(readiness_data, 'score')
        elif isinstance(readiness_data, list) and len(readiness_data) > 0:
            for item in readiness_data:
                if isinstance(item, dict):
                    score = safe_get_value(item, 'score')
                    if score:
                        result['training_readiness'] = score
                        break
    except Exception as e:
        logger.debug(f"Ошибка парсинга готовности: {e}")
    return result

# ================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ================================

garmin_connector = GarminConnector()