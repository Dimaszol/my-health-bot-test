# db_postgresql.py - Подключение к PostgreSQL для медицинского бота

import os
import asyncio
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from error_handler import log_error_with_context

# 🔗 ПУЛ ПОДКЛЮЧЕНИЙ
db_pool: Optional[asyncpg.Pool] = None

async def get_db_connection():
    """Получить соединение с базой даннфх"""
    global db_pool
    if db_pool is None:
        raise Exception("❌ База данных не инициализирована")
    return await db_pool.acquire()

async def release_db_connection(connection):
    """Освободить соединение"""
    global db_pool
    if db_pool:
        await db_pool.release(connection)

async def initialize_db_pool(max_connections: int = 10):
    """Инициализация пула соединений PostgreSQL"""
    global db_pool
    
    # 🔗 Получаем URL базы данных
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # 📝 Если нет DATABASE_URL, собираем из отдельных переменных
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "medical_bot")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        print("🔗 Подключение к PostgreSQL...")
        db_pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=max_connections,
            command_timeout=60
        )
        
        # ✅ Тестируем подключение
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT version()")
            print(f"✅ PostgreSQL подключен: {result[:50]}...")
        
        # 🏗️ Создаем таблицы
        await create_tables()
        print("🗄️ Структура базы данных готова")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        log_error_with_context(e, {"action": "db_connection"})
        raise

