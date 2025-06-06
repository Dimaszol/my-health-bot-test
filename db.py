import sqlite3
import shutil
import os
import time
import re
import logging
from datetime import datetime
from vector_db import delete_document_from_vector_db, delete_all_chunks_by_user
from db_pool import get_db_connection, fetch_one, fetch_all, execute_query, insert_and_get_id
from locales import translations

DB_PATH = "users.db"
# Предопределенные безопасные SQL запросы (добавь в начало файла после импортов)
SAFE_UPDATE_QUERIES = {
    'name': "UPDATE users SET name = ?, last_updated = ? WHERE user_id = ?",
    'birth_year': "UPDATE users SET birth_year = ?, last_updated = ? WHERE user_id = ?",
    'gender': "UPDATE users SET gender = ?, last_updated = ? WHERE user_id = ?",
    'height_cm': "UPDATE users SET height_cm = ?, last_updated = ? WHERE user_id = ?",
    'weight_kg': "UPDATE users SET weight_kg = ?, last_updated = ? WHERE user_id = ?",
    'chronic_conditions': "UPDATE users SET chronic_conditions = ?, last_updated = ? WHERE user_id = ?",
    'medications': "UPDATE users SET medications = ?, last_updated = ? WHERE user_id = ?",
    'allergies': "UPDATE users SET allergies = ?, last_updated = ? WHERE user_id = ?",
    'smoking': "UPDATE users SET smoking = ?, last_updated = ? WHERE user_id = ?",
    'alcohol': "UPDATE users SET alcohol = ?, last_updated = ? WHERE user_id = ?",
    'physical_activity': "UPDATE users SET physical_activity = ?, last_updated = ? WHERE user_id = ?",
    'family_history': "UPDATE users SET family_history = ?, last_updated = ? WHERE user_id = ?",
    'language': "UPDATE users SET language = ?, last_updated = ? WHERE user_id = ?"
}

