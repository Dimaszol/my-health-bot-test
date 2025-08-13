# debug_utils.py - Отладка конкретного пользователя (с правильными импортами)

import logging
import traceback

logger = logging.getLogger(__name__)

async def full_process_debug_7374723347(user_id: int, message_text: str):
    """
    🔍 ПОЛНАЯ ДИАГНОСТИКА ВСЕГО ПРОЦЕССА ВЫБОРКИ ДАННЫХ
    Показывает каждый шаг как в process_user_question_detailed
    """
    
    if user_id != 7374723347:
        return  # Отладка только для этого пользователя
    
    logger.info(f"🚀 [FULL-DEBUG] ========== НАЧИНАЕМ ПОЛНУЮ ДИАГНОСТИКУ ==========")
    logger.info(f"📝 [FULL-DEBUG] Пользователь: {user_id}")
    logger.info(f"📝 [FULL-DEBUG] Сообщение: {message_text}")
    
    try:
        # ========================================
        # ШАГ 1: ПРОВЕРКА ВЕКТОРНОЙ БАЗЫ
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 1: Проверяем векторную базу...")
        
        try:
            from prompt_logger import get_user_vector_count
            vector_count = await get_user_vector_count(user_id)
            logger.info(f"📊 [FULL-DEBUG] Векторов в базе: {vector_count}")
            
            if vector_count == 0:
                logger.info(f"⚠️ [FULL-DEBUG] Пустая векторная база - поиск будет пропущен")
            elif vector_count <= 4:
                logger.info(f"✅ [FULL-DEBUG] Мало векторов ({vector_count}) - возьмем все")
            else:
                logger.info(f"🔍 [FULL-DEBUG] Много векторов ({vector_count}) - будем делать поиск")
            
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка подсчета векторов: {e}")
            vector_count = 0
        
        # ========================================
        # ШАГ 2: ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 2: Получаем профиль пользователя...")
        
        try:
            from save_utils import format_user_profile
            profile_text = await format_user_profile(user_id)
            logger.info(f"📋 [FULL-DEBUG] Профиль получен: {len(profile_text)} символов")
            logger.debug(f"📋 [FULL-DEBUG] Профиль: {profile_text[:200]}...")
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка получения профиля: {e}")
            profile_text = "Профиль пациента не заполнен"
        
        # ========================================
        # ШАГ 3: ПОЛУЧЕНИЕ СВОДКИ РАЗГОВОРА
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 3: Получаем сводку разговора...")
        
        try:
            from db_postgresql import get_conversation_summary
            summary_text, last_msg_id = await get_conversation_summary(user_id)
            
            if not summary_text:
                summary_text = "Новый пациент, предыдущих бесед нет"
                logger.info(f"📝 [FULL-DEBUG] Сводка пустая - используем заглушку")
            else:
                logger.info(f"📝 [FULL-DEBUG] Сводка получена: {len(summary_text)} символов, последнее сообщение: {last_msg_id}")
                logger.debug(f"📝 [FULL-DEBUG] Сводка: {summary_text[:200]}...")
                
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка получения сводки: {e}")
            summary_text = "Ошибка получения сводки разговора"
        
        # ========================================
        # ШАГ 4: ОБРАБОТКА ВЕКТОРОВ (ГЛАВНАЯ ЛОГИКА!)
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 4: Обрабатываем векторы...")
        logger.info(f"🎯 [FULL-DEBUG] Логика выборки для {vector_count} векторов:")
        
        if vector_count == 0:
            # Пустая база: пропускаем поиск
            logger.info(f"🚫 [FULL-DEBUG] Пустая база - пропускаем поиск")
            chunks_text = "У пользователя нет загруженных медицинских документов"
            chunks_found = 0
            
        elif vector_count <= 4:
            # Мало векторов: берем все
            logger.info(f"📥 [FULL-DEBUG] Мало векторов - берем все через get_all_user_chunks")
            
            try:
                from prompt_logger import get_all_user_chunks
                all_chunks = await get_all_user_chunks(user_id, limit=4)
                
                logger.info(f"📊 [FULL-DEBUG] Получено чанков: {len(all_chunks) if all_chunks else 0}")
                
                if all_chunks:
                    chunk_texts = [chunk.get("chunk_text", "") for chunk in all_chunks if chunk.get("chunk_text", "").strip()]
                    chunks_text = "\n\n".join(chunk_texts)
                    chunks_found = len(chunk_texts)
                    
                    logger.info(f"✅ [FULL-DEBUG] Обработано чанков: {chunks_found}")
                    logger.info(f"📊 [FULL-DEBUG] Общая длина chunks_text: {len(chunks_text)} символов")
                    
                    # Показываем образцы чанков
                    for i, chunk in enumerate(all_chunks[:2]):
                        doc_title = chunk.get("document_title", "Unknown")
                        chunk_preview = chunk.get("chunk_text", "")[:100]
                        logger.debug(f"📄 [FULL-DEBUG] Чанк {i+1} из '{doc_title}': {chunk_preview}...")
                        
                else:
                    chunks_text = "Не удалось загрузить данные"
                    chunks_found = 0
                    logger.warning(f"⚠️ [FULL-DEBUG] get_all_user_chunks вернул пустой результат")
                    
            except Exception as e:
                logger.error(f"❌ [FULL-DEBUG] Ошибка get_all_user_chunks: {e}")
                chunks_text = "Ошибка загрузки данных"
                chunks_found = 0
                
        else:
            # Много векторов: полный поиск
            logger.info(f"🔍 [FULL-DEBUG] Много векторов - делаем полный поиск")
            
            # Шаг 4.1: Улучшение запроса
            logger.info(f"🔍 [FULL-DEBUG] Шаг 4.1: Улучшаем запрос через GPT...")
            
            try:
                from gpt import enrich_query_for_vector_search, extract_keywords
                
                refined_query = await enrich_query_for_vector_search(message_text)
                logger.info(f"✅ [FULL-DEBUG] Улучшенный запрос: '{refined_query}'")
                
                keywords = await extract_keywords(message_text)
                logger.info(f"✅ [FULL-DEBUG] Ключевые слова: {keywords}")
                
            except Exception as e:
                logger.error(f"❌ [FULL-DEBUG] Ошибка улучшения запроса: {e}")
                refined_query = message_text
                keywords = []
            
            # Шаг 4.2: Семантический поиск
            logger.info(f"🔍 [FULL-DEBUG] Шаг 4.2: Семантический поиск...")
            
            try:
                from vector_db_postgresql import search_similar_chunks
                vector_chunks = await search_similar_chunks(user_id, refined_query, limit=10)
                
                logger.info(f"📊 [FULL-DEBUG] Семантический поиск: найдено {len(vector_chunks) if vector_chunks else 0} чанков")
                
                if vector_chunks:
                    for i, chunk in enumerate(vector_chunks[:3]):
                        similarity = chunk.get("similarity", "unknown")
                        chunk_preview = chunk.get("chunk_text", "")[:100]
                        logger.debug(f"🔍 [FULL-DEBUG] Векторный чанк {i+1} (similarity: {similarity}): {chunk_preview}...")
                        
            except Exception as e:
                logger.error(f"❌ [FULL-DEBUG] Ошибка семантического поиска: {e}")
                vector_chunks = []
            
            # Шаг 4.3: Поиск по ключевым словам
            logger.info(f"🔍 [FULL-DEBUG] Шаг 4.3: Поиск по ключевым словам...")
            
            try:
                from vector_db_postgresql import keyword_search_chunks
                keyword_list_str = ", ".join(keywords) if keywords else message_text
                keyword_chunks = await keyword_search_chunks(user_id, keyword_list_str, limit=5)
                
                logger.info(f"📊 [FULL-DEBUG] Поиск по ключевым словам: найдено {len(keyword_chunks) if keyword_chunks else 0} чанков")
                
                if keyword_chunks:
                    for i, chunk in enumerate(keyword_chunks[:3]):
                        chunk_preview = chunk.get("chunk_text", "")[:100]
                        logger.debug(f"🔑 [FULL-DEBUG] Ключевой чанк {i+1}: {chunk_preview}...")
                        
            except Exception as e:
                logger.error(f"❌ [FULL-DEBUG] Ошибка поиска по ключевым словам: {e}")
                keyword_chunks = []
            
            # Шаг 4.4: Гибридное ранжирование
            logger.info(f"🔍 [FULL-DEBUG] Шаг 4.4: Гибридное ранжирование...")
            
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
                
                logger.info(f"✅ [FULL-DEBUG] Гибридное ранжирование: выбрано {chunks_found} чанков")
                logger.info(f"📊 [FULL-DEBUG] Общая длина после ранжирования: {len(chunks_text)} символов")
                
            except Exception as e:
                logger.error(f"❌ [FULL-DEBUG] Ошибка гибридного ранжирования: {e}")
                logger.info(f"🔄 [FULL-DEBUG] Fallback на простое объединение...")
                
                # Fallback на простое объединение
                vector_texts = [chunk.get("chunk_text", "") for chunk in vector_chunks[:3] if chunk.get("chunk_text", "").strip()]
                keyword_texts = [chunk.get("chunk_text", "") for chunk in keyword_chunks[:2] if chunk.get("chunk_text", "").strip()]
                all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
                chunks_text = "\n\n".join(all_chunks[:5])
                chunks_found = len(all_chunks)
                
                logger.info(f"✅ [FULL-DEBUG] Fallback объединение: {chunks_found} чанков, {len(chunks_text)} символов")
        
        # ========================================
        # ШАГ 5: ПОЛУЧЕНИЕ ЯЗЫКА И СОЗДАНИЕ СИСТЕМНОГО ПРОМТА
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 5: Получаем язык и создаем системный промпт...")
        
        try:
            from db_postgresql import get_user_language
            lang = await get_user_language(user_id)
            
            system_prompt = (
                "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
                "You speak in a friendly, human tone and provide explanations when needed. "
                f"Always respond in the '{lang}' language."
            )
            
            logger.info(f"🌍 [FULL-DEBUG] Язык: {lang}")
            logger.info(f"📋 [FULL-DEBUG] Системный промпт создан: {len(system_prompt)} символов")
            
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка получения языка: {e}")
            system_prompt = "You are a helpful medical assistant."
            lang = 'ru'
        
        # ========================================
        # ШАГ 6: ПОЛУЧЕНИЕ МЕДИЦИНСКОЙ ХРОНОЛОГИИ
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 6: Получаем медицинскую хронологию...")
        
        try:
            from prompt_logger import get_medical_timeline_simple
            medical_timeline = await get_medical_timeline_simple(user_id, limit=6)
            logger.info(f"📅 [FULL-DEBUG] Медицинская хронология: {len(medical_timeline)} символов")
            logger.debug(f"📅 [FULL-DEBUG] Timeline: {medical_timeline[:200]}...")
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка получения хронологии: {e}")
            medical_timeline = "Medical timeline: unavailable"
        
        # ========================================
        # ШАГ 7: ПОЛУЧЕНИЕ ПОСЛЕДНИХ СООБЩЕНИЙ
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 7: Получаем последние сообщения...")
        
        try:
            from prompt_logger import get_recent_messages_formatted
            recent_messages_text = await get_recent_messages_formatted(user_id, limit=6)
            logger.info(f"💬 [FULL-DEBUG] Последние сообщения: {len(recent_messages_text)} символов")
            logger.debug(f"💬 [FULL-DEBUG] Messages: {recent_messages_text[:200]}...")
        except Exception as e:
            logger.error(f"❌ [FULL-DEBUG] Ошибка получения сообщений: {e}")
            recent_messages_text = "Recent messages unavailable"
        
        # ========================================
        # ШАГ 8: СОЗДАНИЕ ФИНАЛЬНОГО ПРОМТА
        # ========================================
        logger.info(f"🔍 [FULL-DEBUG] ШАГ 8: Создаем финальный промпт...")
        
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
            f"Patient: {message_text}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
        
        # ========================================
        # ФИНАЛЬНАЯ ДИАГНОСТИКА
        # ========================================
        logger.info(f"📊 [FULL-DEBUG] ========== ФИНАЛЬНАЯ ДИАГНОСТИКА ==========")
        logger.info(f"📊 [FULL-DEBUG] Размеры компонентов:")
        logger.info(f"  📋 Profile: {len(profile_text)} символов")
        logger.info(f"  🧠 Summary: {len(summary_text)} символов")
        logger.info(f"  📅 Timeline: {len(medical_timeline)} символов")
        logger.info(f"  🔍 Chunks: {len(chunks_text)} символов ({chunks_found} чанков)")
        logger.info(f"  💬 Messages: {len(recent_messages_text)} символов")
        logger.info(f"📊 [FULL-DEBUG] Финальный промпт: {len(final_user_prompt)} символов")
        logger.info(f"📊 [FULL-DEBUG] Векторов в базе: {vector_count}")
        
        # ПРОВЕРЯЕМ НА КРИТИЧЕСКИЕ РАЗМЕРЫ
        if len(final_user_prompt) > 100000:
            logger.error(f"🚨 [FULL-DEBUG] КРИТИЧЕСКИ ДЛИННЫЙ ПРОМПТ: {len(final_user_prompt)} символов!")
            logger.error(f"🚨 [FULL-DEBUG] Это может вызывать тайм-ауты GPT!")
        elif len(final_user_prompt) > 50000:
            logger.warning(f"⚠️ [FULL-DEBUG] ДЛИННЫЙ ПРОМПТ: {len(final_user_prompt)} символов")
        
        # Показываем образец финального промпта
        logger.info(f"📝 [FULL-DEBUG] Первые 300 символов финального промпта:")
        logger.info(f"     {final_user_prompt[:300]}...")
        
        logger.info(f"🏁 [FULL-DEBUG] ========== ДИАГНОСТИКА ЗАВЕРШЕНА ==========")
        
        # Возвращаем данные как в оригинальной функции
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
        logger.error(f"💥 [FULL-DEBUG] Критическая ошибка полной диагностики: {e}")
        logger.error(f"📋 [FULL-DEBUG] Traceback:\n{traceback.format_exc()}")
        return None