async def close_db_pool():
    """Закрытие пула соединений"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("🔗 Пул PostgreSQL закрыт")

async def create_tables():
    """Создание всех таблиц медицинского бота"""
    
    tables_sql = """
    -- 👤 ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        birth_year INTEGER,
        gender TEXT,
        height_cm INTEGER,
        weight_kg REAL,
        chronic_conditions TEXT,
        medications TEXT,
        allergies TEXT,
        smoking TEXT,
        alcohol TEXT,
        physical_activity TEXT,
        family_history TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        language TEXT DEFAULT 'ru'
    );

    -- 💬 ИСТОРИЯ ЧАТА
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 📄 ДОКУМЕНТЫ
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        title TEXT,
        file_path TEXT,
        file_type TEXT,
        raw_text TEXT,
        summary TEXT,
        confirmed BOOLEAN DEFAULT FALSE,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vector_id TEXT
    );

    -- 💊 ЛЕКАРСТВА
    CREATE TABLE IF NOT EXISTS medications (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        time TEXT,
        label TEXT
    );

    -- 📊 ЛИМИТЫ ПОЛЬЗОВАТЕЛЕЙ
    CREATE TABLE IF NOT EXISTS user_limits (
        user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
        documents_left INTEGER DEFAULT 3,
        gpt4o_queries_left INTEGER DEFAULT 5,
        subscription_type TEXT DEFAULT 'free',
        subscription_expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 💳 ТРАНЗАКЦИИ
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        stripe_session_id TEXT UNIQUE,
        amount_usd REAL,
        package_type TEXT,
        status TEXT DEFAULT 'pending',
        payment_method TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        package_id TEXT,
        documents_granted INTEGER DEFAULT 0,
        queries_granted INTEGER DEFAULT 0
    );

    -- 📦 ПАКЕТЫ ПОДПИСОК
    CREATE TABLE IF NOT EXISTS subscription_packages (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price_usd REAL NOT NULL,
        documents_included INTEGER DEFAULT 0,
        gpt4o_queries_included INTEGER DEFAULT 0,
        type TEXT DEFAULT 'one_time',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 🔄 ПОДПИСКИ ПОЛЬЗОВАТЕЛЕЙ
    CREATE TABLE IF NOT EXISTS user_subscriptions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        stripe_subscription_id TEXT UNIQUE,
        package_id TEXT REFERENCES subscription_packages(id),
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cancelled_at TIMESTAMP
    );

    -- 🧠 РЕЗЮМЕ РАЗГОВОРОВ
    CREATE TABLE IF NOT EXISTS conversation_summary (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        summary_text TEXT,
        last_message_id INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 📚 ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
    CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
    CREATE INDEX IF NOT EXISTS idx_medications_user_id ON medications(user_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
    """
    
    conn = await get_db_connection()
    try:
        await conn.execute(tables_sql)
        print("✅ Все таблицы созданы")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        log_error_with_context(e, {"action": "create_tables"})
        raise
    finally:
        await release_db_connection(conn)

# 👤 ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
async def get_user(user_id: int) -> Optional[Dict]:
    """Получить данные пользователя"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None
    except Exception as e:
        log_error_with_context(e, {"function": "get_user", "user_id": user_id})
        return None
    finally:
        await release_db_connection(conn)

async def create_user(user_id: int, name: str = "") -> bool:
    """Создать нового пользователя"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO users (user_id, name) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            user_id, name or None  # ← Пустое имя = NULL
        )
        
        # Создаем лимиты для нового пользователя
        await conn.execute(
            "INSERT INTO user_limits (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
            user_id
        )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "create_user", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def update_user_profile(user_id: int, field: str, value: Any) -> bool:
    """Обновить поле в профиле пользователя"""
    conn = await get_db_connection()
    try:
        query = f"UPDATE users SET {field} = $1, last_updated = CURRENT_TIMESTAMP WHERE user_id = $2"
        await conn.execute(query, value, user_id)
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "update_user_profile", "user_id": user_id, "field": field})
        return False
    finally:
        await release_db_connection(conn)

# 📄 ФУНКЦИИ ДЛЯ РАБОТЫ С ДОКУМЕНТАМИ
async def save_document(user_id: int, title: str, file_path: str, file_type: str, 
                       raw_text: str, summary: str, confirmed: bool = True, vector_id: str = None) -> Optional[int]:
    """Сохранить документ (исправленная версия)"""
    conn = await get_db_connection()
    try:
        doc_id = await conn.fetchval(
            """INSERT INTO documents (user_id, title, file_path, file_type, raw_text, summary, confirmed, vector_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
            user_id, title, file_path, file_type, raw_text, summary, confirmed, vector_id
        )
        return doc_id
    except Exception as e:
        log_error_with_context(e, {"function": "save_document", "user_id": user_id})
        return None
    finally:
        await release_db_connection(conn)

async def get_user_documents(user_id: int, limit: int = 10) -> List[Dict]:
    """Получить документы пользователя"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """SELECT id, title, file_type, uploaded_at as date 
               FROM documents 
               WHERE user_id = $1 
               ORDER BY uploaded_at DESC 
               LIMIT $2""",
            user_id, limit
        )
        return [dict(row) for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_documents", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

# 💊 ФУНКЦИИ ДЛЯ РАБОТЫ С ЛЕКАРСТВАМИ
async def get_user_medications(user_id: int) -> List[Dict]:
    """Получить лекарства пользователя"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT * FROM medications WHERE user_id = $1 ORDER BY time",
            user_id
        )
        return [dict(row) for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_medications", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

async def update_user_medications(user_id: int, medications: List[Dict]) -> bool:
    """Обновить список лекарств пользователя"""
    conn = await get_db_connection()
    try:
        # 🗑️ Удаляем старые лекарства
        await conn.execute("DELETE FROM medications WHERE user_id = $1", user_id)
        
        # ➕ Добавляем новые
        for med in medications:
            await conn.execute(
                "INSERT INTO medications (user_id, name, time, label) VALUES ($1, $2, $3, $4)",
                user_id, med['name'], med['time'], med['label']
            )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "update_user_medications", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

# 💳 ФУНКЦИИ ДЛЯ РАБОТЫ С ЛИМИТАМИ И ПОДПИСКАМИ
async def get_user_limits(user_id: int) -> Dict:
    """Получить лимиты пользователя"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM user_limits WHERE user_id = $1", user_id)
        return dict(row) if row else {
            "documents_left": 3,
            "gpt4o_queries_left": 5,
            "subscription_type": "free"
        }
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_limits", "user_id": user_id})
        return {"documents_left": 0, "gpt4o_queries_left": 0, "subscription_type": "free"}
    finally:
        await release_db_connection(conn)

async def decrease_user_limit(user_id: int, limit_type: str, amount: int = 1) -> bool:
    """Уменьшить лимит пользователя"""
    conn = await get_db_connection()
    try:
        if limit_type == "documents":
            field = "documents_left"
        elif limit_type == "gpt4o_queries":
            field = "gpt4o_queries_left"
        else:
            return False
            
        await conn.execute(
            f"UPDATE user_limits SET {field} = GREATEST({field} - $1, 0) WHERE user_id = $2",
            amount, user_id
        )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "decrease_user_limit", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_db_stats() -> Dict:
    """Получает статистику базы данных"""
    import logging
    logger = logging.getLogger(__name__)  # ✅ ДОБАВИЛИ
    
    global db_pool
    if not db_pool:
        return {"status": "error", "message": "DB pool not initialized"}
    
    conn = await get_db_connection()
    try:
        # Статистика подключений
        pool_stats = {
            "pool_size": db_pool.get_size(),
            "pool_min_size": db_pool.get_min_size(),
            "pool_max_size": db_pool.get_max_size(),
            "pool_idle": db_pool.get_idle_size(),
        }
        
        # Статистика таблиц
        tables_stats = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables 
            ORDER BY n_tup_ins DESC
            LIMIT 10
        """)
        
        # Общая статистика БД
        db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
        db_version = await conn.fetchval("SELECT version()")
        
        return {
            "status": "healthy",
            "database_size": db_size,
            "database_version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
            "pool_stats": pool_stats,
            "tables_count": len(tables_stats),
            "tables_stats": [dict(row) for row in tables_stats]
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики БД: {e}")  # ✅ ЗАМЕНИЛИ НА print
        return {"status": "error", "message": str(e)}
    finally:
        await release_db_connection(conn)

async def db_health_check() -> bool:
    """Проверяет здоровье базы данных"""
    global db_pool
    if not db_pool:
        return False
    
    conn = await get_db_connection()
    try:
        # Простой тест подключения
        result = await conn.fetchval("SELECT 1")
        return result == 1
    except Exception as e:
        print(f"❌ Health check failed: {e}")  # ✅ ЗАМЕНИЛИ НА print
        return False
    finally:
        await release_db_connection(conn)

# 📄 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДОКУМЕНТАМИ
async def get_document_by_id(document_id: int) -> Optional[Dict]:
    """Получить документ по ID"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM documents WHERE id = $1", document_id)
        return dict(row) if row else None
    except Exception as e:
        log_error_with_context(e, {"function": "get_document_by_id", "document_id": document_id})
        return None
    finally:
        await release_db_connection(conn)

async def update_document_title(document_id: int, new_title: str) -> bool:
    """Обновить название документа"""
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "UPDATE documents SET title = $1 WHERE id = $2",
            new_title, document_id
        )
        return result != "UPDATE 0"
    except Exception as e:
        log_error_with_context(e, {"function": "update_document_title", "document_id": document_id})
        return False
    finally:
        await release_db_connection(conn)

async def delete_document(document_id: int) -> bool:
    """Удалить документ"""
    conn = await get_db_connection()
    try:
        result = await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
        return result != "DELETE 0"
    except Exception as e:
        log_error_with_context(e, {"function": "delete_document", "document_id": document_id})
        return False
    finally:
        await release_db_connection(conn)

# 💬 ФУНКЦИИ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ
async def save_message(user_id: int, role: str, message: str) -> bool:
    """Сохранить сообщение в историю чата"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES ($1, $2, $3)",
            user_id, role, message
        )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "save_message", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_last_messages(user_id: int, limit: int = 5) -> List[tuple]:
    """Получить последние сообщения пользователя (совместимость - возврат tuples)"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """SELECT role, message FROM chat_history 
               WHERE user_id = $1 
               ORDER BY id DESC 
               LIMIT $2""",
            user_id, limit
        )
        # Возвращаем в хронологическом порядке как list of tuples
        return [(row['role'], row['message']) for row in reversed(rows)]
    except Exception as e:
        log_error_with_context(e, {"function": "get_last_messages", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

# 📝 ФУНКЦИИ ДЛЯ РАБОТЫ С РЕЗЮМЕ РАЗГОВОРОВ
async def get_conversation_summary(user_id: int) -> tuple:
    """Получить резюме разговора (совместимость)"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT summary_text, last_message_id FROM conversation_summary WHERE user_id = $1 ORDER BY updated_at DESC LIMIT 1",
            user_id
        )
        return (row['summary_text'], row['last_message_id']) if row else ("", 0)
    except Exception as e:
        log_error_with_context(e, {"function": "get_conversation_summary", "user_id": user_id})
        return ("", 0)
    finally:
        await release_db_connection(conn)