# Настройка логирования подозрительной активности
logging.basicConfig(
    filename='security.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def log_suspicious_activity(user_id, action, data):
    """Логирует подозрительную активность"""
    logging.warning(f"Подозрительная активность: user_id={user_id}, action={action}, data={str(data)[:100]}")

def detect_sql_injection(text):
    """Определение SQL инъекций и XSS атак"""
    if not isinstance(text, str):
        return False
    
    dangerous_patterns = [
        # SQL инъекции
        r"(union|select|insert|update|delete|drop|create|alter)\s",
        r";\s*(drop|delete|insert|update)",
        r"--\s*$",
        r"/\*.*\*/",
        r"'\s*(or|and)\s*'",
        r"'\s*=\s*'",
        
        # ✅ ДОБАВЛЯЕМ XSS защиту
        r"<script[^>]*>",
        r"</script>",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onload, etc.
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            return True
    return False

def validate_user_id(user_id):
    """Валидирует user_id"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Некорректный user_id")
    return user_id

def validate_string(value, max_length=500, field_name="поле"):
    """Валидирует строковые значения"""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} должно быть строкой")
    
    value = value.strip()
    if len(value) == 0:
        raise ValueError(f"{field_name} не может быть пустым")
    
    if len(value) > max_length:
        raise ValueError(f"{field_name} слишком длинное (максимум {max_length} символов)")
    
    # Проверка на SQL инъекции
    if detect_sql_injection(value):
        log_suspicious_activity("unknown", "sql_injection_attempt", value)
        raise ValueError("Обнаружена попытка SQL инъекции")
    
    return value

def validate_user_field(field: str, value):
    """Валидирует поле пользователя перед записью в БД"""
    # Проверяем, что поле разрешено
    if field not in ALLOWED_USER_FIELDS:
        raise ValueError(f"Поле '{field}' не разрешено для обновления")
    
    # Если значение None - это нормально для опциональных полей
    if value is None:
        return None
    
    # Валидация по типам полей
    if field == 'birth_year':
        if not isinstance(value, int):
            raise ValueError("Год рождения должен быть числом")
        current_year = datetime.now().year
        if value < 1900 or value > current_year:
            raise ValueError(f"Год рождения должен быть между 1900 и {current_year}")
    
    elif field in ['height_cm']:
        if not isinstance(value, int):
            raise ValueError("Рост должен быть целым числом")
        if value < 50 or value > 300:
            raise ValueError("Рост должен быть между 50 и 300 см")
    
    elif field == 'weight_kg':
        if not isinstance(value, (int, float)):
            raise ValueError("Вес должен быть числом")
        if value < 20 or value > 500:
            raise ValueError("Вес должен быть между 20 и 500 кг")
    
    elif field == 'language':
        if not isinstance(value, str):
            raise ValueError("Язык должен быть строкой")
        if value not in ['ru', 'uk', 'en']:
            raise ValueError("Неподдерживаемый язык")
    
    # Валидация длины строковых полей
    if isinstance(value, str):
        max_length = MAX_FIELD_LENGTHS.get(field, 500)
        return validate_string(value, max_length, field)
    
    return value

def get_connection():
    return sqlite3.connect(DB_PATH)

async def save_user(user_id: int, name: str, birth_year: int = None):
    """Асинхронное сохранение пользователя с пулом соединений"""
    # Валидация остается такой же
    user_id = validate_user_id(user_id)
    name = validate_string(name, 100, "имя")
    
    if birth_year is not None:
        if not isinstance(birth_year, int):
            raise ValueError("Год рождения должен быть числом")
        current_year = datetime.now().year
        if birth_year < 1900 or birth_year > current_year:
            raise ValueError(f"Некорректный год рождения: {birth_year}")

    # 🔄 НОВЫЙ КОД: Используем пул соединений
    # Получаем текущий язык, если он уже есть
    current_language_row = await fetch_one("SELECT language FROM users WHERE user_id = ?", (user_id,))
    current_language = current_language_row[0] if current_language_row else None

    await execute_query("""
        INSERT OR REPLACE INTO users (user_id, name, birth_year, language, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, birth_year, current_language, datetime.now()))

async def user_exists(user_id: int) -> bool:
    """Асинхронная проверка существования пользователя"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    return result is not None

async def get_user_name(user_id):
    """Асинхронное получение имени пользователя"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("SELECT name FROM users WHERE user_id=?", (user_id,))
    return result[0] if result else None

async def save_document(user_id: int, title: str, file_path: str, file_type: str, raw_text: str, summary: str, confirmed: bool = True):
    """Асинхронное сохранение документа"""
    # Валидация остается такой же
    user_id = validate_user_id(user_id)
    title = validate_string(title, 500, "заголовок")
    
    if not isinstance(file_type, str) or file_type not in ['pdf', 'image', 'note']:
        raise ValueError("Некорректный тип файла")
    
    if file_path and not file_path.startswith(f"files/{user_id}") and file_path != "memory_note":
        raise ValueError("Недопустимый путь к файлу")

    # 🔄 НОВЫЙ КОД: Используем пул
    document_id = await insert_and_get_id("""
        INSERT INTO documents (user_id, title, file_path, file_type, raw_text, summary, confirmed, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, title, file_path, file_type, raw_text, summary,
        int(confirmed), datetime.now()
    ))
    
    return document_id
    
async def get_document_by_id(document_id):
    """Асинхронное получение документа по ID"""
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("Некорректный document_id")
    
    row = await fetch_one("SELECT id, user_id, title, raw_text, file_path FROM documents WHERE id = ?", (document_id,))
    
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "title": row[2],
            "raw_text": row[3],
            "file_path": row[4]
        }
    return None

async def update_document_title(document_id: int, new_title: str):
    """Асинхронное обновление заголовка документа"""
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("Некорректный document_id")
    
    new_title = validate_string(new_title, 500, "новый заголовок")
    
    await execute_query("UPDATE documents SET title = ? WHERE id = ?", (new_title, document_id))

async def delete_document(document_id: int):
    """Асинхронное удаление документа"""
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("Некорректный document_id")
    
    from vector_db import delete_document_from_vector_db
    delete_document_from_vector_db(document_id)  # Это остается синхронным
    
    await execute_query("DELETE FROM documents WHERE id = ?", (document_id,))

async def get_documents_by_user(user_id: int):
    """Асинхронное получение документов пользователя"""
    user_id = validate_user_id(user_id)
    
    rows = await fetch_all("""
        SELECT id, title, uploaded_at, file_type FROM documents
        WHERE user_id = ? AND confirmed = 1
        ORDER BY uploaded_at DESC
    """, (user_id,))

    documents = []
    for row in rows:
        documents.append({
            "id": row[0],
            "title": row[1],
            "date": row[2],
            "file_type": row[3]
        })
    return documents

async def delete_user_completely(user_id: int):
    """Асинхронная версия delete_user_completely"""
    user_id = validate_user_id(user_id)
    
    # Получаем все документы пользователя
    doc_rows = await fetch_all("SELECT id FROM documents WHERE user_id = ?", (user_id,))
    doc_ids = [row[0] for row in doc_rows]

    # Удаляем из векторной базы
    delete_all_chunks_by_user(user_id)

    # Удаляем все данные пользователя
    await execute_query("DELETE FROM documents WHERE user_id = ?", (user_id,))
    await execute_query("DELETE FROM medications WHERE user_id = ?", (user_id,))
    await execute_query("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    await execute_query("DELETE FROM conversation_summary WHERE user_id = ?", (user_id,))
    await execute_query("DELETE FROM users WHERE user_id = ?", (user_id,))

    # Удаляем папку с файлами
    user_folder = f"files/{user_id}"
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
        print(f"📂 Удалена папка: {user_folder}")

async def update_document_confirmed(doc_id: int, confirmed: int):
    """Асинхронная версия update_document_confirmed"""
    if not isinstance(doc_id, int) or doc_id <= 0:
        raise ValueError("Некорректный doc_id")
    
    if confirmed not in [0, 1]:
        raise ValueError("confirmed должен быть 0 или 1")
    
    await execute_query("UPDATE documents SET confirmed = ? WHERE id = ?", (confirmed, doc_id))

async def save_message(user_id, role, message):
    """Асинхронное сохранение сообщения"""
    user_id = validate_user_id(user_id)
    
    if role not in ['user', 'bot', 'system']:
        raise ValueError("Некорректная роль сообщения")
    
    message = validate_string(message, 10000, "сообщение")
    
    await execute_query("""
        INSERT INTO chat_history (user_id, role, message, timestamp)
        VALUES (?, ?, ?, ?);
    """, (user_id, role, message, datetime.now()))

async def get_last_messages(user_id, limit=5):
    """Асинхронное получение последних сообщений"""
    user_id = validate_user_id(user_id)
    
    if not isinstance(limit, int) or limit <= 0 or limit > 100:
        raise ValueError("Лимит должен быть между 1 и 100")
    
    rows = await fetch_all("""
        SELECT role, message FROM chat_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))
    
    # Возвращаем в хронологическом порядке
    return rows[::-1]

