# prompt_logger.py - ИСПРАВЛЕННАЯ ВЕРСИЯ без last_summary

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

def filter_chunks_with_logging(chunks: list, chunk_type: str, limit=5) -> list:
    """✅ УПРОЩЕННАЯ фильтрация чанков без исключений документов"""
    print(f"\n🔍 Фильтрация {chunk_type}:")
    print(f"   📥 Входящих чанков: {len(chunks)}")
    
    filtered_texts = []
    
    for chunk in chunks:
        chunk_text = chunk.get("chunk_text", "")
        
        # Простая проверка на непустой текст
        if chunk_text.strip():
            filtered_texts.append(chunk_text)
            if len(filtered_texts) >= limit:
                break
    
    print(f"   ✅ Финальных чанков: {len(filtered_texts)}")
    
    return filtered_texts

async def process_user_question_detailed(user_id: int, user_input: str) -> Dict:
    """
    🔍 ГЛАВНАЯ ФУНКЦИЯ: Обрабатывает вопрос пользователя с подробным логированием
    ✅ ИСПРАВЛЕННАЯ ВЕРСИЯ без last_summary
    
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
        # ШАГ 2: ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
        # ==========================================
        log_step(2, "ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ")
        
        try:
            from save_utils import format_user_profile
            profile_text = await format_user_profile(user_id)
            print(f"👤 Профиль получен: {len(profile_text)} символов")
        except Exception as e:
            profile_text = "Профиль пациента не заполнен"
            print(f"❌ Ошибка получения профиля: {e}")
        
        # ==========================================
        # ШАГ 3: ПОЛУЧЕНИЕ СВОДКИ РАЗГОВОРА
        # ==========================================
        log_step(3, "ПОЛУЧЕНИЕ СВОДКИ РАЗГОВОРА")
        
        try:
            from db_postgresql import get_conversation_summary
            summary_text, _ = await get_conversation_summary(user_id)
            
            # Безопасная обработка
            if not summary_text:
                summary_text = "Новый пациент, предыдущих бесед нет"
                
            print(f"🧠 Сводка получена: {len(summary_text)} символов")
        except Exception as e:
            summary_text = "Ошибка получения сводки разговора"
            print(f"❌ Ошибка получения сводки: {e}")
        
        # ==========================================
        # ШАГ 4: УЛУЧШЕНИЕ ЗАПРОСА ДЛЯ ПОИСКА
        # ==========================================
        log_step(4, "УЛУЧШЕНИЕ ЗАПРОСА ДЛЯ ВЕКТОРНОГО ПОИСКА")
        
        try:
            from gpt import enrich_query_for_vector_search, extract_keywords
            
            # Улучшаем запрос для векторного поиска
            refined_query = await enrich_query_for_vector_search(user_input)
            print(f"🔍 Исходный: '{user_input}'")
            print(f"🎯 Улучшенный: '{refined_query}'")
            
            # Извлекаем ключевые слова
            keywords = await extract_keywords(user_input)
            print(f"🔑 Ключевые слова: {keywords}")
            
        except Exception as e:
            refined_query = user_input
            keywords = []
            print(f"❌ Ошибка обработки запроса, используем исходный: {e}")
        
        # ❌ УБИРАЕМ ШАГ С ПОЛУЧЕНИЕМ last_summary
        # Больше НЕ получаем и НЕ исключаем последний документ
        
        # ==========================================
        # ШАГ 5A: СЕМАНТИЧЕСКИЙ ПОИСК
        # ==========================================
        log_step(5, "СЕМАНТИЧЕСКИЙ ПОИСК ПО ВЕКТОРНОЙ БАЗЕ")
        
        try:
            from vector_db_postgresql import search_similar_chunks
            # ✅ ИЩЕМ ПО ВСЕМ ДОКУМЕНТАМ без исключений
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
                       
            # Передаем ключевые слова, а не исходный вопрос
            keywords_string = ", ".join(keywords) if keywords else user_input
            # ✅ ИЩЕМ ПО ВСЕМ ДОКУМЕНТАМ без исключений
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
        
        # ✅ ФИЛЬТРУЕМ БЕЗ ИСКЛЮЧЕНИЙ по документам
        vector_texts = filter_chunks_with_logging(
            vector_chunks, "СЕМАНТИЧЕСКИХ", limit=4
        )
        
        keyword_texts = filter_chunks_with_logging(
            keyword_chunks, "КЛЮЧЕВЫХ", limit=2
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
            lang = 'ru'
            print(f"❌ Ошибка создания системного промта: {e}")
        
        # ==========================================
        # ШАГ 8: СОЗДАНИЕ ФИНАЛЬНОГО ПРОМТА
        # ==========================================
        log_step(9, "СОЗДАНИЕ ФИНАЛЬНОГО ПРОМТА")
        
        # ✅ СОЗДАЕМ ПРОМТ БЕЗ last_summary
        user_prompt_parts = [
            "Answer only questions related to the user's health. Do not repeat that you're an AI. Do not ask follow-up questions unless critical.",
            "",
            f"📌 Patient profile:\n{profile_text}",
            "",
            f"🧠 Conversation summary:\n{summary_text}",
            "",
            # ❌ УБРАЛИ: f"📄 Recent document interpretations:\n{last_summary}",
            f"🔎 Related historical data:\n{chunks_text or 'Релевантная информация не найдена'}",
            "",
            f"Patient: {user_input}"
        ]
        
        final_user_prompt = "\n".join(user_prompt_parts)
        
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА ПРОМТА:")
        print(f"   🔧 Системный промт: {len(system_prompt)} символов")
        print(f"   👤 Профиль: {len(profile_text)} символов")
        print(f"   💭 Сводка: {len(summary_text)} символов")
        # ❌ УБРАЛИ: print(f"   📄 Последний документ: {len(last_summary)} символов")
        print(f"   🔎 Исторические данные: {len(chunks_text)} символов")
        print(f"   📏 ОБЩАЯ ДЛИНА: {len(final_user_prompt)} символов")
        print(f"   🎯 Примерно токенов: {len(final_user_prompt) // 4}")
        
        # ✅ ВОЗВРАЩАЕМ ДАННЫЕ БЕЗ last_summary
        return {
            "profile_text": profile_text,
            "summary_text": summary_text, 
            # ❌ УБРАЛИ: "last_summary": last_summary or "Нет недавних документов",
            "chunks_text": chunks_text or "Релевантная информация не найдена",
            "chunks_found": len(all_chunks),
            "lang": lang if 'lang' in locals() else 'ru',
            "context_text": final_user_prompt  # Добавляем для совместимости
        }
        
    except Exception as e:
        log_step(0, "КРИТИЧЕСКАЯ ОШИБКА", f"❌ {e}", success=False)
        raise

# 🔧 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КРАТКОГО ЛОГИРОВАНИЯ (упрощенная)
def log_search_summary(vector_count: int, keyword_count: int, final_count: int):
    """Краткая сводка поиска БЕЗ excluded_doc_id"""
    print(f"🧠 Найдено: {vector_count} векторных + {keyword_count} ключевых = {final_count} итого")