async def save_conversation_summary(user_id: int, summary: str, last_message_id: int) -> bool:
    """Сохранить резюме разговора"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            """INSERT INTO conversation_summary (user_id, summary_text, last_message_id, updated_at)
               VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
               ON CONFLICT (user_id) DO UPDATE SET
               summary_text = $2, last_message_id = $3, updated_at = CURRENT_TIMESTAMP""",
            user_id, summary, last_message_id
        )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "save_conversation_summary", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_messages_after(user_id: int, message_id: int) -> List[Dict]:
    """Получить сообщения после указанного ID"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """SELECT id, role, message, timestamp 
               FROM chat_history 
               WHERE user_id = $1 AND id > $2 
               ORDER BY id ASC""",
            user_id, message_id
        )
        return [dict(row) for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "get_messages_after", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

async def get_last_summary(user_id: int) -> tuple:
    """Получить последнее резюме документа (совместимость)"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id, summary FROM documents WHERE user_id = $1 AND confirmed = true ORDER BY uploaded_at DESC LIMIT 1",
            user_id
        )
        return (row['id'], row['summary']) if row else (None, "")
    except Exception as e:
        log_error_with_context(e, {"function": "get_last_summary", "user_id": user_id})
        return (None, "")
    finally:
        await release_db_connection(conn)

