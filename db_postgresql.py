# db_postgresql.py - Подключение к PostgreSQL для медицинского бота

import os
import asyncio
import asyncpg
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from error_handler import log_error_with_context
import logging

logger = logging.getLogger(__name__)

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
            command_timeout=180,
            statement_cache_size=0
        )
        
        # ✅ Тестируем подключение
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT version()")
            print(f"✅ PostgreSQL подключен: {result[:50]}...")
        
        # 🏗️ Создаем таблицы
        await create_tables()
        print("🗄️ Структура базы данных готова")
        
    except Exception as e:
        log_error_with_context(e, {"action": "db_connection"})
        raise

async def close_db_pool():
    """Закрытие пула соединений"""
    global db_pool
    if db_pool:
        await db_pool.close()

async def create_tables():
    """Создание всех таблиц медицинского бота для Railway (включая Garmin) - ОБНОВЛЕНО"""
    
    # 🔧 СНАЧАЛА подключаем pgvector расширение
    pgvector_setup = """
    -- Подключаем расширение pgvector (если не подключено)
    CREATE EXTENSION IF NOT EXISTS vector;
    """
    
    tables_sql = """
        -- ================================
        -- 👤 ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
        -- ================================
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
            language TEXT DEFAULT 'ru',
            gdpr_consent BOOLEAN DEFAULT FALSE,
            gdpr_consent_time TIMESTAMP DEFAULT NULL,
            total_messages_count INTEGER DEFAULT 0,
            google_id VARCHAR(255) UNIQUE,
            email VARCHAR(255) UNIQUE,
            registration_source VARCHAR(20) DEFAULT 'telegram'
        );

        -- ================================
        -- 💬 ИСТОРИЯ ЧАТА
        -- ================================
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 📄 ДОКУМЕНТЫ
        -- ================================
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            title TEXT,
            file_path TEXT,
            file_type TEXT,
            raw_text TEXT,
            summary TEXT,
            full_analysis TEXT,
            confirmed BOOLEAN DEFAULT FALSE,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            document_type VARCHAR(50),
            subtype VARCHAR(100),
            additional_context TEXT,
            first_analysis TEXT,
            document_date DATE
        );

        -- ================================
        -- 🧠 ВЕКТОРЫ ДОКУМЕНТОВ (pgvector)
        -- ================================
        CREATE TABLE IF NOT EXISTS document_vectors (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB DEFAULT '{}',
            keywords TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_chunk UNIQUE(document_id, chunk_index)
        );

        -- ================================
        -- 💊 ЛЕКАРСТВА
        -- ================================
        CREATE TABLE IF NOT EXISTS medications (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            time TEXT,
            label TEXT
        );

        -- ================================
        -- 📊 ЛИМИТЫ ПОЛЬЗОВАТЕЛЕЙ
        -- ================================
        CREATE TABLE IF NOT EXISTS user_limits (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            documents_left INTEGER DEFAULT 1,
            gpt4o_queries_left INTEGER DEFAULT 5,
            subscription_type TEXT DEFAULT 'free',
            subscription_expires_at TIMESTAMP,
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 💳 ТРАНЗАКЦИИ
        -- ================================
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
            queries_granted INTEGER DEFAULT 0,
            promo_code TEXT
        );

        -- ================================
        -- 📦 ПАКЕТЫ ПОДПИСОК
        -- ================================
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

        -- ================================
        -- 🔄 ПОДПИСКИ ПОЛЬЗОВАТЕЛЕЙ
        -- ================================
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            stripe_subscription_id TEXT UNIQUE,
            stripe_customer_id TEXT,
            package_id TEXT REFERENCES subscription_packages(id),
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cancelled_at TIMESTAMP
        );

        -- ================================
        -- 🧠 РЕЗЮМЕ РАЗГОВОРОВ
        -- ================================
        CREATE TABLE IF NOT EXISTS conversation_summary (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            summary_text TEXT,
            last_message_id INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 📋 МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА
        -- ================================
        CREATE TABLE IF NOT EXISTS medical_timeline (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            source_document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            event_date DATE NOT NULL,
            category TEXT DEFAULT 'general' CHECK (category IN ('diagnosis', 'treatment', 'test', 'procedure', 'general')),
            importance TEXT DEFAULT 'normal' CHECK (importance IN ('critical', 'important', 'normal')),
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 📊 АНАЛИТИКА
        -- ================================
        CREATE TABLE IF NOT EXISTS analytics_events (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            event TEXT NOT NULL,
            properties JSONB DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 🏃 GARMIN: ПОДКЛЮЧЕНИЯ
        -- ================================
        CREATE TABLE IF NOT EXISTS garmin_connections (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            garmin_email TEXT NOT NULL,
            garmin_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_sync_date DATE,
            sync_errors INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 🏃 GARMIN: ЕЖЕДНЕВНЫЕ ДАННЫЕ
        -- ================================
        CREATE TABLE IF NOT EXISTS garmin_daily_data (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            data_date DATE NOT NULL,
            
            -- Активность
            steps INTEGER,
            calories INTEGER,
            floors_climbed INTEGER,
            distance_meters INTEGER,
            active_periods_15min INTEGER,
            sedentary_periods_15min INTEGER,
            sleep_periods_15min INTEGER,
            total_calories INTEGER,
            vigorous_intensity_minutes INTEGER,
            moderate_intensity_minutes INTEGER,
            
            -- Сон
            sleep_duration_minutes INTEGER,
            sleep_deep_minutes INTEGER,
            sleep_light_minutes INTEGER,
            sleep_rem_minutes INTEGER,
            sleep_awake_minutes INTEGER,
            sleep_score INTEGER,
            nap_duration_minutes INTEGER,
            sleep_need_minutes INTEGER,
            sleep_baseline_minutes INTEGER,
            
            -- Пульс
            resting_heart_rate INTEGER,
            avg_heart_rate INTEGER,
            max_heart_rate INTEGER,
            min_heart_rate INTEGER,
            hrv_rmssd REAL,
            heart_rate_measurements INTEGER,
            hr_zone_rest_percent REAL,
            hr_zone_aerobic_percent REAL,
            resting_heart_rate_7day_avg INTEGER,
            hrv_status TEXT,
            hrv_baseline REAL,
            
            -- Стресс и энергия
            stress_avg INTEGER,
            stress_max INTEGER,
            stress_min INTEGER,
            stress_high_periods_count INTEGER,
            stress_low_periods_count INTEGER,
            body_battery_max INTEGER,
            body_battery_min INTEGER,
            body_battery_avg REAL,
            body_battery_charged INTEGER,
            body_battery_drained INTEGER,
            body_battery_after_sleep INTEGER,
            body_battery_stress_events INTEGER,
            body_battery_recovery_events INTEGER,
            body_battery_activity_events INTEGER,
            
            -- Дыхание и кислород
            spo2_avg REAL,
            respiration_avg REAL,
            
            -- Готовность и фитнес
            training_readiness INTEGER,
            training_readiness_status TEXT,
            readiness_sleep_factor INTEGER,
            readiness_hrv_factor INTEGER,
            readiness_stress_factor INTEGER,
            vo2_max REAL,
            fitness_age INTEGER,
            training_status TEXT,
            training_load_7day INTEGER,
            
            -- Тренировки
            activities_count INTEGER DEFAULT 0,
            activities_duration_minutes INTEGER DEFAULT 0,
            activities_calories INTEGER DEFAULT 0,
            activities_types TEXT,
            activities_max_intensity INTEGER,
            activities_data JSONB,
            
            -- Дополнительные биометрические данные
            body_temperature REAL,
            hydration_ml INTEGER,
            menstrual_cycle_phase TEXT,
            
            -- Метаданные
            data_completeness_score REAL,
            last_sync_quality TEXT,
            data_quality JSONB,
            sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(user_id, data_date)
        );

        -- ================================
        -- 🏃 GARMIN: ИСТОРИЯ АНАЛИЗОВ
        -- ================================
        CREATE TABLE IF NOT EXISTS garmin_analysis_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            analysis_date DATE NOT NULL,
            data_period TEXT DEFAULT '1_day',
            analysis_text TEXT NOT NULL,
            recommendations TEXT,
            health_score REAL,
            sleep_trend TEXT,
            activity_trend TEXT,
            stress_trend TEXT,
            recovery_trend TEXT,
            used_consultation_limit BOOLEAN DEFAULT TRUE,
            gpt_model_used TEXT DEFAULT 'gpt-4o',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, analysis_date)
        );

        -- ================================
        -- 🏃 GARMIN: НАСТРОЙКИ АНАЛИЗА
        -- ================================
        CREATE TABLE IF NOT EXISTS garmin_analysis_settings (
            user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            focus_areas TEXT[],
            goals JSONB,
            medical_conditions TEXT[],
            enable_daily_analysis BOOLEAN DEFAULT TRUE,
            enable_weekly_summary BOOLEAN DEFAULT TRUE,
            enable_alerts BOOLEAN DEFAULT TRUE,
            min_sleep_hours REAL DEFAULT 6.0,
            max_stress_threshold INTEGER DEFAULT 80,
            min_body_battery INTEGER DEFAULT 20,
            target_steps INTEGER DEFAULT 10000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ================================
        -- 🏃 GARMIN: ОТСЛЕЖИВАНИЕ СНА
        -- ================================
        CREATE TABLE IF NOT EXISTS garmin_users_sleep_tracking (
            user_id BIGINT PRIMARY KEY,
            last_analyzed_sleep_duration INTEGER,
            last_analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- ================================
        -- 🔗 ПРИВЯЗКА АККАУНТОВ
        -- ================================
        CREATE TABLE IF NOT EXISTS account_links (
            link_code VARCHAR(6) PRIMARY KEY,
            telegram_user_id BIGINT,
            web_user_id BIGINT,
            direction VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT FALSE
        );
    """

    # ================================
    # 🔄 МИГРАЦИИ (для будущих изменений)
    # ================================
    migration_sql = """
        -- Этот блок используется для добавления новых полей в существующие таблицы
        -- Все текущие поля уже добавлены в основные CREATE TABLE выше
        
        DO $$ 
        BEGIN
            NULL;  -- Пустая операция, но синтаксически правильная
        END $$;
        
        -- Пример будущей миграции:
        -- DO $$ 
        -- BEGIN
        --     IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
        --                   WHERE table_name = 'documents' AND column_name = 'new_field') THEN
        --         ALTER TABLE documents ADD COLUMN new_field TEXT;
        --     END IF;
        -- END $$;
    """

    # ================================
    # 📊 ИНДЕКСЫ
    # ================================
    indices_sql = """
        -- Векторный поиск
        CREATE INDEX IF NOT EXISTS idx_document_vectors_user_id ON document_vectors(user_id);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON document_vectors(document_id);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_keywords ON document_vectors USING gin(to_tsvector('russian', keywords));

        -- Garmin
        CREATE INDEX IF NOT EXISTS idx_garmin_daily_data_user_date ON garmin_daily_data(user_id, data_date DESC);
        CREATE INDEX IF NOT EXISTS idx_garmin_daily_data_date ON garmin_daily_data(data_date DESC);
        CREATE INDEX IF NOT EXISTS idx_garmin_analysis_user_date ON garmin_analysis_history(user_id, analysis_date DESC);
        CREATE INDEX IF NOT EXISTS idx_garmin_connections_active ON garmin_connections(user_id) WHERE is_active = TRUE;
        CREATE INDEX IF NOT EXISTS idx_garmin_connections_sync_errors ON garmin_connections(sync_errors) WHERE sync_errors >= 5;
        CREATE INDEX IF NOT EXISTS idx_garmin_daily_completeness ON garmin_daily_data(data_completeness_score) WHERE data_completeness_score IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_garmin_daily_sync_quality ON garmin_daily_data(last_sync_quality) WHERE last_sync_quality IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_garmin_daily_training_status ON garmin_daily_data(user_id, training_status) WHERE training_status IS NOT NULL;

        -- Основные таблицы
        CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics_events(event);
        CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_analytics_user_event ON analytics_events(user_id, event);
        CREATE INDEX IF NOT EXISTS idx_medical_timeline_user_date ON medical_timeline(user_id, event_date DESC);
        CREATE INDEX IF NOT EXISTS idx_medical_timeline_user_importance ON medical_timeline(user_id, importance);
        CREATE INDEX IF NOT EXISTS idx_medical_timeline_category ON medical_timeline(user_id, category);
        CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_medications_user_id ON medications(user_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_customer ON user_subscriptions(stripe_customer_id);
        CREATE INDEX IF NOT EXISTS idx_users_gdpr_consent ON users(gdpr_consent);
        CREATE INDEX IF NOT EXISTS idx_sleep_tracking_user ON garmin_users_sleep_tracking(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_limits_email ON user_limits(email);
        CREATE INDEX IF NOT EXISTS idx_account_links_telegram ON account_links(telegram_user_id);
        CREATE INDEX IF NOT EXISTS idx_account_links_web ON account_links(web_user_id);
        CREATE INDEX IF NOT EXISTS idx_account_links_active ON account_links(link_code) WHERE is_used = FALSE;
    """

    # ================================
    # 🔄 ФУНКЦИИ И ТРИГГЕРЫ
    # ================================
    functions_sql = """
        -- Функция обновления timestamps
        CREATE OR REPLACE FUNCTION update_medical_timeline_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Функция очистки старых данных Garmin
        CREATE OR REPLACE FUNCTION cleanup_old_garmin_data()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM garmin_daily_data 
            WHERE data_date < CURRENT_DATE - INTERVAL '1 year';
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
            DELETE FROM garmin_analysis_history 
            WHERE analysis_date < CURRENT_DATE - INTERVAL '6 months';
            
            BEGIN
                INSERT INTO analytics_events (user_id, event, properties) 
                VALUES (0, 'garmin_cleanup', json_build_object('deleted_records', deleted_count)::jsonb);
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
            
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;

        -- Триггер для medical_timeline
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger 
                WHERE tgname = 'medical_timeline_update_timestamp'
            ) THEN
                CREATE TRIGGER medical_timeline_update_timestamp
                    BEFORE UPDATE ON medical_timeline
                    FOR EACH ROW
                    EXECUTE FUNCTION update_medical_timeline_timestamp();
            END IF;
        END $$;
    """

    # ================================
    # 📝 КОММЕНТАРИИ
    # ================================
    comments_sql = """
        COMMENT ON COLUMN users.gdpr_consent IS 'Согласие на обработку данных (GDPR)';
        COMMENT ON COLUMN users.gdpr_consent_time IS 'Время согласия GDPR';
        COMMENT ON TABLE document_vectors IS 'Векторные эмбеддинги для семантического поиска';
        COMMENT ON COLUMN documents.full_analysis IS 'Полный анализ от Gemini специалиста для врачей';
        COMMENT ON TABLE garmin_connections IS 'Подключения к Garmin Connect';
        COMMENT ON TABLE garmin_daily_data IS 'Ежедневные данные здоровья из Garmin';
        COMMENT ON TABLE garmin_analysis_history IS 'История AI анализов Garmin';
        COMMENT ON TABLE garmin_analysis_settings IS 'Настройки персонализации анализа';
        COMMENT ON TABLE garmin_users_sleep_tracking IS 'Отслеживание сна';
        COMMENT ON COLUMN garmin_connections.garmin_email IS 'Зашифрованный email Garmin';
        COMMENT ON COLUMN garmin_connections.garmin_password IS 'Зашифрованный пароль Garmin';
        COMMENT ON COLUMN garmin_connections.sync_errors IS 'Счетчик ошибок синхронизации';
        COMMENT ON COLUMN garmin_daily_data.data_completeness_score IS 'Полнота данных 0-100';
        COMMENT ON COLUMN garmin_daily_data.last_sync_quality IS 'Качество синхронизации: good, partial, poor';
    """

    try:
        conn = await get_db_connection()
        
        # Выполняем создание таблиц по частям
        await conn.execute(pgvector_setup)
        await conn.execute(tables_sql)
        await conn.execute(migration_sql)  # НОВОЕ: выполняем миграцию
        await conn.execute(indices_sql)
        await conn.execute(functions_sql)
        await conn.execute(comments_sql)
        
        await release_db_connection(conn)
        logger.info("✅ Все таблицы и миграции созданы успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        if 'conn' in locals():
            await release_db_connection(conn)
        raise
        
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

async def update_user_profile(user_id: int, field: str, value: Any) -> bool:
    """Обновить поле в профиле пользователя"""
    
    # 🛡️ WHITELIST РАЗРЕШЁННЫХ ПОЛЕЙ
    ALLOWED_FIELDS = {
        'name', 'birth_year', 'gender', 'height_cm', 'weight_kg',
        'chronic_conditions', 'medications', 'allergies', 
        'smoking', 'alcohol', 'physical_activity', 'family_history', 'language'
    }
    
    if field not in ALLOWED_FIELDS:
        log_error_with_context(
            ValueError(f"Field '{field}' is not allowed for update"), 
            {"function": "update_user_profile", "user_id": user_id, "field": field}
        )
        return False
    
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

async def save_document(user_id: int, file_path: str, file_type: str, 
                       raw_text: str, summary: str, full_analysis: str = None,
                       first_analysis: str = None,  # ← НОВЫЙ ПАРАМЕТР
                       confirmed: bool = True, document_type: str = None, 
                       subtype: str = None, additional_context: str = None,
                       title: str = None, document_date: str = None) -> Optional[int]:
    """Сохранить документ"""
    conn = await get_db_connection()
    try:
        # Конвертируем строку даты в объект date
        from datetime import datetime
        date_obj = None
        if document_date:
            try:
                date_obj = datetime.strptime(document_date, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date format: {document_date}, using None")
        
        doc_id = await conn.fetchval(
            """INSERT INTO documents (user_id, title, file_path, file_type, raw_text, summary, full_analysis, first_analysis, confirmed, document_type, subtype, additional_context, document_date)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) RETURNING id""",
            user_id, title, file_path, file_type, raw_text, summary, full_analysis, first_analysis, confirmed, document_type, subtype, additional_context, date_obj
        )
        return doc_id
    except Exception as e:
        log_error_with_context(e, {"function": "save_document", "user_id": user_id})
        return None
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
            "documents_left": 1,
            "gpt4o_queries_left": 5,
            "subscription_type": "free"
        }
    except Exception as e:
        log_error_with_context(e, {"function": "get_user_limits", "user_id": user_id})
        return {"documents_left": 0, "gpt4o_queries_left": 0, "subscription_type": "free"}
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

async def set_user_language(user_id: int, language: str, telegram_user=None) -> bool:
    """Установить язык пользователя (создать если не существует) + имя из Telegram"""
    conn = await get_db_connection()
    try:
        # Получаем имя из Telegram
        name = None
        username = None
        if telegram_user:
            name = telegram_user.first_name or "Пользователь"
            username = telegram_user.username
        
        # СОЗДАЕМ пользователя с именем и языком
        if name:
            await conn.execute(
                "INSERT INTO users (user_id, language, name, username) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id) DO NOTHING",
                user_id, language, name, username
            )
        else:
            # Fallback если нет telegram_user
            await conn.execute(
                "INSERT INTO users (user_id, language) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
                user_id, language
            )
        
        # ПОТОМ обновляем язык (на случай, если пользователь уже существовал)
        await conn.execute(
            "UPDATE users SET language = $1 WHERE user_id = $2",
            language, user_id
        )
        
        # СОЗДАЕМ лимиты для нового пользователя
        # 🔥 ПРОВЕРЯЕМ: был ли пользователь удалён раньше
        deleted_limits = await conn.fetchrow(
            "SELECT * FROM deleted_users_limits WHERE user_id = $1", 
            user_id
        )

        if deleted_limits:
            # Восстанавливаем старые лимиты
            await conn.execute("""
                INSERT INTO user_limits 
                (user_id, google_id, email, documents_left, gpt4o_queries_left, 
                subscription_type, subscription_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE SET
                    documents_left = EXCLUDED.documents_left,
                    gpt4o_queries_left = EXCLUDED.gpt4o_queries_left,
                    subscription_type = EXCLUDED.subscription_type,
                    subscription_expires_at = EXCLUDED.subscription_expires_at
            """, 
                user_id,
                deleted_limits['google_id'],
                deleted_limits['email'],
                deleted_limits['documents_left'],
                deleted_limits['gpt4o_queries_left'],
                deleted_limits['subscription_type'],
                deleted_limits['subscription_expires_at']
            )
            # 🔥 Удаляем запись из deleted_users_limits
            await conn.execute(
                "DELETE FROM deleted_users_limits WHERE user_id = $1",
                user_id
            )
        else:
            # Новый пользователь - даём бесплатные лимиты
            await conn.execute("""
                INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left, subscription_type, email)
                VALUES ($1, 1, 5, 'free', NULL)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)
        
        # НОВОЕ: Создаем настройки уведомлений с часовым поясом по языку
        default_timezones = {
            'ru': (120, 'Киев'),        # UTC+2
            'uk': (120, 'Киев'),        # UTC+2
            'en': (0, 'Лондон GMT'),    # UTC+0
            'de': (60, 'Европа')        # UTC+1
        }
        offset, timezone_name = default_timezones.get(language, (0, 'UTC'))
        
        await conn.execute("""
            INSERT INTO notification_settings (user_id, notifications_enabled, timezone_offset, timezone_name)
            VALUES ($1, TRUE, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, offset, timezone_name)
        
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
        try:
            lang = await get_user_language(user_id)
            return t("no_medications", lang)
        except:
            return "No medications"
    
    med_texts = []
    for med in medications:
        med_texts.append(f"{med['name']} ({med['label']})")
    
    return "; ".join(med_texts)

# 🗑️ ФУНКЦИЯ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЯ
async def delete_user_completely(user_id: int) -> bool:
    """
    GDPR-совместимое удаление пользователя
    Удаляет ВСЕ данные: файлы + база + векторы + Stripe
    """
    conn = await get_db_connection()
    try:
        # 1. Получаем список файлов для удаления
        documents = await conn.fetch(
            "SELECT file_path FROM documents WHERE user_id = $1", 
            user_id
        )
        
        # 2. Удаляем файлы из Supabase Storage
        for doc in documents:
            file_path = doc['file_path']
            if file_path and file_path.startswith("users/"):
                try:
                    from supabase_storage import get_storage_manager
                    storage = get_storage_manager()
                    await storage.delete_file(file_path)
                except Exception as e:
                    pass  # Игнорируем ошибки при GDPR удалении

        # 3. Удаляем данные из Stripe (GDPR)
        try:
            from stripe_manager import StripeGDPRManager
            await StripeGDPRManager.delete_user_stripe_data_gdpr(user_id)
        except Exception as e:
            pass
        
        # 4. 🔥 НОВОЕ: Сохраняем лимиты в deleted_users_limits
        try:
            # Получаем данные пользователя
            user_data = await conn.fetchrow(
                "SELECT google_id, email, registration_source FROM users WHERE user_id = $1", 
                user_id
            )
            
            # Получаем лимиты
            limits = await conn.fetchrow(
                "SELECT * FROM user_limits WHERE user_id = $1", 
                user_id
            )
            
            if limits:
                await conn.execute("""
                    INSERT INTO deleted_users_limits 
                    (user_id, google_id, email, documents_left, gpt4o_queries_left, 
                     subscription_type, subscription_expires_at, registration_source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (user_id) DO UPDATE SET
                        google_id = COALESCE(EXCLUDED.google_id, deleted_users_limits.google_id),
                        email = COALESCE(EXCLUDED.email, deleted_users_limits.email),
                        documents_left = EXCLUDED.documents_left,
                        gpt4o_queries_left = EXCLUDED.gpt4o_queries_left,
                        subscription_type = EXCLUDED.subscription_type,
                        subscription_expires_at = EXCLUDED.subscription_expires_at,
                        registration_source = EXCLUDED.registration_source,
                        deleted_at = CURRENT_TIMESTAMP
                """, 
                    user_id, 
                    user_data['google_id'] if user_data else None,
                    user_data['email'] if user_data else None,
                    limits['documents_left'],
                    limits['gpt4o_queries_left'],
                    limits['subscription_type'],
                    limits['subscription_expires_at'],
                    user_data['registration_source'] if user_data else 'telegram'
                )
        except Exception as e:
            logger.error(f"Ошибка сохранения лимитов в deleted_users_limits: {e}")
        

        # 5. Удаляем из базы данных (в правильном порядке)
        tables_to_clear = [
            "chat_history",
            "conversation_summary", 
            "medical_timeline",
            "medications",
            "documents",            
            "transactions", 
            "user_subscriptions",
            "analytics_events",
            "users"  # В последнюю очередь
        ]
        
        for table in tables_to_clear:
            try:
                await conn.execute(f"DELETE FROM {table} WHERE user_id = $1", user_id)
            except Exception as e:
                pass
        
        # 6. Удаляем векторы
        try:
            from vector_db_postgresql import delete_all_chunks_by_user
            await delete_all_chunks_by_user(user_id)
        except Exception as e:
            pass
        
        # 7. Логируем удаление в аналитику (в самом конце)
        try:
            from analytics_system import Analytics
            await Analytics.track(user_id, "user_data_deleted_gdpr", {
                "timestamp": datetime.now().isoformat(),
                "reason": "user_request",
                "stripe_cleaned": True
            })
        except Exception as e:
            pass
        
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "delete_user_completely", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def update_user_field(user_id: int, field: str, value: Any) -> bool:
    """Совместимость: update_user_field -> update_user_profile"""
    return await update_user_profile(user_id, field, value)

async def save_user(user_id: int, name: str = None, birth_year: int = None,
                   gdpr_consent: bool = None, username: str = None) -> bool:
    """
    ✅ УПРОЩЕННАЯ версия: только обновляет существующих пользователей
    (новые пользователи создаются через set_user_language)
    """
    conn = await get_db_connection()
    try:
        # Пользователь уже должен существовать (создан через set_user_language)
        # Просто обновляем его данные
        await conn.execute("""
            UPDATE users SET 
                name = COALESCE($2, name),
                birth_year = COALESCE($3, birth_year),
                gdpr_consent = COALESCE($4, gdpr_consent),
                username = COALESCE($5, username),
                gdpr_consent_time = CASE WHEN $4 = TRUE THEN CURRENT_TIMESTAMP ELSE gdpr_consent_time END,
                last_updated = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id, name, birth_year, gdpr_consent, username)
        
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "save_user", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_user_name(user_id: int) -> Optional[str]:
    """Совместимость: получение имени пользователя"""
    user_data = await get_user(user_id)
    return user_data.get('name') if user_data else None

async def is_fully_registered(user_id: int) -> bool:
    """
    ✅ ДЛЯ МЕДИЦИНСКОГО БОТА: Проверяет имя и год рождения
    Это минимум для качественных медицинских рекомендаций
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT name, birth_year FROM users WHERE user_id = $1", 
            user_id
        )
        
        if not row:
            return False
            
        # ✅ Проверяем обязательные поля для медицинского бота
        name = row['name']
        birth_year = row['birth_year']
        
        # Имя обязательно
        if not name or len(name.strip()) == 0:
            return False
            
        # Год рождения нужен для возрастных рекомендаций
        if not birth_year:
            return False
        
        # Проверяем разумность года рождения (1900-2025)
        current_year = datetime.now().year
        if birth_year < 1900 or birth_year > current_year:
            return False
        
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "is_fully_registered", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

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

async def get_documents_by_user(user_id: int, limit: int = 999) -> List[Dict]:
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
        log_error_with_context(e, {"function": "get_documents_by_user", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ

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
        
        schedule_lines = []
        for row in rows:
            if row['label']:
                line = f"{row['time']} — {row['name']} ({row['label']})"
            else:
                line = f"{row['time']} — {row['name']}"
            schedule_lines.append(line)
        
        return "\n".join(schedule_lines)
        
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

def convert_sql_to_postgresql(query: str, params: tuple) -> tuple:
    """Конвертирует SQLite запрос в PostgreSQL"""
    placeholder_count = 0
    
    def replace_placeholder(match):
        nonlocal placeholder_count
        placeholder_count += 1
        return f"${placeholder_count}"
    
    converted_query = re.sub(r'\?', replace_placeholder, query)
    return converted_query, params

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

async def set_gdpr_consent(user_id: int, consent: bool = True) -> bool:
    """Устанавливает GDPR согласие пользователя"""
    conn = await get_db_connection()
    try:
        await conn.execute(
            """UPDATE users SET 
               gdpr_consent = $1, 
               gdpr_consent_time = CURRENT_TIMESTAMP 
               WHERE user_id = $2""",
            consent, user_id
        )
        
        # 📊 Логируем согласие в аналитику
        if consent:
            from analytics_system import Analytics
            await Analytics.track(user_id, "gdpr_consent_given", {
                "timestamp": datetime.now().isoformat(),
                "user_agent": "telegram_bot"
            })

        return True
        
    except Exception as e:
        log_error_with_context(e, {
            "function": "set_gdpr_consent", 
            "user_id": user_id, 
            "consent": consent
        })
        return False
    finally:
        await release_db_connection(conn)

async def has_gdpr_consent(user_id: int) -> bool:
    """Проверяет, дал ли пользователь GDPR согласие"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT gdpr_consent FROM users WHERE user_id = $1", 
            user_id
        )
        return bool(row['gdpr_consent']) if row else False
    except Exception as e:
        log_error_with_context(e, {"function": "has_gdpr_consent", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_last_message_id(user_id: int) -> int:
    """Получить ID последнего сообщения пользователя"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id FROM chat_history WHERE user_id = $1 ORDER BY id DESC LIMIT 1",
            user_id
        )
        return row['id'] if row else 0
    except Exception as e:
        log_error_with_context(e, {"function": "get_last_message_id", "user_id": user_id})
        return 0
    finally:
        await release_db_connection(conn)

# ФУНКЦИЯ ДЛЯ ВЕБСЕРВИСА ОБНОВЛЕНИЕ ПРОФАЙЛА
async def update_user_profile_dict(user_id: int, update_data: dict) -> bool:
    """
    Обновление профиля пользователя
    
    Args:
        user_id: ID пользователя
        update_data: Словарь с полями для обновления
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    
    # 🛡️ WHITELIST РАЗРЕШЁННЫХ ПОЛЕЙ
    ALLOWED_FIELDS = {
        'name', 'birth_year', 'gender', 'height_cm', 'weight_kg',
        'chronic_conditions', 'medications', 'allergies', 
        'smoking', 'alcohol', 'physical_activity', 'family_history', 'language'
    }
    
    try:
        # Формируем SQL запрос динамически на основе переданных полей
        fields = []
        values = []
        param_count = 1
        
        for key, value in update_data.items():
            # ✅ ПРОВЕРЯЕМ ЧТО ПОЛЕ РАЗРЕШЕНО
            if key not in ALLOWED_FIELDS:
                logger.error(f"Попытка обновить недопустимое поле: {key}")
                continue  # Пропускаем недопустимое поле
            
            fields.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1
        
        if not fields:
            return True  # Нечего обновлять
        
        # Добавляем user_id в конец
        values.append(user_id)
        
        query = f"""
            UPDATE users 
            SET {', '.join(fields)}
            WHERE user_id = ${param_count}
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, *values)
        
        return True
        
    except Exception as e:
        logger.error("Ошибка обновления профиля пользователя")
        return False