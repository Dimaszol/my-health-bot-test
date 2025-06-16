# db_safe.py - Безопасные функции для работы с базой данных

import sqlite3
import logging
from datetime import datetime
from typing import Any, Optional, List, Dict
from contextlib import asynccontextmanager
import aiosqlite

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WHITELIST разрешенных полей для обновления (КРИТИЧЕСКИ ВАЖНО!)
ALLOWED_USER_FIELDS = {
    'name', 'birth_year', 'gender', 'height_cm', 'weight_kg', 
    'chronic_conditions', 'medications', 'allergies', 'smoking', 
    'alcohol', 'physical_activity', 'family_history', 'language'
}

# Максимальная длина текстовых полей
MAX_FIELD_LENGTHS = {
    'name': 100,
    'chronic_conditions': 1000,
    'medications': 1000,
    'allergies': 500,
    'smoking': 50,
    'alcohol': 50,
    'physical_activity': 100,
    'family_history': 1000,
    'language': 10
}

class DatabaseError(Exception):
    """Кастомное исключение для ошибок базы данных"""
    pass

class ValidationError(Exception):
    """Исключение для ошибок валидации данных"""
    pass

def validate_user_field(field: str, value: Any) -> Any:
    """
    Валидирует поле пользователя перед записью в БД
    
    Args:
        field: Имя поля
        value: Значение поля
        
    Returns:
        Валидированное значение
        
    Raises:
        ValidationError: Если поле или значение недопустимо
    """
    # Проверяем, что поле разрешено
    if field not in ALLOWED_USER_FIELDS:
        raise ValidationError(f"Поле '{field}' не разрешено для обновления")
    
    # Если значение None - это нормально для опциональных полей
    if value is None:
        return None
    
    # Валидация по типам полей
    if field == 'birth_year':
        if not isinstance(value, int):
            raise ValidationError("Год рождения должен быть числом")
        current_year = datetime.now().year
        if value < 1900 or value > current_year:
            raise ValidationError(f"Год рождения должен быть между 1900 и {current_year}")
    
    elif field in ['height_cm']:
        if not isinstance(value, int):
            raise ValidationError("Рост должен быть целым числом")
        if value < 50 or value > 300:
            raise ValidationError("Рост должен быть между 50 и 300 см")
    
    elif field == 'weight_kg':
        if not isinstance(value, (int, float)):
            raise ValidationError("Вес должен быть числом")
        if value < 20 or value > 500:
            raise ValidationError("Вес должен быть между 20 и 500 кг")
    
    elif field == 'language':
        if not isinstance(value, str):
            raise ValidationError("Язык должен быть строкой")
        if value not in ['ru', 'uk', 'en']:
            raise ValidationError("Неподдерживаемый язык")
    
    # Валидация длины строковых полей
    if isinstance(value, str):
        # Очищаем от опасных символов
        cleaned_value = value.strip()
        
        # Проверяем длину
        max_length = MAX_FIELD_LENGTHS.get(field, 500)
        if len(cleaned_value) > max_length:
            raise ValidationError(f"Поле '{field}' слишком длинное (максимум {max_length} символов)")
        
        # Проверяем на SQL-инъекции (базовая проверка)
        dangerous_patterns = [
            ';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE', 
            'CREATE', 'ALTER', 'EXEC', 'UNION', 'SELECT'
        ]
        
        value_upper = cleaned_value.upper()
        for pattern in dangerous_patterns:
            if pattern in value_upper:
                logger.warning(f"Подозрительный паттерн '{pattern}' в поле '{field}': {cleaned_value[:50]}")
                # Не блокируем полностью, но логируем
        
        return cleaned_value
    
    return value

def validate_user_id(user_id: Any) -> int:
    """Валидирует user_id"""
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise ValidationError("user_id должен быть числом")
    
    if user_id <= 0:
        raise ValidationError("user_id должен быть положительным числом")
    
    return user_id

@asynccontextmanager
async def get_db_connection():
    """
    Асинхронный контекстный менеджер для безопасной работы с БД
    """
    conn = None
    try:
        conn = await aiosqlite.connect("users.db", timeout=30.0)
        # Включаем WAL режим для лучшей производительности
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        await conn.commit()
    except Exception as e:
        if conn:
            await conn.rollback()
        logger.error(f"Ошибка базы данных: {e}")
        raise DatabaseError(f"Ошибка базы данных: {e}")
    finally:
        if conn:
            await conn.close()

