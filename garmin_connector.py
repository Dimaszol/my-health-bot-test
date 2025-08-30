# garmin_connector.py - Модуль для работы с Garmin Connect API

import os
import json
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Any
from cryptography.fernet import Fernet
import psycopg2
from psycopg2.extras import RealDictCursor
from garminconnect import Garmin
from dotenv import load_dotenv

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
        self.db_url = os.getenv("DATABASE_URL")
        self._api_cache = {}  # Кеш подключений API
        
    def get_db_connection(self):
        """Получить подключение к БД"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    async def save_garmin_connection(self, user_id: int, email: str, password: str, 
                                   notification_time: str = "07:00", timezone_offset: int = 0,
                                   timezone_name: str = "UTC") -> bool:
        """Сохранить данные подключения к Garmin"""
        try:
            encrypted_email = encrypt_data(email)
            encrypted_password = encrypt_data(password)
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Используем ON CONFLICT для обновления существующих записей
            cursor.execute("""
                INSERT INTO garmin_connections 
                (user_id, garmin_email, garmin_password, notification_time, 
                 timezone_offset, timezone_name, is_active, sync_errors)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, 0)
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
            """, (user_id, encrypted_email, encrypted_password, notification_time,
                  timezone_offset, timezone_name))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Garmin подключение сохранено для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения Garmin подключения: {e}")
            return False

    async def get_garmin_connection(self, user_id: int) -> Optional[Dict]:
        """Получить данные подключения к Garmin"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM garmin_connections 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Расшифровываем данные
                result = dict(result)
                result['garmin_email'] = decrypt_data(result['garmin_email'])
                result['garmin_password'] = decrypt_data(result['garmin_password'])
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения Garmin подключения: {e}")
            return None

    async def test_garmin_connection(self, email: str, password: str) -> tuple[bool, str]:
        """Проверить подключение к Garmin"""
        try:
            # Пробуем подключиться к Garmin
            api = Garmin(email, password)
            await asyncio.get_event_loop().run_in_executor(None, api.login)
            
            # Пробуем получить базовую информацию
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
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE garmin_connections 
                SET is_active = FALSE, updated_at = NOW()
                WHERE user_id = %s
            """, (user_id,))
            
            conn.commit()
            conn.close()
            
            # Очищаем кеш
            if user_id in self._api_cache:
                del self._api_cache[user_id]
                
            logger.info(f"✅ Garmin отключен для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отключения Garmin: {e}")
            return False

    async def get_garmin_api(self, user_id: int) -> Optional[Garmin]:
        """Получить API подключение к Garmin с кешированием"""
        try:
            # Проверяем кеш
            if user_id in self._api_cache:
                return self._api_cache[user_id]
            
            # Получаем данные подключения
            connection = await self.get_garmin_connection(user_id)
            if not connection:
                return None
            
            # Создаем API подключение
            api = Garmin(connection['garmin_email'], connection['garmin_password'])
            
            # Логинимся
            await asyncio.get_event_loop().run_in_executor(None, api.login)
            
            # Кешируем на 1 час
            self._api_cache[user_id] = api
            
            return api
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания Garmin API для {user_id}: {e}")
            
            # Увеличиваем счетчик ошибок
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE garmin_connections 
                    SET sync_errors = sync_errors + 1, updated_at = NOW()
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
                conn.close()
            except:
                pass
                
            return None

    async def collect_daily_data(self, user_id: int, target_date: date = None) -> Optional[Dict]:
        """Собрать все данные за день"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # Вчерашний день
            
        try:
            api = await self.get_garmin_api(user_id)
            if not api:
                logger.warning(f"Не удалось получить Garmin API для {user_id}")
                return None
            
            logger.info(f"📊 Собираю данные Garmin за {target_date} для пользователя {user_id}")
            
            # Собираем данные параллельно
            tasks = []
            loop = asyncio.get_event_loop()
            
            # Базовая активность
            tasks.append(loop.run_in_executor(None, lambda: api.get_steps_data(target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: api.get_heart_rates(target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: api.get_sleep_data(target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: api.get_body_battery(target_date.isoformat(), target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: api.get_stress_data(target_date.isoformat())))
            
            # Дополнительные данные (могут не поддерживаться всеми устройствами)
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_spo2_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_respiration_data, target_date.isoformat())))
            tasks.append(loop.run_in_executor(None, lambda: safe_api_call(api.get_training_readiness, target_date.isoformat())))
            
            # Выполняем все запросы
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            steps_data, heart_data, sleep_data, battery_data, stress_data, spo2_data, respiration_data, readiness_data = results
            
            # Формируем структурированные данные
            daily_data = {
                'user_id': user_id,
                'data_date': target_date,
                'sync_timestamp': datetime.now()
            }
            
            # Шаги и активность
            if not isinstance(steps_data, Exception) and steps_data:
                daily_data.update({
                    'steps': steps_data.get('totalSteps', 0),
                    'calories': steps_data.get('totalKilocalories', 0),
                    'distance_meters': int(steps_data.get('totalDistanceMeters', 0)),
                    'floors_climbed': steps_data.get('floorsAscended', 0)
                })
            
            # Пульс
            if not isinstance(heart_data, Exception) and heart_data:
                daily_data.update({
                    'resting_heart_rate': heart_data.get('restingHeartRate'),
                    'avg_heart_rate': calculate_avg_heart_rate(heart_data),
                    'max_heart_rate': heart_data.get('maxHeartRate'),
                })
            
            # Сон
            if not isinstance(sleep_data, Exception) and sleep_data:
                daily_data.update(parse_sleep_data(sleep_data))
            
            # Body Battery
            if not isinstance(battery_data, Exception) and battery_data and len(battery_data) > 0:
                battery_values = [item.get('charged', 0) for item in battery_data if item.get('charged')]
                if battery_values:
                    daily_data.update({
                        'body_battery_max': max(battery_values),
                        'body_battery_min': min(battery_values)
                    })
            
            # Стресс
            if not isinstance(stress_data, Exception) and stress_data:
                daily_data.update(parse_stress_data(stress_data))
            
            # Дополнительные данные
            if not isinstance(spo2_data, Exception) and spo2_data:
                daily_data['spo2_avg'] = spo2_data.get('averageSpO2')
            
            if not isinstance(respiration_data, Exception) and respiration_data:
                daily_data['respiration_avg'] = respiration_data.get('avgRespirationValue')
            
            if not isinstance(readiness_data, Exception) and readiness_data:
                daily_data['training_readiness'] = readiness_data.get('score')
            
            logger.info(f"✅ Собраны данные Garmin: {len([k for k,v in daily_data.items() if v is not None])} полей")
            return daily_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных Garmin для {user_id}: {e}")
            return None

    async def save_daily_data(self, daily_data: Dict) -> bool:
        """Сохранить ежедневные данные в БД"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Подготавливаем данные для вставки
            fields = []
            values = []
            placeholders = []
            
            for key, value in daily_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
                    placeholders.append('%s')
            
            # Формируем ON CONFLICT для обновления
            update_fields = ', '.join([f"{field} = EXCLUDED.{field}" for field in fields if field not in ['user_id', 'data_date']])
            
            query = f"""
                INSERT INTO garmin_daily_data ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (user_id, data_date)
                DO UPDATE SET {update_fields}
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Данные Garmin сохранены в БД для пользователя {daily_data['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных Garmin: {e}")
            return False

# ================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ================================

def safe_api_call(func, *args, **kwargs):
    """Безопасный вызов API функции"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.debug(f"API вызов не удался: {func.__name__}: {e}")
        return None

def calculate_avg_heart_rate(heart_data):
    """Вычислить средний пульс из данных"""
    try:
        if isinstance(heart_data, list):
            rates = [item.get('heartRate') for item in heart_data if item.get('heartRate')]
            return sum(rates) // len(rates) if rates else None
        return heart_data.get('averageHeartRate')
    except:
        return None

def parse_sleep_data(sleep_data):
    """Парсинг данных сна"""
    try:
        result = {}
        
        if isinstance(sleep_data, dict):
            # Общая длительность сна
            result['sleep_duration_minutes'] = sleep_data.get('sleepTimeSeconds', 0) // 60
            
            # Фазы сна
            sleep_levels = sleep_data.get('sleepLevels', [])
            deep_seconds = sum(level.get('seconds', 0) for level in sleep_levels if level.get('activityLevel') == 'deep')
            light_seconds = sum(level.get('seconds', 0) for level in sleep_levels if level.get('activityLevel') == 'light')
            rem_seconds = sum(level.get('seconds', 0) for level in sleep_levels if level.get('activityLevel') == 'rem')
            awake_seconds = sum(level.get('seconds', 0) for level in sleep_levels if level.get('activityLevel') == 'awake')
            
            result.update({
                'sleep_deep_minutes': deep_seconds // 60,
                'sleep_light_minutes': light_seconds // 60,
                'sleep_rem_minutes': rem_seconds // 60,
                'sleep_awake_minutes': awake_seconds // 60,
            })
            
            # Оценка сна
            result['sleep_score'] = sleep_data.get('overallSleepScore')
        
        return result
    except Exception as e:
        logger.debug(f"Ошибка парсинга сна: {e}")
        return {}

def parse_stress_data(stress_data):
    """Парсинг данных стресса"""
    try:
        result = {}
        
        if isinstance(stress_data, list) and len(stress_data) > 0:
            stress_values = [item.get('stressLevel') for item in stress_data if item.get('stressLevel') is not None]
            if stress_values:
                result['stress_avg'] = sum(stress_values) // len(stress_values)
                result['stress_max'] = max(stress_values)
        
        return result
    except:
        return {}

# ================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ================================

garmin_connector = GarminConnector()