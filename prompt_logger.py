import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

def log_step(step_num: int, title: str, content: str = "", success: bool = True):
    """Логирует шаг процесса с красивым форматированием"""
    status = "✅" if success else "❌"
    separator = "=" * 60
    
    print(f"\n{separator}")
    print(f"{status} ШАГ {step_num}: {title}")
    print(f"{separator}")
    if content:
        print(content)

def log_chunk_info(chunks: list, chunk_type: str):
    """Логирует информацию о найденных чанках"""
    print(f"\n📊 {chunk_type}: найдено {len(chunks)} чанков")
    for i, chunk in enumerate(chunks[:3]):  # Показываем только первые 3
        chunk_text = chunk.get('chunk_text', '')[:100]
        similarity = chunk.get('similarity', chunk.get('rank', 'N/A'))
        if isinstance(similarity, (int, float)):
            print(f"   {i+1}. [🎯{similarity:.3f}] {chunk_text}...")
        else:
            print(f"   {i+1}. [📊{similarity}] {chunk_text}...")
    if len(chunks) > 3:
        print(f"   ... и еще {len(chunks) - 3} чанков")

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
        
        # ✅ ИСКЛЮЧАЕМ ПОСЛЕДНЕЕ СООБЩЕНИЕ (текущий вопрос)
        if len(recent_messages) > 1:
            recent_messages = recent_messages[:-1]  # Убираем последнее
        
        # ✅ ОБЕСПЕЧИВАЕМ ЧЕТНОЕ КОЛИЧЕСТВО (пары USER-BOT)
        if len(recent_messages) % 2 != 0:
            recent_messages = recent_messages[1:]  # Убираем первое если нечетное
        
        formatted_lines = []
        for msg in recent_messages:
            if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                role = "USER" if msg[0] == 'user' else "BOT"
                content = str(msg[1])
                
                # ✅ УМНАЯ ОЧИСТКА HTML ТЕГОВ
                import re
                content = re.sub(r'<[^>]+>', '', content)  # Убираем HTML теги
                
                # ✅ ОБРЕЗКА ДО 100 СИМВОЛОВ БЕЗ РАЗРЫВА СЛОВ
                if len(content) > 100:
                    content = content[:97]
                    # Найдем последний пробел чтобы не резать слово
                    last_space = content.rfind(' ')
                    if last_space > 80:  # Если пробел не слишком близко к началу
                        content = content[:last_space]
                    content += "..."
                
                formatted_lines.append(f"{role}: {content}")
        
        # ✅ ОГРАНИЧИВАЕМ ДО 3 ПАР (6 сообщений)
        if len(formatted_lines) > 6:
            formatted_lines = formatted_lines[-6:]
        
        return "\n".join(formatted_lines) if formatted_lines else "No recent messages"
        
    except Exception as e:
        print(f"❌ Ошибка получения последних сообщений: {e}")
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
        print(f"❌ Ошибка получения медкарты: {e}")
        return "Medical timeline: unavailable"
    finally:
        if 'conn' in locals():
            await release_db_connection(conn)

async def get_user_vector_count(user_id: int) -> int:
    """
    🔍 Получает количество векторов пользователя (ПРОСТАЯ версия)
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
        print(f"❌ Ошибка подсчета векторов: {e}")
        return 0

async def get_all_user_chunks(user_id: int, limit: int = 4) -> List[Dict]:
    """
    📥 Получает ВСЕ чанки пользователя (ПРОСТАЯ версия)
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
        print(f"❌ Ошибка получения всех чанков: {e}")
        return []