# Получение последнего summary и до какого id оно покрывает
async def get_conversation_summary(user_id):
    """Асинхронное получение резюме разговора"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("""
        SELECT summary_text, last_message_id FROM conversation_summary
        WHERE user_id = ?
        ORDER BY updated_at DESC LIMIT 1
    """, (user_id,))
    
    return result if result else ("", 0)

async def get_messages_after(user_id, after_id, limit=50):
    """Асинхронное получение сообщений после определенного ID"""
    user_id = validate_user_id(user_id)
    
    if not isinstance(after_id, int) or after_id < 0:
        raise ValueError("Некорректный after_id")
    
    if not isinstance(limit, int) or limit <= 0 or limit > 1000:
        raise ValueError("Лимит должен быть между 1 и 1000")
    
    rows = await fetch_all("""
        SELECT id, role, message FROM chat_history
        WHERE user_id = ? AND id > ?
        ORDER BY id ASC LIMIT ?
    """, (user_id, after_id, limit))
    
    return rows

# Сохранение нового summary
async def save_conversation_summary(user_id, summary_text, last_message_id):
    """Асинхронное сохранение резюме разговора"""
    user_id = validate_user_id(user_id)
    summary_text = validate_string(summary_text, 5000, "текст резюме")
    
    if not isinstance(last_message_id, int) or last_message_id < 0:
        raise ValueError("Некорректный last_message_id")
    
    await execute_query("""
        INSERT INTO conversation_summary (user_id, summary_text, last_message_id)
        VALUES (?, ?, ?)
    """, (user_id, summary_text, last_message_id))

async def get_last_summary(user_id):
    """Асинхронное получение последнего резюме"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("""
        SELECT id, summary FROM documents
        WHERE user_id = ? AND confirmed = 1
        ORDER BY uploaded_at DESC LIMIT 1
    """, (user_id,))
    
    return (result[0], result[1]) if result else (None, "")

# ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ БЕЗОПАСНАЯ ФУНКЦИЯ update_user_field
async def update_user_field(user_id: int, field: str, value):
    """✅ БЕЗОПАСНАЯ версия обновления поля пользователя"""
    try:
        user_id = validate_user_id(user_id)
        validated_value = validate_user_field(field, value)
        
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: используем предопределенные запросы
        if field not in SAFE_UPDATE_QUERIES:
            print(f"❌ Поле '{field}' не разрешено для обновления")
            log_suspicious_activity(user_id, f"update_field_{field}", value)
            return False
        
        # Берем готовый безопасный SQL запрос (НЕ f-строка!)
        safe_query = SAFE_UPDATE_QUERIES[field]
        
        rowcount = await execute_query(safe_query, (validated_value, datetime.now(), user_id))
        
        if rowcount == 0:
            print(f"⚠️ Пользователь {user_id} не найден при обновлении поля {field}")
            return False
        
        print(f"✅ Обновлено поле {field} для пользователя {user_id}")
        return True
        
    except ValueError as e:
        print(f"❌ Ошибка валидации при обновлении поля {field}: {e}")
        log_suspicious_activity(user_id, f"update_field_{field}", value)
        return False
    except Exception as e:
        print(f"❌ Ошибка при обновлении поля {field} для пользователя {user_id}: {e}")
        return False

async def get_user_profile(user_id: int) -> dict:
    """Асинхронное получение профиля пользователя"""
    user_id = validate_user_id(user_id)
    
    row = await fetch_one("""
        SELECT name, birth_year, gender, height_cm, weight_kg, chronic_conditions,
               medications, allergies, smoking, alcohol, physical_activity, family_history
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    if not row:
        return {}

    fields = [
        "name", "birth_year", "gender", "height_cm", "weight_kg",
        "chronic_conditions", "medications", "allergies",
        "smoking", "alcohol", "physical_activity", "family_history"
    ]
    return dict(zip(fields, row))

