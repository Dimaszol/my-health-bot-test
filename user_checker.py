# debug_utils.py - Отладка конкретного пользователя (с правильными импортами)

import logging
import traceback

logger = logging.getLogger(__name__)

async def debug_user_5246978155(user_id: int, message_text: str):
    """Специальная отладка для проблемного пользователя"""
    
    if user_id != 5246978155:
        return  # Отладка только для этого пользователя
    
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
        
        # 2. Проверяем документы пользователя
        try:
            from db_postgresql import get_user_documents
            
            docs = await get_user_documents(user_id)
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

async def reset_user_cache_5246978155():
    """Безопасная очистка кэша проблемного пользователя"""
    
    user_id = 5246978155
    
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