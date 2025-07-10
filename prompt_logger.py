import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Настройка логирования для продакшена
logger = logging.getLogger(__name__)

async def get_recent_messages_formatted(user_id: int, limit: int = 6) -> str:
    """
    Получает последние сообщения ИСКЛЮЧАЯ текущее (последнее) сообщение
    """
    try:
        from db_postgresql import get_last_messages
        
        # Берем на 1 больше чтобы исключить последнее (текущее) сообщение
        recent_messages = await get_last_messages(user_id, limit=limit + 1)
        
        if not recent_messages:
            return "No recent messages"
        
        # ИСКЛЮЧАЕМ ПОСЛЕДНЕЕ СООБЩЕНИЕ (текущий вопрос)
        if len(recent_messages) > 1:
            recent_messages = recent_messages[:-1]  # Убираем последнее
        
        # ОБЕСПЕЧИВАЕМ ЧЕТНОЕ КОЛИЧЕСТВО (пары USER-BOT)
        if len(recent_messages) % 2 != 0:
            recent_messages = recent_messages[1:]  # Убираем первое если нечетное
        
        formatted_lines = []
        for msg in recent_messages:
            if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                role = "USER" if msg[0] == 'user' else "BOT"
                content = str(msg[1])
                
                # УМНАЯ ОЧИСТКА HTML ТЕГОВ
                import re
                content = re.sub(r'<[^>]+>', '', content)  # Убираем HTML теги
                
                # ОБРЕЗКА ДО 100 СИМВОЛОВ БЕЗ РАЗРЫВА СЛОВ
                if len(content) > 100:
                    content = content[:97]
                    # Найдем последний пробел чтобы не резать слово
                    last_space = content.rfind(' ')
                    if last_space > 80:  # Если пробел не слишком близко к началу
                        content = content[:last_space]
                    content += "..."
                
                formatted_lines.append(f"{role}: {content}")
        
        # ОГРАНИЧИВАЕМ ДО 3 ПАР (6 сообщений)
        if len(formatted_lines) > 6:
            formatted_lines = formatted_lines[-6:]
        
        return "\n".join(formatted_lines) if formatted_lines else "No recent messages"
        
    except Exception as e:
        return "Recent messages unavailable"

async def get_medical_timeline_simple(user_id: int, limit: int = 6) -> str:
    """
    Простая функция для получения медкарты в компактном виде
    """
    try:
        from db_postgresql import get_db_connection, release_db_connection
        
        conn = await get_db_connection()
        
        # Получаем последние записи
        rows = await conn.fetch("""
            SELECT event_date, description, importance
            FROM medical_timeline 
            WHERE user_id = $1 
            ORDER BY event_date DESC, created_at DESC
            LIMIT $2
        """, user_id, limit)
        
        if not rows:
            return "Medical timeline: empty"
        
        # Форматируем компактно
        lines = []
        for row in rows:
            date_str = row['event_date'].strftime('%d.%m.%Y') if row['event_date'] else 'N/A'
            importance = row['importance'] or 'normal'
            description = (row['description'] or '')[:80]  # Ограничиваем длину
            
            # Добавляем эмодзи важности
            emoji = '🔴' if importance == 'critical' else '🟡' if importance == 'important' else '⚪'
            lines.append(f"{emoji} {date_str}: {description}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return "Medical timeline: unavailable"
    finally:
        if 'conn' in locals():
            await release_db_connection(conn)

async def get_user_vector_count(user_id: int) -> int:
    """
    Получает количество векторов пользователя
    """
    try:
        from vector_db_postgresql import vector_db
        if not vector_db:
            return 0
            
        conn = await vector_db.db_pool.acquire()
        try:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM document_vectors WHERE user_id = $1", 
                user_id
            )
            return result or 0
        finally:
            await vector_db.db_pool.release(conn)
    except Exception as e:
        return 0

