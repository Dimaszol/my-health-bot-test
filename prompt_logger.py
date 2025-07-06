# prompt_logger.py - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ с проверкой векторной базы

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

async def get_user_vector_count(user_id: int) -> int:
    """
    🔍 НОВАЯ ФУНКЦИЯ: Получает количество векторов пользователя
    
    Returns:
        int: Количество векторов в базе для данного пользователя
    """
    try:
        from vector_db_postgresql import vector_db
        if not vector_db:
            print("❌ Векторная база не инициализирована")
            return 0
            
        conn = await vector_db.db_pool.acquire()
        try:
            result = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM document_vectors 
                WHERE user_id = $1
            """, user_id)
            
            count = result or 0
            print(f"📊 У пользователя {user_id} в векторной базе: {count} записей")
            return count
            
        finally:
            await vector_db.db_pool.release(conn)
            
    except Exception as e:
        print(f"❌ Ошибка подсчета векторов для пользователя {user_id}: {e}")
        return 0

async def get_all_user_vectors(user_id: int, limit: int = 4) -> List[Dict]:
    """
    📥 НОВАЯ ФУНКЦИЯ: Получает ВСЕ векторы пользователя (для малых баз)
    
    Args:
        user_id: ID пользователя
        limit: Максимальное количество записей
        
    Returns:
        List[Dict]: Все записи пользователя из векторной базы
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
            
            print(f"📦 Получено {len(chunks)} записей из векторной базы пользователя {user_id}")
            return chunks
            
        finally:
            await vector_db.db_pool.release(conn)
            
    except Exception as e:
        print(f"❌ Ошибка получения всех векторов для пользователя {user_id}: {e}")
        return []