async def process_user_question_detailed(user_id: int, user_input: str) -> Dict:
    """
    🔍 ГЛАВНАЯ ФУНКЦИЯ: Обрабатывает вопрос пользователя с ПРОСТОЙ оптимизацией
    
    Логика:
    - 0 векторов: пропускаем поиск
    - 1-4 вектора: берем все без поиска  
    - 5+ векторов: делаем полный поиск
    
    Returns:
        Dict с данными для финального промта
    """
    
    # ==========================================
    # ШАГ 1: ПОЛУЧЕНИЕ ВОПРОСА ПОЛЬЗОВАТЕЛЯ
    # ==========================================
    log_step(1, "ПОЛУЧЕНИЕ ВОПРОСА ПОЛЬЗОВАТЕЛЯ", 
             f"👤 Пользователь {user_id}\n💬 Вопрос: '{user_input}'")
    
    try:
        # ==========================================
        # ШАГ 2: ПРОВЕРКА ВЕКТОРНОЙ БАЗЫ (НОВОЕ!)
        # ==========================================
        log_step(2, "🚀 ПРОВЕРКА ВЕКТОРНОЙ БАЗЫ")
        
        vector_count = await get_user_vector_count(user_id)
        print(f"📊 У пользователя {user_id} векторов: {vector_count}")
        
        # ==========================================
        # ШАГ 3: ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
        # ==========================================
        log_step(3, "ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ")
        
        try:
            from save_utils import format_user_profile
            profile_text = await format_user_profile(user_id)
            print(f"👤 Профиль получен: {len(profile_text)} символов")
        except Exception as e:
            profile_text = "Профиль пациента не заполнен"
            print(f"❌ Ошибка получения профиля: {e}")
        
        # ==========================================
        # ШАГ 4: ПОЛУЧЕНИЕ СВОДКИ РАЗГОВОРА
        # ==========================================
        log_step(4, "ПОЛУЧЕНИЕ СВОДКИ РАЗГОВОРА")
        
        try:
            from db_postgresql import get_conversation_summary
            summary_text, _ = await get_conversation_summary(user_id)
            
            if not summary_text:
                summary_text = "Новый пациент, предыдущих бесед нет"
                
            print(f"🧠 Сводка получена: {len(summary_text)} символов")
        except Exception as e:
            summary_text = "Ошибка получения сводки разговора"
            print(f"❌ Ошибка получения сводки: {e}")
        
        # ==========================================
        # ШАГ 5: УМНАЯ ОБРАБОТКА ВЕКТОРОВ
        # ==========================================
        
        if vector_count == 0:
            # 🚀 ПУСТАЯ БАЗА: пропускаем поиск
            log_step(5, "🚀 ПРОПУСК: Векторная база пустая")
            chunks_text = "У пользователя нет загруженных медицинских документов"
            chunks_found = 0
            print("💰 ЭКОНОМИЯ: Пропущены GPT вызовы для поиска")
            
        elif vector_count <= 4:
            # 🎯 МАЛО ВЕКТОРОВ: берем все
            log_step(5, f"🎯 БЕРЕМ ВСЕ: {vector_count} векторов")
            
            all_chunks = await get_all_user_chunks(user_id, limit=4)
            
            if all_chunks:
                chunk_texts = [chunk.get("chunk_text", "") for chunk in all_chunks if chunk.get("chunk_text", "").strip()]
                chunks_text = "\n\n".join(chunk_texts)
                chunks_found = len(chunk_texts)
                print(f"📦 Загружено {chunks_found} записей без поиска")
                print("💰 ЭКОНОМИЯ: Пропущены GPT вызовы для поиска")
            else:
                chunks_text = "Не удалось загрузить данные"
                chunks_found = 0
                
        else:
            # 🔍 МНОГО ВЕКТОРОВ: полный поиск как в рабочей версии
            log_step(5, f"🔍 ПОЛНЫЙ ПОИСК: {vector_count} векторов")
            
            # ШАГ 5A: УЛУЧШЕНИЕ ЗАПРОСА
            try:
                from gpt import enrich_query_for_vector_search, extract_keywords
                
                refined_query = await enrich_query_for_vector_search(user_input)
                print(f"🔍 Исходный: '{user_input}'")
                print(f"🎯 Улучшенный: '{refined_query}'")
                
                keywords = await extract_keywords(user_input)
                print(f"🔑 Ключевые слова: {keywords}")
                
            except Exception as e:
                refined_query = user_input
                keywords = []
                print(f"❌ Ошибка обработки запроса: {e}")
            
            # ШАГ 5B: СЕМАНТИЧЕСКИЙ ПОИСК
            try:
                from vector_db_postgresql import search_similar_chunks
                vector_chunks = await search_similar_chunks(user_id, refined_query, limit=10)
                
                if vector_chunks:
                    log_chunk_info(vector_chunks, "СЕМАНТИЧЕСКИЕ ЧАНКИ")
                else:
                    print("❌ Семантических чанков не найдено")
                    
            except Exception as e:
                vector_chunks = []
                print(f"❌ Ошибка семантического поиска: {e}")
            
            # ШАГ 5C: ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ
            try:
                from vector_db_postgresql import keyword_search_chunks
                keyword_list_str = ", ".join(keywords) if keywords else user_input
                keyword_chunks = await keyword_search_chunks(user_id, keyword_list_str, limit=5)
                
                if keyword_chunks:
                    log_chunk_info(keyword_chunks, "КЛЮЧЕВЫЕ ЧАНКИ")
                else:
                    print("❌ Чанков по ключевым словам не найдено")
                    
            except Exception as e:
                keyword_chunks = []
                print(f"❌ Ошибка поиска по ключевым словам: {e}")
            
            # ШАГ 5D: ГИБРИДНОЕ РАНЖИРОВАНИЕ (ИСПРАВЛЕНО!)
            try:
                # ✅ ПРАВИЛЬНЫЙ ИМПОРТ
                from vector_db_postgresql import create_hybrid_ranking
                
                ranked_chunk_texts = create_hybrid_ranking(
                    vector_chunks=vector_chunks,
                    keyword_chunks=keyword_chunks,
                    boost_factor=1.8
                )
                
                selected_chunks = ranked_chunk_texts[:5]
                chunks_text = "\n\n".join(selected_chunks)
                chunks_found = len(selected_chunks)
                
                print(f"\n📦 ГИБРИДНЫЙ РЕЗУЛЬТАТ:")
                print(f"   🔥 Ранжированных чанков: {len(ranked_chunk_texts)}")
                print(f"   🎯 Отобрано для промпта: {chunks_found}")
                
            except Exception as e:
                print(f"❌ Ошибка гибридного ранжирования: {e}")
                # Fallback на простое объединение
                vector_texts = [chunk.get("chunk_text", "") for chunk in vector_chunks[:3] if chunk.get("chunk_text", "").strip()]
                keyword_texts = [chunk.get("chunk_text", "") for chunk in keyword_chunks[:2] if chunk.get("chunk_text", "").strip()]
                all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
                chunks_text = "\n\n".join(all_chunks[:5])
                chunks_found = len(all_chunks)
                print(f"📦 FALLBACK: {chunks_found} чанков")
        
        # ==========================================
        # ШАГ 6: СИСТЕМНЫЙ ПРОМТ
        # ==========================================
        log_step(6, "СОЗДАНИЕ СИСТЕМНОГО ПРОМТА")
        
        try:
            from db_postgresql import get_user_language
            lang = await get_user_language(user_id)
            
            system_prompt = (
                "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
                "You speak in a friendly, human tone and provide explanations when needed. "
                f"Always respond in the '{lang}' language."
            )
            
            print(f"🌐 Язык ответа: {lang}")
            
        except Exception as e:
            system_prompt = "You are a helpful medical assistant."
            lang = 'ru'
            print(f"❌ Ошибка создания системного промта: {e}")
        
        # ==========================================
        # ШАГ 7: ПОЛУЧЕНИЕ МЕДКАРТЫ
        # ==========================================
        log_step(7, "ПОЛУЧЕНИЕ МЕДКАРТЫ")
        
        try:
            medical_timeline = await get_medical_timeline_simple(user_id, limit=6)
            print(f"🏥 Медкарта получена: {len(medical_timeline)} символов")
        except Exception as e:
            medical_timeline = "Medical timeline: unavailable"
            print(f"❌ Ошибка получения медкарты: {e}")
        
        # ==========================================
        # ШАГ 8: ПОЛУЧЕНИЕ ПОСЛЕДНИХ СООБЩЕНИЙ
        # ==========================================
        log_step(8, "ПОЛУЧЕНИЕ ПОСЛЕДНИХ СООБЩЕНИЙ")
        
        try:
            recent_messages_text = await get_recent_messages_formatted(user_id, limit=6)
            print(f"💬 Последние сообщения получены: {len(recent_messages_text)} символов")
        except Exception as e:
            recent_messages_text = "Recent messages unavailable"
            print(f"❌ Ошибка получения последних сообщений: {e}")


        # ==========================================
        # ШАГ 9: СОЗДАНИЕ ФИНАЛЬНОГО ПРОМТА
        # ==========================================
        log_step(9, "СОЗДАНИЕ ФИНАЛЬНОГО ПРОМТА")
        
        user_prompt_parts = [            
            f"📌 Patient profile:\n{profile_text}",
            "",
            f"🧠 Conversation summary:\n{summary_text}",
            "",
            f"🏥 Medical timeline:\n{medical_timeline}",  # ← ДОБАВИТЬ МЕДКАРТУ
            "",
            f"🔎 Related historical data:\n{chunks_text or 'Релевантная информация не найдена'}",
            "",
            f"💬 Recent messages (last 3 pairs):\n{recent_messages_text}",  # ← ДОБАВИТЬ ПОСЛЕДНИЕ СООБЩЕНИЯ
            "",
            f"Patient: {user_input}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
        
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ПРОМПТА:")
        print(f"   🔧 Системный промт: {len(system_prompt)} символов")
        print(f"   👤 Профиль: {len(profile_text)} символов")
        print(f"   💭 Сводка: {len(summary_text)} символов")
        print(f"   🏥 Медкарта: {len(medical_timeline)} символов")
        print(f"   💬 Последние сообщения: {len(recent_messages_text)} символов")
        print(f"   🔎 Исторические данные: {len(chunks_text)} символов")
        print(f"   📏 ОБЩАЯ ДЛИНА: {len(final_user_prompt)} символов")
        print(f"   🎯 Примерно токенов: {len(final_user_prompt) // 4}")
        
        # Дополнительная статистика оптимизации
        if vector_count <= 4:
            print(f"\n💰 ЭКОНОМИЯ:")
            print(f"   📊 Векторов: {vector_count}")
            print(f"   💸 Пропущено GPT вызовов: 3")
            print(f"   ⚡ Режим: упрощенный")
        
        return {
            "profile_text": profile_text,
            "summary_text": summary_text,
            "medical_timeline": medical_timeline,
            "recent_messages": recent_messages_text,
            "chunks_text": chunks_text or "Релевантная информация не найдена",
            "chunks_found": chunks_found,
            "lang": lang if 'lang' in locals() else 'ru',
            "context_text": final_user_prompt,
            "vector_count": vector_count
        }
        
    except Exception as e:
        log_step(0, "КРИТИЧЕСКАЯ ОШИБКА", f"❌ {e}", success=False)
        raise