# 🌐 ФУНКЦИИ ЛОКАЛИЗАЦИИ
async def get_user_language(user_id: int) -> str:
    """Получить язык пользователя"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT language FROM users WHERE user_id = $1", user_id)
        return row['language'] if row and row['language'] else 'ru'
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_language", "user_id": user_id})
        return 'ru'
    finally:
        await release_db_connection(conn)

async def set_user_language(user_id: int, language: str) -> bool:
    """Установить язык пользователя (создать если не существует)"""
    conn = await get_db_connection()
    try:
        # ✅ СНАЧАЛА создаем пользователя, если его нет
        await conn.execute(
            "INSERT INTO users (user_id, language) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            user_id, language
        )
        
        # ✅ ПОТОМ обновляем язык (на случай, если пользователь уже существовал)
        await conn.execute(
            "UPDATE users SET language = $1 WHERE user_id = $2",
            language, user_id
        )
        
        # ✅ СОЗДАЕМ лимиты для нового пользователя
        await conn.execute(
            "INSERT INTO user_limits (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
            user_id
        )
        
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "set_user_language", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Функция локализации (исправленная)"""
    try:
        from locales import translations
        
        # Получаем переводы для указанного языка
        lang_translations = translations.get(lang, translations.get('ru', {}))
        text = lang_translations.get(key, key)
        
        # Форматируем с параметрами если они есть
        return text.format(**kwargs) if kwargs else text
    except Exception as e:
        # Fallback в случае ошибки
        return key

def get_all_values_for_key(key: str) -> List[str]:
    """Получить все значения для ключа локализации"""
    from locales import translations
    return [lang_data.get(key) for lang_data in translations.values() if key in lang_data]