async def get_medications(user_id: int):
    """Асинхронное получение лекарств пользователя"""
    user_id = validate_user_id(user_id)
    
    rows = await fetch_all("SELECT name, time, label FROM medications WHERE user_id = ? ORDER BY time", (user_id,))
    return [{"name": row[0], "time": row[1], "label": row[2]} for row in rows]

async def replace_medications(user_id: int, new_list: list):
    """Асинхронная замена списка лекарств"""
    user_id = validate_user_id(user_id)
    
    if not isinstance(new_list, list):
        raise ValueError("new_list должен быть списком")
    
    # Валидируем каждый элемент списка
    for item in new_list:
        if not isinstance(item, dict):
            raise ValueError("Каждый элемент должен быть словарем")
        
        required_keys = {"name", "time", "label"}
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Отсутствуют обязательные ключи: {required_keys}")
        
        validate_string(item["name"], 200, "название лекарства")
        validate_string(item["time"], 10, "время приема")
        validate_string(item["label"], 100, "метка времени")
    
    # 🔄 ПРАВИЛЬНЫЙ КОД: Используем функции из db_pool
    # Сначала удаляем старые лекарства
    await execute_query("DELETE FROM medications WHERE user_id = ?", (user_id,))
    
    # Затем добавляем новые
    for item in new_list:
        await execute_query(
            "INSERT INTO medications (user_id, name, time, label) VALUES (?, ?, ?, ?)",
            (user_id, item["name"], item["time"], item["label"])
        )

async def get_user_medications_text(user_id: int) -> str:
    """Асинхронное получение текста лекарств пользователя"""
    user_id = validate_user_id(user_id)
    
    rows = await fetch_all("SELECT name FROM medications WHERE user_id = ? ORDER BY time", (user_id,))
    return ", ".join([row[0] for row in rows])

async def format_medications_schedule(user_id: int) -> str:
    """Асинхронное форматирование расписания лекарств"""
    user_id = validate_user_id(user_id)
    
    rows = await fetch_all("SELECT name, time, label FROM medications WHERE user_id = ? ORDER BY time", (user_id,))
    
    if not rows:
        lang = await get_user_language(user_id)  # Теперь тоже асинхронная!
        return t("schedule_empty", lang)
    
    return "\n".join([f"{row[1]} — {row[0]} ({row[2]})" for row in rows])

async def set_user_language(user_id: int, language: str):
    """Асинхронная установка языка пользователя"""
    user_id = validate_user_id(user_id)
    
    if language not in ['ru', 'uk', 'en']:
        raise ValueError("Неподдерживаемый язык")
    
    await execute_query("""
        INSERT INTO users (user_id, language, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language=excluded.language
    """, (user_id, language, datetime.now()))

def t(key: str, lang: str = "ru", **kwargs) -> str:
    return translations.get(lang, {}).get(key, key).format(**kwargs)

async def get_user_language(user_id: int) -> str:
    """Асинхронное получение языка пользователя"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("SELECT language FROM users WHERE user_id = ?", (user_id,))
    return result[0] if result and result[0] else "ru"

async def is_fully_registered(user_id: int) -> bool:
    """Асинхронная проверка полной регистрации"""
    user_id = validate_user_id(user_id)
    
    result = await fetch_one("SELECT name FROM users WHERE user_id = ?", (user_id,))
    return result is not None and result[0] not in (None, "")

def get_all_values_for_key(key: str) -> list[str]:
    key = validate_string(key, 100, "ключ")
    return [lang_data.get(key) for lang_data in translations.values() if key in lang_data]