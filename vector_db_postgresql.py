# vector_db_postgresql.py - Замена ChromaDB на PostgreSQL + pgvector

import re
import tiktoken
import asyncpg
import numpy as np
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    """Получает OpenAI клиент с ленивой инициализацией"""
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PostgreSQLVectorDB:
    """
    Векторная база данных на PostgreSQL с pgvector
    Замена ChromaDB для медицинского бота
    """
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def initialize_vector_tables(self):
        """Создает таблицы для векторного поиска"""
        
        create_tables_sql = """
        -- 🔌 Включаем расширение pgvector
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- 📊 ТАБЛИЦА ВЕКТОРОВ ДОКУМЕНТОВ
        CREATE TABLE IF NOT EXISTS document_vectors (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding vector(1536),  -- OpenAI text-embedding-3-small размерность
            metadata JSONB DEFAULT '{}',
            keywords TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- 🔍 ИНДЕКСЫ ДЛЯ БЫСТРОГО ПОИСКА
            CONSTRAINT unique_chunk UNIQUE(document_id, chunk_index)
        );
        
        -- 📈 ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
        CREATE INDEX IF NOT EXISTS idx_document_vectors_user_id ON document_vectors(user_id);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON document_vectors(document_id);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding ON document_vectors USING ivfflat (embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS idx_document_vectors_keywords ON document_vectors USING gin(to_tsvector('russian', keywords));
        """
        
        conn = await self.db_pool.acquire()
        try:
            await conn.execute(create_tables_sql)
            logger.info("✅ Векторные таблицы PostgreSQL созданы")
        except Exception as e:
            logger.error(f"❌ Ошибка создания векторных таблиц: {e}")
            raise
        finally:
            await self.db_pool.release(conn)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Получает эмбеддинг от OpenAI"""
        try:
            # ✅ СОЗДАЕМ КЛИЕНТ ТОЛЬКО КОГДА НУЖЕН:
            client = get_openai_client()
            
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text.replace("\n", " ")[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Ошибка получения эмбеддинга: {e}")
            raise
    
    async def add_document_chunks(self, document_id: int, user_id: int, chunks: List[Dict]) -> bool:
        """
        Добавляет чанки документа в векторную базу
        
        Args:
            document_id: ID документа
            user_id: ID пользователя  
            chunks: Список чанков с текстом и метаданными
        """
        conn = await self.db_pool.acquire()
        try:
            # 🗑️ Удаляем старые векторы этого документа
            await conn.execute(
                "DELETE FROM document_vectors WHERE document_id = $1",
                document_id
            )
            
            # ➕ Добавляем новые векторы
            for chunk in chunks:
                # 🧠 Получаем эмбеддинг
                embedding = await self.get_embedding(chunk['chunk_text'])
                
                # 💾 Сохраняем в базу
                await conn.execute("""
                    INSERT INTO document_vectors 
                    (document_id, user_id, chunk_index, chunk_text, embedding, metadata, keywords)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                    document_id,
                    user_id,
                    chunk['chunk_index'],
                    chunk['chunk_text'],
                    embedding,
                    json.dumps(chunk['metadata']),
                    chunk['metadata'].get('keywords', '')
                )
            
            logger.info(f"✅ Добавлено {len(chunks)} векторов для документа {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления векторов: {e}")
            return False
        finally:
            await self.db_pool.release(conn)
    
    async def search_similar_chunks(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """
        Векторный поиск по чанкам пользователя
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Количество результатов
            
        Returns:
            Список релевантных чанков
        """
        conn = await self.db_pool.acquire()
        try:
            # 🧠 Получаем эмбеддинг запроса
            query_embedding = await self.get_embedding(query)
            
            # 🔍 Векторный поиск
            results = await conn.fetch("""
                SELECT 
                    dv.chunk_text,
                    dv.metadata,
                    dv.keywords,
                    d.title as document_title,
                    d.uploaded_at,
                    (dv.embedding <=> $1::vector) as distance
                FROM document_vectors dv
                JOIN documents d ON d.id = dv.document_id
                WHERE dv.user_id = $2
                ORDER BY dv.embedding <=> $1::vector
                LIMIT $3
            """, query_embedding, user_id, limit)
            
            # 📊 Форматируем результаты
            chunks = []
            for row in results:
                chunks.append({
                    "chunk_text": row['chunk_text'],
                    "metadata": json.loads(row['metadata']),
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at'],
                    "similarity": 1 - row['distance']  # Конвертируем distance в similarity
                })
            
            logger.info(f"🔍 Найдено {len(chunks)} релевантных чанков для пользователя {user_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Ошибка векторного поиска: {e}")
            return []
        finally:
            await self.db_pool.release(conn)
    
    async def keyword_search_chunks(self, user_id: int, keywords: str, limit: int = 5) -> List[Dict]:
        """
        Текстовый поиск по ключевым словам
        
        Args:
            user_id: ID пользователя
            keywords: Ключевые слова для поиска
            limit: Количество результатов
        """
        conn = await self.db_pool.acquire()
        try:
            # 🔍 Полнотекстовый поиск по PostgreSQL
            results = await conn.fetch("""
                SELECT 
                    dv.chunk_text,
                    dv.metadata,
                    dv.keywords,
                    d.title as document_title,
                    d.uploaded_at,
                    ts_rank(to_tsvector('russian', dv.chunk_text || ' ' || dv.keywords), 
                           plainto_tsquery('russian', $1)) as rank
                FROM document_vectors dv
                JOIN documents d ON d.id = dv.document_id
                WHERE dv.user_id = $2
                  AND (to_tsvector('russian', dv.chunk_text || ' ' || dv.keywords) @@ 
                       plainto_tsquery('russian', $1))
                ORDER BY rank DESC
                LIMIT $3
            """, keywords, user_id, limit)
            
            # 📊 Форматируем результаты
            chunks = []
            for row in results:
                chunks.append({
                    "chunk_text": row['chunk_text'],
                    "metadata": json.loads(row['metadata']),
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at'],
                    "rank": float(row['rank'])
                })
            
            logger.info(f"🔍 Найдено {len(chunks)} чанков по ключевым словам для пользователя {user_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска по ключевым словам: {e}")
            return []
        finally:
            await self.db_pool.release(conn)
    
    async def delete_document_vectors(self, document_id: int):
        """Удаляет все векторы документа"""
        conn = await self.db_pool.acquire()
        try:
            result = await conn.execute(
                "DELETE FROM document_vectors WHERE document_id = $1",
                document_id
            )
            deleted_count = int(result.split()[-1])  # Извлекаем количество удаленных строк
            logger.info(f"🗑️ Удалено {deleted_count} векторов документа {document_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления векторов документа {document_id}: {e}")
            return False
        finally:
            await self.db_pool.release(conn)
    
    async def delete_user_vectors(self, user_id: int):
        """Удаляет все векторы пользователя"""
        conn = await self.db_pool.acquire()
        try:
            result = await conn.execute(
                "DELETE FROM document_vectors WHERE user_id = $1",
                user_id
            )
            deleted_count = int(result.split()[-1])
            logger.info(f"🗑️ Удалено {deleted_count} векторов пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления векторов пользователя {user_id}: {e}")
            return False
        finally:
            await self.db_pool.release(conn)
    
    async def get_vector_stats(self) -> Dict:
        """Получает статистику векторной базы"""
        conn = await self.db_pool.acquire()
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_vectors,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT document_id) as unique_documents,
                    AVG(length(chunk_text)) as avg_chunk_length
                FROM document_vectors
            """)
            
            return {
                "total_vectors": stats['total_vectors'],
                "unique_users": stats['unique_users'], 
                "unique_documents": stats['unique_documents'],
                "avg_chunk_length": round(stats['avg_chunk_length'], 1) if stats['avg_chunk_length'] else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {"total_vectors": 0, "unique_users": 0, "unique_documents": 0}
        finally:
            await self.db_pool.release(conn)

# 🌐 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР (будет инициализирован в main.py)
vector_db: Optional[PostgreSQLVectorDB] = None

async def initialize_vector_db(db_pool):
    from db_postgresql import db_pool  # Импортируем внутри функции
    """Инициализирует векторную базу данных"""
    global vector_db
    vector_db = PostgreSQLVectorDB(db_pool)
    await vector_db.initialize_vector_tables()
    logger.info("✅ PostgreSQL Vector DB инициализирована")

# 🔄 ФУНКЦИИ СОВМЕСТИМОСТИ (чтобы не менять весь код)
async def add_chunks_to_vector_db(document_id: int, user_id: int, chunks: List[Dict]):
    """Добавляет чанки в векторную базу (совместимость с ChromaDB)"""
    if vector_db:
        return await vector_db.add_document_chunks(document_id, user_id, chunks)
    return False

async def search_similar_chunks(user_id: int, query: str, limit: int = 5) -> List[Dict]:
    """Поиск похожих чанков (совместимость с ChromaDB)"""
    if vector_db:
        return await vector_db.search_similar_chunks(user_id, query, limit)
    return []

async def keyword_search_chunks(user_id: int, keywords: str, limit: int = 5) -> List[Dict]:
    """Поиск по ключевым словам (совместимость с ChromaDB)"""
    if vector_db:
        return await vector_db.keyword_search_chunks(user_id, keywords, limit)
    return []

async def delete_document_from_vector_db(document_id: int):
    """Удаляет документ из векторной базы (совместимость с ChromaDB)"""
    if vector_db:
        return await vector_db.delete_document_vectors(document_id)
    return False

async def extract_date_from_text(text: str) -> str:
    """Извлекает дату из текста (перенесено из vector_utils.py)"""
    match = re.match(r"\[(\d{2})[./](\d{2})[./](\d{4})\]", text.strip())
    if match:
        try:
            date = datetime.strptime(".".join(match.groups()), "%d.%m.%Y")
            return date.strftime("%Y-%m-%d")
        except:
            pass
    return None

async def split_into_chunks(summary: str, document_id: int, user_id: int) -> List[Dict]:
    """
    Разбивает документ на чанки для векторизации
    Перенесено из vector_utils.py и адаптировано для PostgreSQL
    """
    from gpt import extract_keywords  # Импорт внутри функции
    
    encoder = tiktoken.encoding_for_model("gpt-4")
    paragraphs = summary.strip().split("\n\n")
    now_str = datetime.now().strftime("%Y-%m-%d")

    chunks = []
    chunk_index = 0

    for para in paragraphs:
        clean_text = para.strip()
        if len(clean_text) < 20:
            continue

        token_count = len(encoder.encode(clean_text))
        
        found_date = await extract_date_from_text(clean_text)
        chunk_date = found_date if found_date else now_str

        # 🔹 Извлекаем ключевые слова для этого абзаца
        keywords = await extract_keywords(clean_text)

        chunks.append({
            "chunk_text": clean_text,
            "chunk_index": chunk_index,
            "metadata": {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "confirmed": 1,
                "source": "summary",
                "token_count": token_count,
                "created_at": chunk_date,
                "date_inside": found_date or "",
                "keywords": ", ".join(keywords)
            }
        })
        chunk_index += 1
    
    # ❗ Удаляем последний чанк, если их больше одного (логика из vector_utils)
    if len(chunks) > 1:
        chunks = chunks[:-1]

    return chunks

# ✅ ОБНОВЛЯЕМ функцию add_chunks_to_vector_db для совместимости:

async def add_chunks_to_vector_db(document_id: int, user_id: int, chunks: List[Dict]):
    """
    Добавляет чанки в векторную базу (совместимость с ChromaDB)
    Теперь это обертка для PostgreSQL функции
    """
    if vector_db:
        return await vector_db.add_document_chunks(document_id, user_id, chunks)
    return False

# ✅ ДОБАВЛЯЕМ функции для полной совместимости с vector_utils.py:

async def delete_all_chunks_by_user(user_id: int):
    """Удаляет все векторы пользователя (совместимость с vector_db.py)"""
    if vector_db:
        return await vector_db.delete_user_vectors(user_id)
    return False

async def mark_chunks_unconfirmed(document_id: int):
    """
    Помечает чанки документа как неподтвержденные
    (в PostgreSQL версии можно не реализовывать или сделать заглушку)
    """
    # В PostgreSQL версии эта функция может быть заглушкой
    # так как у нас нет поля "confirmed" или оно не критично
    logger.info(f"mark_chunks_unconfirmed({document_id}) - заглушка для PostgreSQL")
    return True

async def get_collection_stats():
    """Получает статистику векторной базы (совместимость с vector_db.py)"""
    if vector_db:
        return await vector_db.get_vector_stats()
    return {"total_documents": 0, "status": "error"}

# ✅ ФУНКЦИИ ДЛЯ РАБОТЫ С ЭМБЕДДИНГАМИ (если нужны):

def validate_embedding_dimensions(embedding: List[float]) -> bool:
    """Проверяет размерность эмбеддинга"""
    return len(embedding) == 1536  # OpenAI text-embedding-3-small

async def batch_get_embeddings(texts: List[str]) -> List[List[float]]:
    """Получает эмбеддинги для списка текстов (batch обработка)"""
    embeddings = []
    for text in texts:
        if vector_db:
            embedding = await vector_db.get_embedding(text)
            embeddings.append(embedding)
        else:
            embeddings.append([0.0] * 1536)  # Заглушка
    return embeddings

# 🌐 ГЛОБАЛЬНЫЙ ДОСТУП К БД ПУЛУ
async def initialize_vector_db(db_pool=None):
    """Инициализирует векторную базу данных"""
    global vector_db
    
    # Получаем пул из db_postgresql если не передан
    if db_pool is None:
        from db_postgresql import db_pool as main_db_pool
        db_pool = main_db_pool
    
    vector_db = PostgreSQLVectorDB(db_pool)
    await vector_db.initialize_vector_tables()
    logger.info("✅ PostgreSQL Vector DB инициализирована")

# 🔄 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ СОВМЕСТИМОСТИ

async def delete_all_chunks_by_user(user_id: int):
    """Удаляет все векторы пользователя (совместимость с vector_db.py)"""
    if vector_db:
        return await vector_db.delete_user_vectors(user_id)
    return False

async def mark_chunks_unconfirmed(document_id: int):
    """
    Помечает чанки документа как неподтвержденные
    (в PostgreSQL версии можно не реализовывать или сделать заглушку)
    """
    # В PostgreSQL версии эта функция может быть заглушкой
    # так как у нас нет поля "confirmed" или оно не критично
    logger.info(f"mark_chunks_unconfirmed({document_id}) - заглушка для PostgreSQL")
    return True

async def get_collection_stats():
    """Получает статистику векторной базы (совместимость с vector_db.py)"""
    if vector_db:
        return await vector_db.get_vector_stats()
    return {"total_documents": 0, "status": "error"}

# ✅ ФУНКЦИИ ДЛЯ РАБОТЫ С ЭМБЕДДИНГАМИ (если нужны):

def validate_embedding_dimensions(embedding: List[float]) -> bool:
    """Проверяет размерность эмбеддинга"""
    return len(embedding) == 1536  # OpenAI text-embedding-3-small

async def batch_get_embeddings(texts: List[str]) -> List[List[float]]:
    """Получает эмбеддинги для списка текстов (batch обработка)"""
    embeddings = []
    for text in texts:
        if vector_db:
            embedding = await vector_db.get_embedding(text)
            embeddings.append(embedding)
        else:
            embeddings.append([0.0] * 1536)  # Заглушка
    return embeddings

# 🛠️ ИСПРАВЛЕНИЯ В СУЩЕСТВУЮЩИХ ФУНКЦИЯХ

# Исправляем функцию split_into_chunks если есть проблемы с extract_keywords
async def split_into_chunks(summary: str, document_id: int, user_id: int) -> List[Dict]:
    """
    Разбивает документ на чанки для векторизации
    Перенесено из vector_utils.py и адаптировано для PostgreSQL
    """
    import tiktoken
    
    encoder = tiktoken.encoding_for_model("gpt-4")
    paragraphs = summary.strip().split("\n\n")
    now_str = datetime.now().strftime("%Y-%m-%d")

    chunks = []
    chunk_index = 0

    for para in paragraphs:
        clean_text = para.strip()
        if len(clean_text) < 20:
            continue

        token_count = len(encoder.encode(clean_text))
        
        found_date = await extract_date_from_text(clean_text)
        chunk_date = found_date if found_date else now_str

        # 🔹 Извлекаем ключевые слова (безопасно)
        try:
            from gpt import extract_keywords
            keywords = await extract_keywords(clean_text)
        except Exception as e:
            logger.warning(f"Ошибка извлечения ключевых слов: {e}")
            keywords = []  # Используем пустой список при ошибке

        chunks.append({
            "chunk_text": clean_text,
            "chunk_index": chunk_index,
            "metadata": {
                "user_id": str(user_id),
                "document_id": str(document_id),
                "confirmed": 1,
                "source": "summary",
                "token_count": token_count,
                "created_at": chunk_date,
                "date_inside": found_date or "",
                "keywords": ", ".join(keywords) if keywords else ""
            }
        })
        chunk_index += 1
    
    # ❗ Удаляем последний чанк, если их больше одного (логика из vector_utils)
    if len(chunks) > 1:
        chunks = chunks[:-1]

    return chunks

# 🔧 ИСПРАВЛЕНИЕ ФУНКЦИИ ИНИЦИАЛИЗАЦИИ

async def initialize_vector_db_safe():
    """Безопасная инициализация векторной базы с проверками"""
    try:
        from db_postgresql import db_pool
        
        if db_pool is None:
            logger.error("❌ db_pool не инициализирован!")
            return False
            
        await initialize_vector_db(db_pool)
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации векторной базы: {e}")
        return False