# 👤 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ПРОФИЛЯ
async def get_user_profile(user_id: int) -> Dict:
    """Получить полный профиль пользователя"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else {}
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_profile", "user_id": user_id})
        return {}
    finally:
        await release_db_connection(conn)

async def get_user_medications_text(user_id: int) -> str:
    """Получить лекарства пользователя в текстовом виде"""
    medications = await get_user_medications(user_id)
    if not medications:
        return "Не принимает лекарства"
    
    med_texts = []
    for med in medications:
        med_texts.append(f"{med['name']} ({med['label']})")
    
    return "; ".join(med_texts)

# 🗑️ ФУНКЦИЯ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЯ
async def delete_user_completely(user_id: int) -> bool:
    """Полностью удалить пользователя и все его данные"""
    conn = await get_db_connection()
    try:
        # Удаляем в правильном порядке (из-за внешних ключей)
        await conn.execute("DELETE FROM chat_history WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM conversation_summary WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM medications WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM documents WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM user_limits WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM transactions WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM user_subscriptions WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
        
        # Удаляем из векторной базы
        from vector_db_postgresql import delete_all_chunks_by_user
        await delete_all_chunks_by_user(user_id)
        
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "delete_user_completely", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

# 📊 ФУНКЦИИ СТАТИСТИКИ
async def get_db_stats() -> Dict:
    """Получить статистику базы данных"""
    conn = await get_db_connection()
    try:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        docs_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
        messages_count = await conn.fetchval("SELECT COUNT(*) FROM chat_history")
        
        return {
            "users": users_count,
            "documents": docs_count,
            "messages": messages_count,
            "status": "healthy"
        }
    except Exception as e:
        log_error_with_context(e, {"function": "get_db_stats"})
        return {"status": "error", "error": str(e)}
    finally:
        await release_db_connection(conn)

async def db_health_check() -> bool:
    """Проверка здоровья базы данных"""
    try:
        conn = await get_db_connection()
        await conn.fetchval("SELECT 1")
        await release_db_connection(conn)
        return True
    except Exception:
        return False

# 🔄 СОВМЕСТИМОСТЬ СО СТАРЫМИ ИМЕНАМИ ФУНКЦИЙ
async def get_user_documents(user_id: int, limit: int = 10) -> List[Dict]:
    """Получить документы пользователя"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """SELECT id, title, file_type, uploaded_at as date 
               FROM documents 
               WHERE user_id = $1 AND confirmed = TRUE
               ORDER BY uploaded_at DESC 
               LIMIT $2""",
            user_id, limit
        )
        return [dict(row) for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_documents", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

async def update_user_field(user_id: int, field: str, value: Any) -> bool:
    """Совместимость: update_user_field -> update_user_profile"""
    return await update_user_profile(user_id, field, value)

async def save_user(user_id: int, name: str, birth_year: int = None) -> bool:
    """Сохранить/обновить данные пользователя"""
    conn = await get_db_connection()
    try:
        # Обновляем имя
        if name:
            await conn.execute(
                "UPDATE users SET name = $1 WHERE user_id = $2",
                name, user_id
            )
        
        # Обновляем год рождения
        if birth_year is not None:
            await conn.execute(
                "UPDATE users SET birth_year = $1 WHERE user_id = $2",
                birth_year, user_id
            )
        
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "save_user", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def user_exists(user_id: int) -> bool:
    """Совместимость: проверка существования пользователя"""
    user_data = await get_user(user_id)
    return user_data is not None

async def get_user_name(user_id: int) -> Optional[str]:
    """Совместимость: получение имени пользователя"""
    user_data = await get_user(user_id)
    return user_data.get('name') if user_data else None

async def is_fully_registered(user_id: int) -> bool:
    """Проверяет, полностью ли зарегистрирован пользователь"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT name, birth_year FROM users WHERE user_id = $1", 
            user_id
        )
        
        if not row:
            return False
            
        # Проверяем обязательные поля
        name = row['name']
        birth_year = row['birth_year']
        
        return bool(name and len(name.strip()) > 0 and birth_year)
        
    except Exception as e:
        log_error_with_context(e, {"function": "is_fully_registered", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_user_name(user_id: int) -> Optional[str]:
    """Получить имя пользователя (совместимость)"""
    user_data = await get_user(user_id)
    return user_data.get('name') if user_data else None

async def update_document_confirmed(document_id: int, confirmed: int) -> bool:
    """Обновить статус подтверждения документа"""
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "UPDATE documents SET confirmed = $1 WHERE id = $2",
            bool(confirmed), document_id
        )
        return result != "UPDATE 0"
    except Exception as e:
        log_error_with_context(e, {"function": "update_document_confirmed", "document_id": document_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_documents_by_user(user_id: int, limit: int = 10) -> List[Dict]:
    """Совместимость: get_documents_by_user -> get_user_documents"""
    return await get_user_documents(user_id, limit)

# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ

async def execute_query(query: str, params: tuple = ()) -> int:
    """
    Выполнение простого запроса (INSERT, UPDATE, DELETE)
    Возвращает количество затронутых строк
    """
    conn = await get_db_connection()
    try:
        # Преобразуем SQLite синтаксис в PostgreSQL
        pg_query = query.replace('?', '${}').format(*[i+1 for i in range(len(params))])
        result = await conn.execute(pg_query, *params)
        
        # Извлекаем количество строк из результата
        if result.startswith('INSERT'):
            return 1
        elif result.startswith('UPDATE'):
            return int(result.split()[-1]) if result.split()[-1].isdigit() else 1
        elif result.startswith('DELETE'):
            return int(result.split()[-1]) if result.split()[-1].isdigit() else 1
        else:
            return 0
    except Exception as e:
        log_error_with_context(e, {"function": "execute_query", "query": query[:100]})
        return 0
    finally:
        await release_db_connection(conn)

async def fetch_one(query: str, params: tuple = ()) -> Optional[tuple]:
    """Выполнение SELECT запроса, возврат одной строки как tuple"""
    conn = await get_db_connection()
    try:
        # Преобразуем SQLite синтаксис в PostgreSQL
        pg_query = query.replace('?', '${}').format(*[i+1 for i in range(len(params))])
        row = await conn.fetchrow(pg_query, *params)
        return tuple(row) if row else None
    except Exception as e:
        log_error_with_context(e, {"function": "fetch_one", "query": query[:100]})
        return None
    finally:
        await release_db_connection(conn)

async def fetch_all(query: str, params: tuple = ()) -> List[tuple]:
    """Выполнение SELECT запроса, возврат всех строк как list of tuples"""
    conn = await get_db_connection()
    try:
        # Преобразуем SQLite синтаксис в PostgreSQL
        pg_query = query.replace('?', '${}').format(*[i+1 for i in range(len(params))])
        rows = await conn.fetch(pg_query, *params)
        return [tuple(row) for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "fetch_all", "query": query[:100]})
        return []
    finally:
        await release_db_connection(conn)

async def insert_and_get_id(query: str, params: tuple = ()) -> int:
    """Выполнение INSERT и возврат ID новой записи"""
    conn = await get_db_connection()
    try:
        # Преобразуем SQLite синтаксис в PostgreSQL и добавляем RETURNING id
        pg_query = query.replace('?', '${}').format(*[i+1 for i in range(len(params))])
        
        if 'RETURNING' not in pg_query.upper():
            # Находим название таблицы и добавляем RETURNING id
            if 'INSERT INTO' in pg_query.upper():
                pg_query = pg_query.rstrip(';') + ' RETURNING id'
        
        result = await conn.fetchval(pg_query, *params)
        return result if result else 0
    except Exception as e:
        log_error_with_context(e, {"function": "insert_and_get_id", "query": query[:100]})
        return 0
    finally:
        await release_db_connection(conn)

async def get_medications(user_id: int) -> List[Dict]:
    """Получить список лекарств пользователя (совместимость со старой версией)"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT name, time, label FROM medications WHERE user_id = $1 ORDER BY time",
            user_id
        )
        return [{"name": row['name'], "time": row['time'], "label": row['label']} for row in rows]
    except Exception as e:
        log_error_with_context(e, {"function": "get_medications", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

async def replace_medications(user_id: int, new_list: List[Dict]) -> bool:
    """Заменить список лекарств пользователя"""
    conn = await get_db_connection()
    try:
        # Удаляем старые
        await conn.execute("DELETE FROM medications WHERE user_id = $1", user_id)
        
        # Добавляем новые
        for med in new_list:
            await conn.execute(
                "INSERT INTO medications (user_id, name, time, label) VALUES ($1, $2, $3, $4)",
                user_id, med.get('name', ''), med.get('time', ''), med.get('label', '')
            )
        return True
    except Exception as e:
        log_error_with_context(e, {"function": "replace_medications", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def format_medications_schedule(user_id: int) -> str:
    """Форматировать расписание лекарств для пользователя"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT name, time, label FROM medications WHERE user_id = $1 ORDER BY time",
            user_id
        )
        
        if not rows:
            lang = await get_user_language(user_id)
            return t("schedule_empty", lang)
        
        return "\n".join([f"{row['time']} — {row['name']} ({row['label']})" for row in rows])
    except Exception as e:
        log_error_with_context(e, {"function": "format_medications_schedule", "user_id": user_id})
        try:
            lang = await get_user_language(user_id)
            return t("schedule_empty", lang)
        except:
            return "Расписание недоступно"
    finally:
        await release_db_connection(conn)

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
    
    return value

# Добавьте ЭТИ ФУНКЦИИ в КОНЕЦ вашего db_postgresql.py

import re

def convert_sql_to_postgresql(query: str, params: tuple) -> tuple:
    """Конвертирует SQLite запрос в PostgreSQL"""
    placeholder_count = 0
    
    def replace_placeholder(match):
        nonlocal placeholder_count
        placeholder_count += 1
        return f"${placeholder_count}"
    
    converted_query = re.sub(r'\?', replace_placeholder, query)
    return converted_query, params

# ✅ СОВМЕСТИМЫЕ ФУНКЦИИ (добавить в конец db_postgresql.py)
async def fetch_one(query: str, params: tuple = ()):
    """Совместимая версия fetch_one с автоконвертацией SQLite → PostgreSQL"""
    pg_query, pg_params = convert_sql_to_postgresql(query, params)
    
    conn = await get_db_connection()
    try:
        result = await conn.fetchrow(pg_query, *pg_params)
        return tuple(result.values()) if result else None
    finally:
        await release_db_connection(conn)

async def fetch_all(query: str, params: tuple = ()):
    """Совместимая версия fetch_all с автоконвертацией SQLite → PostgreSQL"""
    pg_query, pg_params = convert_sql_to_postgresql(query, params)
    
    conn = await get_db_connection()
    try:
        results = await conn.fetch(pg_query, *pg_params)
        return [tuple(row.values()) for row in results]
    finally:
        await release_db_connection(conn)

async def execute_query(query: str, params: tuple = ()):
    """Совместимая версия execute_query с автоконвертацией SQLite → PostgreSQL"""
    pg_query, pg_params = convert_sql_to_postgresql(query, params)
    
    conn = await get_db_connection()
    try:
        result = await conn.execute(pg_query, *pg_params)
        # Возвращаем количество затронутых строк
        if result.startswith(('INSERT', 'UPDATE', 'DELETE')):
            return int(result.split()[-1])
        return 0
    finally:
        await release_db_connection(conn)

async def insert_and_get_id(query: str, params: tuple = ()):
    """Совместимая версия INSERT с возвратом ID"""
    pg_query, pg_params = convert_sql_to_postgresql(query, params)
    
    # Добавляем RETURNING id если его нет
    if 'RETURNING' not in pg_query.upper():
        pg_query += ' RETURNING id'
    
    conn = await get_db_connection()
    try:
        result = await conn.fetchval(pg_query, *pg_params)
        return result
    finally:
        await release_db_connection(conn)

# Переименовываем старые функции (если они есть)
# async def fetch_one_native(query: str, params: tuple = ()):
#     """Оригинальная PostgreSQL версия"""
#     ...