async def process_user_question_detailed(user_id: int, user_input: str) -> Dict:
    """
    🔍 ОПТИМИЗИРОВАННАЯ ГЛАВНАЯ ФУНКЦИЯ: Обрабатывает вопрос пользователя с умной оптимизацией
    
    Логика оптимизации:
    - 0 векторов: НЕ вызываем GPT для поиска, сразу отвечаем
    - 1-4 вектора: НЕ делаем поиск, берем ВСЕ векторы пользователя  
    - 5+ векторов: Делаем полный поиск как обычно
    
    Returns:
        Dict с данными для финального промпта
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
        log_step(2, "🚀 ОПТИМИЗАЦИЯ: ПРОВЕРКА ВЕКТОРНОЙ БАЗЫ")
        
        vector_count = await get_user_vector_count(user_id)
        
        if vector_count == 0:
            print("🎯 ОПТИМИЗАЦИЯ: Векторная база пустая - пропускаем ВСЕ GPT вызовы для поиска")
            search_mode = "empty"
        elif vector_count <= 4:
            print(f"🎯 ОПТИМИЗАЦИЯ: Мало векторов ({vector_count}) - берем ВСЕ без поиска")
            search_mode = "take_all"
        else:
            print(f"🎯 СТАНДАРТНЫЙ РЕЖИМ: Много векторов ({vector_count}) - делаем полный поиск")
            search_mode = "full_search"
        
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
        # ШАГ 5: УМНАЯ ОБРАБОТКА ВЕКТОРНОЙ БАЗЫ
        # ==========================================
        
        if search_mode == "empty":
            # 🚀 ОПТИМИЗАЦИЯ: Пустая база - никаких вызовов GPT
            log_step(5, "🚀 ПРОПУСК: Векторная база пустая")
            chunks_text = "У пользователя нет загруженных медицинских документов"
            chunks_found = 0
            print("💰 ЭКОНОМИЯ: Пропущено 3 вызова GPT (расширение запроса + ключевые слова + эмбеддинг)")
            
        elif search_mode == "take_all":
            # 🎯 ОПТИМИЗАЦИЯ: Мало векторов - берем все без поиска
            log_step(5, f"🎯 УМНАЯ ЗАГРУЗКА: Берем все {vector_count} записей без поиска")
            
            all_chunks = await get_all_user_vectors(user_id, limit=4)
            
            if all_chunks:
                # Преобразуем в текст
                chunk_texts = []
                for chunk in all_chunks:
                    chunk_text = chunk.get("chunk_text", "")
                    if chunk_text.strip():
                        chunk_texts.append(chunk_text)
                
                chunks_text = "\n\n".join(chunk_texts)
                chunks_found = len(chunk_texts)
                
                print(f"📦 Загружено {chunks_found} записей ({len(chunks_text)} символов)")
                print("💰 ЭКОНОМИЯ: Пропущено 3 вызова GPT (расширение запроса + ключевые слова + эмбеддинг)")
            else:
                chunks_text = "Не удалось загрузить данные из векторной базы"
                chunks_found = 0
                
        else:
            # 🔍 ПОЛНЫЙ ПОИСК: Много векторов - делаем как обычно
            log_step(5, "🔍 ПОЛНЫЙ ПОИСК: Расширение запроса и векторный поиск")
            
            # ШАГ 5A: УЛУЧШЕНИЕ ЗАПРОСА ДЛЯ ПОИСКА
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
                print(f"❌ Ошибка обработки запроса, используем исходный: {e}")
            
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
            
            # ШАГ 5D: ГИБРИДНОЕ РАНЖИРОВАНИЕ
            try:
                from save_utils import rank_chunks_hybrid
                
                ranked_chunk_texts = rank_chunks_hybrid(
                    vector_chunks=vector_chunks,
                    keyword_chunks=keyword_chunks,
                    query=user_input,
                    max_chunks=6
                )
                
                selected_chunks = ranked_chunk_texts[:6]
                chunks_text = "\n\n".join(selected_chunks)
                chunks_found = len(selected_chunks)
                
                print(f"\n📦 ИТОГОВЫЙ РЕЗУЛЬТАТ ГИБРИДНОГО ПОИСКА:")
                print(f"   🔥 Ранжированных чанков: {len(ranked_chunk_texts)}")
                print(f"   🎯 Отобрано для промпта: {chunks_found}")
                print(f"   📄 Символов контекста: {len(chunks_text)}")
                
            except Exception as e:
                print(f"❌ Ошибка гибридного ранжирования: {e}")
                # Fallback на простое объединение
                
                def filter_chunks_simple(chunks, limit=5):
                    filtered_texts = []
                    for chunk in chunks:
                        chunk_text = chunk.get("chunk_text", "")
                        if chunk_text.strip():
                            filtered_texts.append(chunk_text)
                            if len(filtered_texts) >= limit:
                                break
                    return filtered_texts

                vector_texts = filter_chunks_simple(vector_chunks, limit=3)
                keyword_texts = filter_chunks_simple(keyword_chunks, limit=2)
                all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
                chunks_text = "\n\n".join(all_chunks[:5])
                chunks_found = len(all_chunks)
                
                print(f"📦 FALLBACK: {chunks_found} чанков (простое объединение)")
        
        # ==========================================
        # ШАГ 6: СИСТЕМНЫЙ ПРОМТ
        # ==========================================
        log_step(6, "СОЗДАНИЕ СИСТЕМНОГО ПРОМПТА")
        
        try:
            from db_postgresql import get_user_language
            lang = await get_user_language(user_id)
            
            system_prompt = (
                "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
                "You speak in a friendly, human tone and provide explanations when needed. "
                f"Always respond in the '{lang}' language."
            )
            
            print(f"🌐 Язык ответа: {lang}")
            print(f"📏 Длина системного промта: {len(system_prompt)} символов")
            
        except Exception as e:
            system_prompt = "You are a helpful medical assistant."
            lang = 'ru'
            print(f"❌ Ошибка создания системного промта: {e}")
        
        # ==========================================
        # ШАГ 7: СОЗДАНИЕ ФИНАЛЬНОГО ПРОМПТА
        # ==========================================
        log_step(7, "СОЗДАНИЕ ФИНАЛЬНОГО ПРОМПТА")
        
        user_prompt_parts = [
            "Answer only questions related to the user's health. Do not repeat that you're an AI. Do not ask follow-up questions unless critical.",
            "",
            f"📌 Patient profile:\n{profile_text}",
            "",
            f"🧠 Conversation summary:\n{summary_text}",
            "",
            f"🔎 Related historical data:\n{chunks_text or 'Релевантная информация не найдена'}",
            "",
            f"Patient: {user_input}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
        
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ПРОМПТА:")
        print(f"   🔧 Системный промт: {len(system_prompt)} символов")
        print(f"   👤 Профиль: {len(profile_text)} символов")
        print(f"   💭 Сводка: {len(summary_text)} символов")
        print(f"   🔎 Исторические данные: {len(chunks_text)} символов")
        print(f"   📏 ОБЩАЯ ДЛИНА: {len(final_user_prompt)} символов")
        print(f"   🎯 Примерно токенов: {len(final_user_prompt) // 4}")
        
        # ==========================================
        # ШАГ 8: ФИНАЛЬНАЯ СВОДКА ОПТИМИЗАЦИЙ
        # ==========================================
        
        if search_mode in ["empty", "take_all"]:
            print(f"\n💰 ИТОГОВАЯ ЭКОНОМИЯ:")
            print(f"   🚀 Режим оптимизации: {search_mode}")
            print(f"   💸 Пропущено вызовов GPT: 3")
            print(f"   📊 Векторов в базе: {vector_count}")
            print(f"   ⚡ Время обработки: значительно сокращено")
        else:
            print(f"\n🔍 ПОЛНАЯ ОБРАБОТКА:")
            print(f"   📊 Векторов в базе: {vector_count}")
            print(f"   🧠 Использованы все GPT вызовы")
            print(f"   ⚡ Режим: полный поиск")
        
        return {
            "profile_text": profile_text,
            "summary_text": summary_text, 
            "chunks_text": chunks_text or "Релевантная информация не найдена",
            "chunks_found": chunks_found,
            "lang": lang if 'lang' in locals() else 'ru',
            "context_text": final_user_prompt,
            "search_mode": search_mode,  # Дополнительная информация
            "vector_count": vector_count  # Дополнительная информация
        }
        
    except Exception as e:
        log_step(0, "КРИТИЧЕСКАЯ ОШИБКА", f"❌ {e}", success=False)
        raise