async def debug_user_7374723347(user_id: int, message_text: str):
    """Специальная отладка для проблемного пользователя"""
    
    if user_id != 7374723347:
        return  # Отладка только для этого пользователя
    
    await full_process_debug_7374723347(user_id, message_text)

    logger.info(f"🔍 [DEBUG-USER] Начинаем отладку пользователя {user_id}")
    logger.info(f"📝 [DEBUG-USER] Сообщение: {message_text[:100]}")
    
    try:
        # 1. Проверяем базовые данные пользователя
        try:
            from db_postgresql import get_user_name, get_user_language
            
            name = await get_user_name(user_id)
            lang = await get_user_language(user_id)
            
            logger.info(f"👤 [DEBUG-USER] Имя: {name}")
            logger.info(f"🌍 [DEBUG-USER] Язык: {lang}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка базовых данных: {e}")
        
        # 2. Проверяем документы пользователя (ИСПРАВЛЕНО!)
        try:
            from db_postgresql import get_documents_by_user  # ← ИСПРАВЛЕННЫЙ ИМПОРТ!
            
            docs = await get_documents_by_user(user_id)  # ← ИСПРАВЛЕННЫЙ ВЫЗОВ!
            logger.info(f"📄 [DEBUG-USER] Документов: {len(docs) if docs else 0}")
            
            if docs:
                for i, doc in enumerate(docs[:3]):  # Показываем первые 3
                    title = doc.get('title', 'Без названия')[:50] if doc else 'Неопределено'
                    logger.info(f"📄 [DEBUG-USER] Документ {i+1}: {title}")
                    
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения документов: {e}")
        
        # 3. Проверяем сообщения (ПРАВИЛЬНЫЙ ИМПОРТ!)
        try:
            from db_postgresql import get_last_messages
            
            recent_msgs = await get_last_messages(user_id, limit=5)
            logger.info(f"💬 [DEBUG-USER] Последних сообщений: {len(recent_msgs)}")
            
            if recent_msgs:
                for i, msg in enumerate(recent_msgs[:3]):
                    # msg это tuple (role, message)
                    if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                        role = msg[0]
                        content = str(msg[1])[:50] if msg[1] else 'Пусто'
                        logger.info(f"💬 [DEBUG-USER] Сообщение {i+1} ({role}): {content}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения сообщений: {e}")
        
        # 4. Проверяем профиль (ПРАВИЛЬНЫЙ ИМПОРТ!)
        try:
            from save_utils import format_user_profile
            
            profile = await format_user_profile(user_id)
            logger.info(f"📋 [DEBUG-USER] Профиль: {len(profile)} символов")
            logger.debug(f"📋 [DEBUG-USER] Профиль: {profile[:200]}")
                        
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения профиля: {e}")
        
        # 5. Проверяем сводку разговора (ПРАВИЛЬНЫЙ ИМПОРТ!)
        try:
            from db_postgresql import get_conversation_summary
            
            summary_text, last_msg_id = await get_conversation_summary(user_id)
            logger.info(f"🧠 [DEBUG-USER] Сводка: {len(summary_text)} символов, последнее сообщение: {last_msg_id}")
            
            if summary_text:
                logger.debug(f"🧠 [DEBUG-USER] Сводка: {summary_text[:200]}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения сводки: {e}")
        
        # 6. Проверяем лимиты и подписку
        try:
            from subscription_manager import SubscriptionManager
            
            limits = await SubscriptionManager.get_user_limits(user_id)
            logger.info(f"🎫 [DEBUG-USER] Лимиты: {limits}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения лимитов: {e}")
        
        # 7. Проверяем векторную базу
        try:
            from vector_db_postgresql import search_similar_chunks
            
            # Простой поиск для проверки
            chunks = await search_similar_chunks(user_id, "тест", limit=1)
            logger.info(f"🔍 [DEBUG-USER] Векторных чанков найдено: {len(chunks) if chunks else 0}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка векторной базы: {e}")
        
        # 8. Проверяем состояние пользователя
        try:
            from registration import user_states
            
            current_state = user_states.get(user_id)
            logger.info(f"🔄 [DEBUG-USER] Текущее состояние: {current_state}")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка получения состояния: {e}")
        
        # 9. Проверяем функцию process_user_question_detailed
        try:
            from prompt_logger import process_user_question_detailed
            
            logger.info(f"🔍 [DEBUG-USER] Пробуем запустить process_user_question_detailed...")
            
            # Тестовый запрос
            test_result = await process_user_question_detailed(user_id, "как дела?")
            
            if test_result:
                logger.info(f"✅ [DEBUG-USER] process_user_question_detailed работает нормально")
                logger.info(f"📊 [DEBUG-USER] Результат: chunks_found={test_result.get('chunks_found', 0)}")
            else:
                logger.warning(f"⚠️ [DEBUG-USER] process_user_question_detailed вернул пустой результат")
            
        except Exception as e:
            logger.error(f"❌ [DEBUG-USER] Ошибка в process_user_question_detailed: {e}")
            logger.error(f"📋 [DEBUG-USER] Traceback process_user_question_detailed:\n{traceback.format_exc()}")
        
        logger.info(f"🔍 [DEBUG-USER] Отладка завершена для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"💥 [DEBUG-USER] Критическая ошибка отладки: {e}")
        logger.error(f"📋 [DEBUG-USER] Traceback:\n{traceback.format_exc()}")

# 🧹 ДОПОЛНИТЕЛЬНАЯ ФУНКЦИЯ - ОЧИСТКА ДАННЫХ ПОЛЬЗОВАТЕЛЯ

async def reset_user_cache_7374723347():
    """Безопасная очистка кэша проблемного пользователя"""
    
    user_id = 7374723347
    
    logger.info(f"🔄 [RESET-USER] Начинаем очистку кэша пользователя {user_id}")
    
    try:
        # 1. Очищаем состояние пользователя
        try:
            from registration import user_states
            if user_id in user_states:
                del user_states[user_id]
                logger.info(f"✅ [RESET-USER] Состояние пользователя очищено")
        except Exception as e:
            logger.error(f"❌ [RESET-USER] Ошибка очистки состояния: {e}")
        
        # 2. Можно очистить summary (если есть функция)
        try:
            from db_postgresql import get_conversation_summary
            
            # Проверяем что есть summary
            summary, _ = await get_conversation_summary(user_id)
            if summary:
                logger.info(f"📝 [RESET-USER] Найдена сводка длиной {len(summary)} символов")
                # Здесь можно добавить очистку если нужно
                
        except Exception as e:
            logger.error(f"❌ [RESET-USER] Ошибка работы со сводкой: {e}")
        
        logger.info(f"🔄 [RESET-USER] Очистка завершена для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ [RESET-USER] Ошибка очистки: {e}")

# 📋 ПРОСТАЯ ФУНКЦИЯ ДЛЯ БЫСТРОГО ВЫЗОВА

async def quick_debug_user(user_id: int):
    """Быстрая отладка любого пользователя"""
    
    logger.info(f"⚡ [QUICK-DEBUG] Быстрая проверка пользователя {user_id}")
    
    try:
        from db_postgresql import get_user_name, get_db_pool
        
        name = await get_user_name(user_id)
        logger.info(f"👤 [QUICK-DEBUG] Пользователь: {name}")
        
        # Проверяем количество сообщений и документов
        pool = get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                msg_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM chat_history WHERE user_id = $1",
                    user_id
                )
                doc_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM documents WHERE user_id = $1",
                    user_id
                )
                
                logger.info(f"📊 [QUICK-DEBUG] Сообщений: {msg_count}, Документов: {doc_count}")
        
    except Exception as e:
        logger.error(f"❌ [QUICK-DEBUG] Ошибка: {e}")