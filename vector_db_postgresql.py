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
        """Проверяет существование таблиц для векторного поиска (без создания)"""
        
        check_tables_sql = """
        -- 🔍 Проверяем, что pgvector расширение включено
        SELECT EXISTS(
            SELECT 1 FROM pg_extension WHERE extname = 'vector'
        ) as pgvector_enabled;
        """
        
        conn = await self.db_pool.acquire()
        try:
            # Проверяем pgvector
            result = await conn.fetchrow("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector') as pgvector_enabled")
            
            if not result['pgvector_enabled']:
                raise Exception("❌ pgvector расширение не включено в PostgreSQL")
            
            # Проверяем таблицу document_vectors
            result = await conn.fetchrow("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'document_vectors'
                ) as table_exists
            """)
            
            if not result['table_exists']:
                raise Exception("❌ Таблица document_vectors не существует")
            
            logger.info("✅ Векторные таблицы PostgreSQL готовы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки векторных таблиц: {e}")
            raise
        finally:
            await self.db_pool.release(conn)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Получает эмбеддинг от OpenAI"""
        try:
            # ✅ СОЗДАЕМ КЛИЕНТ ТОЛЬКО КОГДА НУЖЕН:
            client = get_openai_client()
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text.replace("\n", " ")[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
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
                    f"[{','.join(map(str, embedding))}]",
                    json.dumps(chunk['metadata']),
                    chunk['metadata'].get('keywords', '')
                )

            return True
            
        except Exception as e:
            return False
        finally:
            await self.db_pool.release(conn)
    
    async def search_similar_chunks(self, user_id: int, query: str, limit: int = 5, similarity_threshold: float = 0.3) -> List[Dict]:
        """
        Векторный поиск с фильтрацией по порогу релевантности
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Максимальное количество результатов
            similarity_threshold: Минимальный порог сходства (0.0-1.0)
                - 0.85+ = очень релевантные результаты
                - 0.7+ = релевантные результаты  
                - 0.5+ = умеренно релевантные
                - <0.5 = слабо релевантные (лучше исключить)
                
        Returns:
            Список релевантных чанков, отсортированных по similarity
        """
        conn = await self.db_pool.acquire()
        try:
            # 🧠 Получаем эмбеддинг запроса
            query_embedding = await self.get_embedding(query)
            
            # 🔧 ИСПРАВЛЕНИЕ: Конвертируем list в строку для PostgreSQL
            if isinstance(query_embedding, list):
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            else:
                embedding_str = query_embedding
                                    
            # 🔍 Векторный поиск с фильтрацией по threshold
            # Ищем больше результатов для последующей фильтрации
            search_limit = min(limit * 3, 20)  # Не больше 20 для производительности
            
            results = await conn.fetch("""
                WITH ranked_chunks AS (
                    SELECT 
                        dv.chunk_text,
                        dv.metadata,
                        dv.keywords,
                        d.title as document_title,
                        d.uploaded_at,
                        (dv.embedding <=> $1::vector) as distance,
                        (1 - (dv.embedding <=> $1::vector)) as similarity,
                        -- 📊 Дополнительные факторы ранжирования
                        CASE 
                            WHEN d.uploaded_at > NOW() - INTERVAL '30 days' THEN 0.1
                            WHEN d.uploaded_at > NOW() - INTERVAL '90 days' THEN 0.05
                            ELSE 0.0
                        END as recency_boost,
                        LENGTH(dv.chunk_text) as chunk_length
                    FROM document_vectors dv
                    JOIN documents d ON d.id = dv.document_id
                    WHERE dv.user_id = $2 AND d.confirmed = true
                    ORDER BY dv.embedding <=> $1::vector
                    LIMIT $3
                )
                SELECT 
                    chunk_text,
                    metadata,
                    keywords,
                    document_title,
                    uploaded_at,
                    distance,
                    similarity,
                    (similarity + recency_boost) as final_score,
                    chunk_length
                FROM ranked_chunks
                WHERE similarity >= $4  -- 🎯 ФИЛЬТРАЦИЯ ПО THRESHOLD
                ORDER BY final_score DESC, similarity DESC
                LIMIT $5
            """, embedding_str, user_id, search_limit, similarity_threshold, limit)
            
            # 📊 Форматируем результаты с подробной информацией
            chunks = []
            for row in results:
                # Безопасная обработка metadata
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
                
                chunk_data = {
                    "chunk_text": row['chunk_text'],
                    "metadata": metadata,
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at'],
                    "similarity": round(float(row['similarity']), 3),
                    "final_score": round(float(row['final_score']), 3),
                    "chunk_length": row['chunk_length']
                }
                chunks.append(chunk_data)
                
            return chunks
            
        except Exception as e:
            return []
        finally:
            await self.db_pool.release(conn)
    
    async def keyword_search_chunks(self, user_id: int, keywords: str, limit: int = 5) -> List[Dict]:
        """
        🔍 УЛУЧШЕННЫЙ поиск по ключевым словам с точным подсчетом совпадений
        
        Теперь точно считает совпавшие ключевые слова:
        - "УЗИ печени" найдет чанки с обоими словами выше чем с одним
        - Автоматически ранжирует по количеству совпадений
        """
        conn = await self.db_pool.acquire()
        try:
            
            # 🔹 Разбиваем и очищаем ключевые слова
            keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
            
            if not keyword_list:
                return []

            # 🔧 Создаем SQL с точным подсчетом каждого ключевого слова
            params = [user_id]
            param_index = 2
            
            # Создаем отдельные условия для каждого ключевого слова
            match_conditions = []
            
            for keyword in keyword_list:
                match_conditions.append(f"dv.keywords ILIKE ${param_index}")
                params.append(f'%{keyword}%')
                param_index += 1
            
            # Общее условие поиска (любое совпадение)
            where_clause = " OR ".join(match_conditions)
            
            # Подсчет общего количества совпадений
            total_matches = " + ".join([f"CASE WHEN dv.keywords ILIKE ${i+2} THEN 1 ELSE 0 END" 
                                    for i, _ in enumerate(keyword_list)])
            
            sql = f"""
                WITH keyword_analysis AS (
                    SELECT 
                        dv.chunk_text,
                        dv.metadata,
                        dv.keywords,
                        d.title as document_title,
                        d.uploaded_at,
                        
                        -- 📊 ТОЧНЫЙ ПОДСЧЕТ СОВПАДЕНИЙ
                        ({total_matches}) as exact_matches_count,
                        
                        -- 📏 ДЛИНА ТЕКСТА (для нормализации)
                        LENGTH(dv.keywords) as keywords_length
                        
                    FROM document_vectors dv
                    JOIN documents d ON d.id = dv.document_id
                    WHERE dv.user_id = $1
                    AND d.confirmed = true
                    AND ({where_clause})
                ),
                scored_chunks AS (
                    SELECT *,
                        -- 🏆 УЛУЧШЕННЫЙ SCORE:
                        (
                            -- Количество совпадений * 10 (основной фактор)
                            exact_matches_count * 10.0 +
                            
                            -- Бонус за полное совпадение всех ключевых слов
                            CASE WHEN exact_matches_count = {len(keyword_list)} THEN 5.0 ELSE 0.0 END +
                            
                            -- Плотность ключевых слов
                            CASE WHEN keywords_length > 0 THEN 
                                (exact_matches_count::float / keywords_length * 100) * 2.0 
                            ELSE 0.0 END +
                            
                            -- Бонус за новизну документа
                            CASE 
                                WHEN uploaded_at > NOW() - INTERVAL '7 days' THEN 3.0
                                WHEN uploaded_at > NOW() - INTERVAL '30 days' THEN 1.5
                                WHEN uploaded_at > NOW() - INTERVAL '90 days' THEN 0.5
                                ELSE 0.0
                            END
                        ) as advanced_score
                        
                    FROM keyword_analysis
                    WHERE exact_matches_count > 0
                )
                SELECT 
                    chunk_text,
                    metadata,
                    keywords,
                    document_title,
                    uploaded_at,
                    exact_matches_count,
                    advanced_score,
                    -- ✅ ДЛЯ СОВМЕСТИМОСТИ с существующим кодом:
                    advanced_score as rank,
                    exact_matches_count as matches_count
                FROM scored_chunks
                ORDER BY 
                    exact_matches_count DESC,      -- 🥇 Сначала по количеству совпадений
                    advanced_score DESC,           -- 🥈 Потом по продвинутому score  
                    uploaded_at DESC               -- 🥉 Потом по новизне
                LIMIT {limit}
            """
            
            results = await conn.fetch(sql, *params)
            
            # 📊 Форматируем результаты (совместимо с существующим кодом)
            chunks = []
            for row in results:
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
                
                chunk_data = {
                    "chunk_text": row['chunk_text'],
                    "metadata": metadata,
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at'],
                    "rank": round(float(row['rank']), 3),                    # ✅ Совместимость
                    "matches_count": int(row['matches_count']),              # ✅ Совместимость
                    "exact_matches_count": int(row['exact_matches_count']),  # 🆕 Новое поле
                    "advanced_score": round(float(row['advanced_score']), 3) # 🆕 Новое поле
                }
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
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
            return True
        except Exception as e:
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
            return True
        except Exception as e:
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
            return {"total_vectors": 0, "unique_users": 0, "unique_documents": 0}
        finally:
            await self.db_pool.release(conn)
    
    async def count_user_vectors(self, user_id: int) -> int:
        """
        🔍 НОВАЯ ФУНКЦИЯ: Подсчитывает количество векторов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество векторов в базе
        """
        conn = await self.db_pool.acquire()
        try:
            result = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM document_vectors 
                WHERE user_id = $1
            """, user_id)
            
            count = result or 0
            return count
            
        except Exception as e:
            return 0
        finally:
            await self.db_pool.release(conn)

    async def get_all_user_chunks(self, user_id: int, limit: int = 4) -> List[Dict]:
        """
        📥 НОВАЯ ФУНКЦИЯ: Получает ВСЕ чанки пользователя (для малых баз)
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            
        Returns:
            List[Dict]: Все записи пользователя из векторной базы
        """
        conn = await self.db_pool.acquire()
        try:
            results = await conn.fetch("""
                SELECT 
                    dv.chunk_text,
                    dv.metadata,
                    dv.keywords,
                    d.title as document_title,
                    d.uploaded_at
                FROM document_vectors dv
                JOIN documents d ON d.id = dv.document_id
                WHERE dv.user_id = $1 AND d.confirmed = true
                ORDER BY d.uploaded_at DESC, dv.id DESC
                LIMIT $2
            """, user_id, limit)
            
            chunks = []
            for row in results:
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
                
                chunk_data = {
                    "chunk_text": row['chunk_text'],
                    "metadata": metadata,
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at'],
                    "similarity": 1.0,  # Все записи одинаково релевантны
                    "final_score": 1.0
                }
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            return []
        finally:
            await self.db_pool.release(conn)

# 🌐 ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР (будет инициализирован в main.py)
vector_db: Optional[PostgreSQLVectorDB] = None

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

async def close_vector_db():
    """Закрывает векторную базу данных"""
    global vector_db
    if vector_db and vector_db.db_pool:
        try:
            # Векторная БД использует ТОТ ЖЕ пул что и основная БД
            # Поэтому просто обнуляем ссылку
            vector_db = None
            logger.info("✅ Векторная БД закрыта")
        except Exception as e:
            logger.error(f"⚠️ Ошибка закрытия векторной БД: {e}")

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
     

    return chunks

# 🔧 ИСПРАВЛЕНИЕ ФУНКЦИИ ИНИЦИАЛИЗАЦИИ

async def initialize_vector_db_safe():
    """Безопасная инициализация векторной базы с проверками"""
    try:
        from db_postgresql import db_pool
        
        if db_pool is None:
            return False
            
        await initialize_vector_db(db_pool)
        return True
        
    except Exception as e:
        return False
    
def create_hybrid_ranking(vector_chunks: List[Dict], keyword_chunks: List[Dict], 
                         boost_factor: float = 1.8) -> List[str]:
    """
    🧠 ГИБРИДНЫЙ ПОИСК с boost-фактором для чанков, найденных в обоих поисках
    
    Args:
        vector_chunks: Результаты векторного поиска
        keyword_chunks: Результаты поиска по ключевым словам  
        boost_factor: Множитель для чанков из обоих поисков (1.8 = +80%)
    
    Returns:
        Список текстов чанков, отсортированных по гибридному score
    """
    
    chunk_scores = {}  # chunk_text -> score_data
    
    # ==========================================
    # ШАГ 1: ОБРАБАТЫВАЕМ ВЕКТОРНЫЕ РЕЗУЛЬТАТЫ
    # ==========================================
    for i, chunk in enumerate(vector_chunks):
        chunk_text = chunk.get("chunk_text", "").strip()
        if not chunk_text:
            continue
            
        # Нормализуем similarity (0.0-1.0) в score (0.0-10.0)
        vector_score = chunk.get("similarity", 0.0) * 10
        
        # Бонус за позицию в векторном поиске (топ результаты важнее)
        position_bonus = max(0, (len(vector_chunks) - i) * 0.1)
        
        chunk_scores[chunk_text] = {
            "vector_score": vector_score + position_bonus,
            "keyword_score": 0.0,
            "keyword_matches": 0,
            "found_in_vector": True,
            "found_in_keywords": False
        }
    
    # ==========================================
    # ШАГ 2: ОБРАБАТЫВАЕМ КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ
    # ==========================================
    for i, chunk in enumerate(keyword_chunks):
        chunk_text = chunk.get("chunk_text", "").strip()
        if not chunk_text:
            continue
            
        # Используем улучшенный score из новой функции keyword_search_chunks
        keyword_score = chunk.get("rank", 0.0)
        keyword_matches = chunk.get("matches_count", 0)
        
        # Бонус за позицию в ключевом поиске
        position_bonus = max(0, (len(keyword_chunks) - i) * 0.2)
        
        if chunk_text in chunk_scores:
            # 🔥 НАЙДЕН В ОБОИХ ПОИСКАХ - ПРИМЕНЯЕМ BOOST!
            chunk_scores[chunk_text]["keyword_score"] = keyword_score + position_bonus
            chunk_scores[chunk_text]["keyword_matches"] = keyword_matches
            chunk_scores[chunk_text]["found_in_keywords"] = True
        else:
            # Найден только в ключевом поиске
            chunk_scores[chunk_text] = {
                "vector_score": 0.0,
                "keyword_score": keyword_score + position_bonus,
                "keyword_matches": keyword_matches,
                "found_in_vector": False,
                "found_in_keywords": True
            }
    
    # ==========================================
    # ШАГ 3: ВЫЧИСЛЯЕМ ФИНАЛЬНЫЕ SCORES
    # ==========================================
    scored_chunks = []
    
    for chunk_text, data in chunk_scores.items():
        vector_score = data["vector_score"]
        keyword_score = data["keyword_score"] 
        keyword_matches = data["keyword_matches"]
        
        if data["found_in_vector"] and data["found_in_keywords"]:
            # 🚀 ГИБРИДНЫЙ РЕЗУЛЬТАТ с boost
            base_score = (vector_score + keyword_score) / 2
            
            # Дополнительный boost за количество совпавших ключевых слов
            matches_multiplier = 1.0 + (keyword_matches * 0.15)  # +15% за каждое совпадение
            
            final_score = base_score * boost_factor * matches_multiplier
            search_type = f"🔥 HYBRID({keyword_matches})"
            
        elif data["found_in_vector"]:
            final_score = vector_score
            search_type = "🧠 VECTOR"
        else:
            # Ключевой результат с бонусом за совпадения
            matches_multiplier = 1.0 + (keyword_matches * 0.1)
            final_score = keyword_score * matches_multiplier
            search_type = f"🔑 KEYWORD({keyword_matches})"
        
        scored_chunks.append({
            "chunk_text": chunk_text,
            "final_score": final_score,
            "search_type": search_type,
            "keyword_matches": keyword_matches,
            "is_hybrid": data["found_in_vector"] and data["found_in_keywords"]
        })
    
    # ==========================================
    # ШАГ 4: СОРТИРОВКА ПО ПРИОРИТЕТУ
    # ==========================================
    def sort_key(item):
        # Приоритет: гибридные > количество совпадений > финальный score
        return (item["is_hybrid"], item["keyword_matches"], item["final_score"])
    
    scored_chunks.sort(key=sort_key, reverse=True)
    
    # 📊 Подробное логирование
    hybrid_count = sum(1 for c in scored_chunks if c["is_hybrid"])
    
    # Показываем топ-5 результатов
    for i, item in enumerate(scored_chunks[:5]):
        score = item["final_score"]
        search_type = item["search_type"]
        preview = item["chunk_text"][:50] + "..."
    
    # Возвращаем только тексты чанков (для совместимости)
    return [item["chunk_text"] for item in scored_chunks]

async def count_user_vectors(user_id: int) -> int:
    """Подсчитывает векторы пользователя (совместимость)"""
    if vector_db:
        return await vector_db.count_user_vectors(user_id)
    return 0

async def get_all_user_chunks(user_id: int, limit: int = 4) -> List[Dict]:
    """Получает все чанки пользователя (совместимость)"""
    if vector_db:
        return await vector_db.get_all_user_chunks(user_id, limit)
    return []

async def delete_chunks_by_document(document_id: int) -> bool:
    """Удаляет все векторы документа из базы"""
    if vector_db:
        try:
            conn = await vector_db.db_pool.acquire()
            try:
                await conn.execute(
                    "DELETE FROM document_vectors WHERE document_id = $1",
                    document_id
                )
                logger.info(f"✅ Векторы документа {document_id} удалены")
                return True
            finally:
                await vector_db.db_pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Ошибка удаления векторов документа {document_id}: {e}")
            return False
    return False