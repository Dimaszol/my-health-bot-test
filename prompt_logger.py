# prompt_logger.py - Детальное логирование процесса создания промта

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

def filter_chunks_with_logging(chunks: list, chunk_type: str, exclude_doc_id=None, 
                             exclude_texts=None, limit=5) -> list:
    """Фильтрует чанки с детальным логированием"""
    print(f"\n🔍 Фильтрация {chunk_type}:")
    print(f"   📥 Входящих чанков: {len(chunks)}")
    
    filtered_texts = []
    excluded_by_doc = 0
    excluded_by_text = 0
    
    for chunk in chunks:
        chunk_text = chunk.get("chunk_text", "")
        metadata = chunk.get("metadata", {})
        
        # Фильтр по document_id
        if exclude_doc_id and str(metadata.get("document_id")) == str(exclude_doc_id):
            excluded_by_doc += 1
            continue
        # Фильтр по тексту
        if exclude_texts and chunk_text.strip() in exclude_texts:
            excluded_by_text += 1
            continue
            
        filtered_texts.append(chunk_text)
        if len(filtered_texts) >= limit:
            break
    
    print(f"   🚫 Исключено по документу: {excluded_by_doc}")
    print(f"   🚫 Исключено по тексту: {excluded_by_text}")
    print(f"   ✅ Финальных чанков: {len(filtered_texts)}")
    
    return filtered_texts