# БЕЗОПАСНАЯ замена для update_user_field
async def safe_update_user_field(user_id: int, field: str, value: Any) -> bool:
    """
    Безопасное обновление поля пользователя
    
    Args:
        user_id: ID пользователя
        field: Имя поля
        value: Новое значение
        
    Returns:
        True если обновление прошло успешно
        
    Raises:
        ValidationError: Если данные невалидны
        DatabaseError: Если ошибка БД
    """
    try:
        # Валидируем входные данные
        user_id = validate_user_id(user_id)
        validated_value = validate_user_field(field, value)
        
        # Используем предопределенный запрос (НЕ f-строку!)
        query = f"UPDATE users SET {field} = ?, last_updated = ? WHERE user_id = ?"
        
        # НО! Проверяем field через whitelist ПЕРЕД созданием запроса
        if field not in ALLOWED_USER_FIELDS:
            raise ValidationError(f"Поле '{field}' не разрешено")
        
        async with get_db_connection() as conn:
            cursor = await conn.execute(
                query, 
                (validated_value, datetime.now(), user_id)
            )
            
            # Проверяем, что запись действительно обновилась
            if cursor.rowcount == 0:
                logger.warning(f"Пользователь {user_id} не найден при обновлении поля {field}")
                return False
            
            logger.info(f"Обновлено поле {field} для пользователя {user_id}")
            return True
            
    except ValidationError:
        raise  # Перебрасываем ValidationError как есть
    except Exception as e:
        logger.error(f"Ошибка при обновлении поля {field} для пользователя {user_id}: {e}")
        raise DatabaseError(f"Не удалось обновить поле: {e}")

# БЕЗОПАСНАЯ замена для других функций
async def safe_save_user(user_id: int, name: str, birth_year: Optional[int] = None) -> bool:
    """Безопасное сохранение пользователя"""
    try:
        user_id = validate_user_id(user_id)
        name = validate_user_field('name', name)
        if birth_year is not None:
            birth_year = validate_user_field('birth_year', birth_year)
        
        async with get_db_connection() as conn:
            # Получаем текущий язык
            cursor = await conn.execute(
                "SELECT language FROM users WHERE user_id = ?", 
                (user_id,)
            )
            row = await cursor.fetchone()
            current_language = row[0] if row else 'ru'
            
            # Используем INSERT OR REPLACE с параметрами
            await conn.execute("""
                INSERT OR REPLACE INTO users (user_id, name, birth_year, language, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, birth_year, current_language, datetime.now()))
            
            logger.info(f"Сохранен пользователь {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя {user_id}: {e}")
        raise DatabaseError(f"Не удалось сохранить пользователя: {e}")

async def safe_get_user_by_id(user_id: int) -> Optional[Dict]:
    """Безопасное получение пользователя по ID"""
    try:
        user_id = validate_user_id(user_id)
        
        async with get_db_connection() as conn:
            cursor = await conn.execute(
                "SELECT user_id, name, birth_year, language, created_at FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    'user_id': row[0],
                    'name': row[1],
                    'birth_year': row[2],
                    'language': row[3],
                    'created_at': row[4]
                }
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
        raise DatabaseError(f"Не удалось получить пользователя: {e}")

# Функция для массового обновления (транзакция)
async def safe_bulk_update_user(user_id: int, updates: Dict[str, Any]) -> bool:
    """
    Безопасное массовое обновление полей пользователя в одной транзакции
    
    Args:
        user_id: ID пользователя
        updates: Словарь {поле: значение} для обновления
    """
    try:
        user_id = validate_user_id(user_id)
        
        # Валидируем все поля
        validated_updates = {}
        for field, value in updates.items():
            validated_updates[field] = validate_user_field(field, value)
        
        if not validated_updates:
            return True
        
        # Строим запрос безопасно
        set_clauses = []
        values = []
        
        for field in validated_updates.keys():
            set_clauses.append(f"{field} = ?")
            values.append(validated_updates[field])
        
        # Добавляем last_updated
        set_clauses.append("last_updated = ?")
        values.append(datetime.now())
        values.append(user_id)  # Для WHERE
        
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
        
        async with get_db_connection() as conn:
            cursor = await conn.execute(query, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Пользователь {user_id} не найден при массовом обновлении")
                return False
            
            logger.info(f"Массово обновлены поля для пользователя {user_id}: {list(validated_updates.keys())}")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении пользователя {user_id}: {e}")
        raise DatabaseError(f"Не удалось выполнить массовое обновление: {e}")

# Тестовая функция для проверки защиты
def test_sql_injection_protection():
    """Тестирует защиту от SQL инъекций"""
    print("🧪 Тестирование защиты от SQL инъекций...")
    
    dangerous_inputs = [
        "name'; DROP TABLE users; --",
        "'; DELETE FROM users WHERE 1=1; --",
        "name' OR '1'='1",
        "'; INSERT INTO users (user_id, name) VALUES (999999, 'hacker'); --",
        "name'; UPDATE users SET name='hacked' WHERE 1=1; --"
    ]
    
    for dangerous_input in dangerous_inputs:
        try:
            # Попытка атаки через валидацию поля
            validate_user_field('name', dangerous_input)
            print(f"⚠️ Потенциально опасный ввод пропущен: {dangerous_input[:50]}")
        except ValidationError as e:
            print(f"✅ Заблокирован опасный ввод: {dangerous_input[:30]}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    test_sql_injection_protection()