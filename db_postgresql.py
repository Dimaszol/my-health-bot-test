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
    """Получить соединение с базой данных"""
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

async def create_user(user_id: int, name: str) -> bool:
    """Создать нового пользователя"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO users (user_id, name) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            user_id, name
        )
        
        # 🎁 Создаем лимиты для нового пользователя
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
                       raw_text: str, summary: str, vector_id: str = None) -> Optional[int]:
    """Сохранить документ"""
    conn = await get_db_connection()
    try:
        doc_id = await conn.fetchval(
            """INSERT INTO documents (user_id, title, file_path, file_type, raw_text, summary, vector_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
            user_id, title, file_path, file_type, raw_text, summary, vector_id
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
            """SELECT id, title, file_type, uploaded_at 
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