async def process_user_question_detailed(user_id: int, user_input: str) -> Dict:
    """
    🔍 ГЛАВНАЯ ФУНКЦИЯ: Обрабатывает вопрос пользователя с подробным логированием
    
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
        # ШАГ 2: РАСШИРЕНИЕ ВОПРОСА ЧЕРЕЗ GPT
        # ==========================================
        log_step(2, "РАСШИРЕНИЕ ВОПРОСА ЧЕРЕЗ GPT")
        
        try:
            from gpt import enrich_query_for_vector_search
            refined_query = await enrich_query_for_vector_search(user_input)
            
            print(f"🔍 Исходный вопрос: '{user_input}'")
            print(f"🧠 Расширенный запрос: '{refined_query}'")
            print(f"📏 Длина: {len(user_input)} → {len(refined_query)} символов")
            
        except Exception as e:
            refined_query = user_input
            print(f"❌ Ошибка GPT расширения: {e}")
            print(f"🔄 Используем исходный вопрос: '{user_input}'")
        
        # ==========================================
        # ШАГ 3: ИЗВЛЕЧЕНИЕ КЛЮЧЕВЫХ СЛОВ
        # ==========================================
        log_step(3, "ИЗВЛЕЧЕНИЕ КЛЮЧЕВЫХ СЛОВ НА АНГЛИЙСКОМ")
        
        try:
            from gpt import extract_keywords
            keywords = await extract_keywords(user_input)
            
            print(f"🔑 Ключевые слова из вопроса: {keywords}")
            print(f"📊 Количество: {len(keywords)}")
            
        except Exception as e:
            keywords = []
            print(f"❌ Ошибка извлечения ключевых слов: {e}")
        
        # ==========================================
        # ШАГ 4: ПОДГОТОВКА К ПОИСКУ
        # ==========================================
        log_step(4, "ПОДГОТОВКА К ПОИСКУ В ВЕКТОРНОЙ БАЗЕ")
        
        # Получаем данные для фильтрации
        try:
            from db_postgresql import get_last_summary
            last_doc_id, last_summary = await get_last_summary(user_id)
            exclude_texts = last_summary.strip().split("\n\n") if last_summary else []
            
            print(f"🚫 Исключаем документ ID: {last_doc_id}")
            print(f"🚫 Исключаем текстов из последнего документа: {len(exclude_texts)}")
            
        except Exception as e:
            last_doc_id, last_summary = None, ""
            exclude_texts = []
            print(f"❌ Ошибка получения данных для исключения: {e}")
        
        # ==========================================
        # ШАГ 5A: СЕМАНТИЧЕСКИЙ ПОИСК
        # ==========================================
        log_step(5, "СЕМАНТИЧЕСКИЙ ПОИСК ПО ВЕКТОРНОЙ БАЗЕ")
        
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
        
        # ==========================================
        # ШАГ 5B: ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ
        # ==========================================
        log_step(6, "ПОИСК ПО КЛЮЧЕВЫМ СЛОВАМ")
        
        try:
            from vector_db_postgresql import keyword_search_chunks
                       
            # ✅ ИСПРАВЛЕНИЕ: передаем ключевые слова, а не исходный вопрос
            keywords_string = ", ".join(keywords) if keywords else user_input
            keyword_chunks = await keyword_search_chunks(user_id, keywords_string, limit=10)
            
            print(f"🔍 Поиск по ключевым словам: '{keywords_string}'")
            
            if keyword_chunks:
                log_chunk_info(keyword_chunks, "КЛЮЧЕВЫЕ ЧАНКИ")
            else:
                print("❌ Чанков по ключевым словам не найдено")
                
        except Exception as e:
            keyword_chunks = []
            print(f"❌ Ошибка поиска по ключевым словам: {e}")
        
        # ==========================================
        # ШАГ 6: ФИЛЬТРАЦИЯ И ОБЪЕДИНЕНИЕ
        # ==========================================
        log_step(7, "ФИЛЬТРАЦИЯ И ОБЪЕДИНЕНИЕ РЕЗУЛЬТАТОВ")
        
        # Фильтруем результаты
        vector_texts = filter_chunks_with_logging(
            vector_chunks, "СЕМАНТИЧЕСКИХ", 
            exclude_doc_id=last_doc_id, exclude_texts=exclude_texts, limit=4
        )
        
        keyword_texts = filter_chunks_with_logging(
            keyword_chunks, "КЛЮЧЕВЫХ", 
            exclude_doc_id=last_doc_id, exclude_texts=exclude_texts, limit=2
        )
        
        # Объединяем и убираем дубликаты
        all_chunks = list(dict.fromkeys(vector_texts + keyword_texts))
        chunks_text = "\n\n".join(all_chunks[:6])
        
        print(f"\n📦 ИТОГОВЫЙ РЕЗУЛЬТАТ ПОИСКА:")
        print(f"   🧠 Семантических чанков: {len(vector_texts)}")
        print(f"   🔑 Ключевых чанков: {len(keyword_texts)}")
        print(f"   📋 Уникальных чанков: {len(all_chunks)}")
        print(f"   📄 Символов контекста: {len(chunks_text)}")
        
        # ==========================================
        # ШАГ 7: СИСТЕМНЫЙ ПРОМТ
        # ==========================================
        log_step(8, "СОЗДАНИЕ СИСТЕМНОГО ПРОМТА")
        
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
            print(f"❌ Ошибка создания системного промта: {e}")
        
        # ==========================================
        # ШАГ 8: ДАННЫЕ ПАЦИЕНТА
        # ==========================================
        log_step(9, "ЗАГРУЗКА ДАННЫХ ПАЦИЕНТА ИЗ АНКЕТЫ")
        
        try:
            from save_utils import format_user_profile
            profile_text = await format_user_profile(user_id)
            
            print(f"👤 Профиль пациента загружен:")
            print(f"   📏 Длина: {len(profile_text)} символов")
            print(f"   📋 Превью: {profile_text[:150]}...")
            
        except Exception as e:
            profile_text = "Профиль пациента недоступен"
            print(f"❌ Ошибка загрузки профиля: {e}")
        
        # ==========================================
        # ШАГ 9: СВОДКА РАЗГОВОРА
        # ==========================================
        log_step(10, "СВОДКА КОНТЕКСТА РАЗГОВОРА")
        
        try:
            from db_postgresql import get_conversation_summary
            summary_text, _ = await get_conversation_summary(user_id)
            
            print(f"💭 Сводка разговора:")
            print(f"   📏 Длина: {len(summary_text)} символов")
            print(f"   📋 Превью: {summary_text[:150]}...")
            
        except Exception as e:
            summary_text = "Сводка разговора недоступна"
            print(f"❌ Ошибка загрузки сводки: {e}")
        
        # ==========================================
        # ШАГ 10: ПОСЛЕДНИЙ ДОКУМЕНТ
        # ==========================================
        log_step(11, "ИНФОРМАЦИЯ ИЗ ПОСЛЕДНЕГО ДОКУМЕНТА")
        
        if last_summary:
            print(f"📄 Последний документ (ID: {last_doc_id}):")
            print(f"   📏 Длина: {len(last_summary)} символов")
            print(f"   📋 Превью: {last_summary[:150]}...")
        else:
            print("❌ Последний документ не найден")
            last_summary = "Нет недавних документов"
        
        # ==========================================
        # ШАГ 11: ФИНАЛЬНАЯ СБОРКА ПРОМТА
        # ==========================================
        log_step(12, "ФИНАЛЬНАЯ СБОРКА ПРОМТА")
        
        # Собираем финальный промт
        user_prompt_parts = [
            "You have access to the user's health profile, medical documents, imaging reports, conversation history, and memory notes.",
            "Answer only questions related to the user's health. Do not repeat that you're an AI. Do not ask follow-up questions unless critical.",
            "",
            f"📌 Patient profile:\n{profile_text}",
            "",
            f"🧠 Conversation summary:\n{summary_text}",
            "",
            f"📄 Recent document interpretations:\n{last_summary}",
            "",
            f"🔎 Related historical data:\n{chunks_text or 'Релевантная информация не найдена'}",
            "",
            f"Patient: {user_input}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
        
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ПРОМТА:")
        print(f"   🔧 Системный промт: {len(system_prompt)} символов")
        print(f"   👤 Профиль: {len(profile_text)} символов")
        print(f"   💭 Сводка: {len(summary_text)} символов")
        print(f"   📄 Последний документ: {len(last_summary)} символов")
        print(f"   🔎 Исторические данные: {len(chunks_text)} символов")
        print(f"   📏 ОБЩАЯ ДЛИНА: {len(final_user_prompt)} символов")
        print(f"   🎯 Примерно токенов: {len(final_user_prompt) // 4}")
        
        # Возвращаем все данные для использования в main.py
        return {
            "profile_text": profile_text,
            "summary_text": summary_text, 
            "last_summary": last_summary or "Нет недавних документов",
            "chunks_text": chunks_text or "Релевантная информация не найдена",
            "chunks_found": len(all_chunks),
            "lang": lang if 'lang' in locals() else 'ru'
        }
        
    except Exception as e:
        log_step(0, "КРИТИЧЕСКАЯ ОШИБКА", f"❌ {e}", success=False)
        raise

# 🔧 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КРАТКОГО ЛОГИРОВАНИЯ
def log_search_summary(vector_count: int, keyword_count: int, final_count: int, 
                      excluded_doc_id: Optional[int] = None):
    """Краткая сводка поиска (для обратной совместимости)"""
    print(f"🧠 Найдено: {vector_count} векторных + {keyword_count} ключевых = {final_count} итого", end="")
    if excluded_doc_id:
        print(f" (исключен док.{excluded_doc_id})")
    else:
        print()