async def get_all_user_chunks(user_id: int, limit: int = 4) -> List[Dict]:
    """
    Получает ВСЕ чанки пользователя (для случаев с малым количеством данных)
    """
    try:
        from vector_db_postgresql import vector_db
        if not vector_db:
            return []
            
        conn = await vector_db.db_pool.acquire()
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
                WHERE dv.user_id = $1
                ORDER BY d.uploaded_at DESC
                LIMIT $2
            """, user_id, limit)
            
            chunks = []
            for row in results:
                try:
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                except:
                    metadata = {}
                
                chunks.append({
                    "chunk_text": row['chunk_text'],
                    "metadata": metadata,
                    "keywords": row['keywords'],
                    "document_title": row['document_title'],
                    "uploaded_at": row['uploaded_at']
                })
            
            return chunks
        finally:
            await vector_db.db_pool.release(conn)
    except Exception as e:
        return []

async def process_user_question_detailed(user_id: int, user_input: str) -> Dict:
    """
    ГЛАВНАЯ ФУНКЦИЯ: Обрабатывает вопрос пользователя с оптимизацией
    
    Логика оптимизации:
    - 0 векторов: пропускаем поиск
    - 1-4 вектора: берем все без поиска  
    - 5+ векторов: делаем полный поиск
    
    Returns:
        Dict с данными для финального промта
    """
    
    try:
        # ШАГ 1: Проверка векторной базы
        vector_count = await get_user_vector_count(user_id)
        
        # ШАГ 2: Получение профиля пользователя
        try:
            from save_utils import format_user_profile
            profile_text = await format_user_profile(user_id)
        except Exception as e:
            profile_text = "Профиль пациента не заполнен"
        
        # ШАГ 3: Получение сводки разговора
        try:
            from db_postgresql import get_conversation_summary
            summary_text, _ = await get_conversation_summary(user_id)
            
            if not summary_text:
                summary_text = "Новый пациент, предыдущих бесед нет"
                
        except Exception as e:
            summary_text = "Ошибка получения сводки разговора"
        
        # ШАГ 4: Обработка векторов (оптимизированная)
        if vector_count == 0:
            # Пустая база: пропускаем поиск
            chunks_text = "У пользователя нет загруженных медицинских документов"
            chunks_found = 0
            
        elif vector_count <= 4:
            # Мало векторов: берем все
            all_chunks = await get_all_user_chunks(user_id, limit=4)
            
            if all_chunks:
                chunk_texts = [chunk.get("chunk_text", "") for chunk in all_chunks if chunk.get("chunk_text", "").strip()]
                chunks_text = "\n\n".join(chunk_texts)
                chunks_found = len(chunk_texts)
            else:
                chunks_text = "Не удалось загрузить данные"
                chunks_found = 0
                
        else:
            # Много векторов: полный поиск
            try:
                # Улучшение запроса
                from gpt import enrich_query_for_vector_search, extract_keywords
                
                refined_query = await enrich_query_for_vector_search(user_input)
                keywords = await extract_keywords(user_input)
                
            except Exception as e:
                refined_query = user_input
                keywords = []
            
            # Семантический поиск
            try:
                from vector_db_postgresql import search_similar_chunks
                vector_chunks = await search_similar_chunks(user_id, refined_query, limit=10)
            except Exception as e:
                vector_chunks = []
            
            # Поиск по ключевым словам
            try:
                from vector_db_postgresql import keyword_search_chunks
                keyword_list_str = ", ".join(keywords) if keywords else user_input
                keyword_chunks = await keyword_search_chunks(user_id, keyword_list_str, limit=5)
            except Exception as e:
                keyword_chunks = []
            
            # Гибридное ранжирование
            try:
                from vector_db_postgresql import create_hybrid_ranking
                
                ranked_chunk_texts = create_hybrid_ranking(
                    vector_chunks=vector_chunks,
                    keyword_chunks=keyword_chunks,
                    boost_factor=1.8
                )
                
                selected_chunks = ranked_chunk_texts[:5]
                chunks_text = "\n\n".join(selected_chunks)
                chunks_found = len(selected_chunks)
                
            except Exception as e:
                # Fallback на простое объединение
                vector_texts = [chunk.get("chunk_text", "") for chunk in vector_chunks[:3] if chunk.get("chunk_text", "").strip()]
                keyword_texts = [chunk.get("chunk_text", "") for chunk in keyword_chunks[:2] if chunk.get("chunk_text", "").strip()]
                all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
                chunks_text = "\n\n".join(all_chunks[:5])
                chunks_found = len(all_chunks)
        
        # ШАГ 5: Получение языка и создание системного промта
        try:
            from db_postgresql import get_user_language
            lang = await get_user_language(user_id)
            
            system_prompt = (
                "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
                "You speak in a friendly, human tone and provide explanations when needed. "
                f"Always respond in the '{lang}' language."
            )
            
        except Exception as e:
            system_prompt = "You are a helpful medical assistant."
            lang = 'ru'
        
        # ШАГ 6: Получение медкарты
        try:
            medical_timeline = await get_medical_timeline_simple(user_id, limit=6)
        except Exception as e:
            medical_timeline = "Medical timeline: unavailable"
        
        # ШАГ 7: Получение последних сообщений
        try:
            recent_messages_text = await get_recent_messages_formatted(user_id, limit=6)
        except Exception as e:
            recent_messages_text = "Recent messages unavailable"

        # ШАГ 8: Создание финального промта
        user_prompt_parts = [            
            f"📌 Patient profile:\n{profile_text}",
            "",
            f"🧠 Conversation summary:\n{summary_text}",
            "",
            f"🏥 Medical timeline:\n{medical_timeline}",
            "",
            f"🔎 Related historical data:\n{chunks_text or 'Релевантная информация не найдена'}",
            "",
            f"💬 Recent messages (last 3 pairs):\n{recent_messages_text}",
            "",
            f"Patient: {user_input}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
   
        return {
            "profile_text": profile_text,
            "summary_text": summary_text,
            "medical_timeline": medical_timeline,
            "recent_messages": recent_messages_text,
            "chunks_text": chunks_text or "Релевантная информация не найдена",
            "chunks_found": chunks_found,
            "lang": lang,
            "context_text": final_user_prompt,
            "vector_count": vector_count
        }
        
    except Exception as e:
        from error_handler import log_error_with_context
        log_error_with_context(e, {
            "function": "process_user_question_detailed"
        })
        raise