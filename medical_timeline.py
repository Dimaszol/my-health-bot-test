# medical_timeline.py - Работа с медицинской картой пациента

import json
import asyncio
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from db_postgresql import get_db_connection, release_db_connection, t
from gpt import client, OPENAI_SEMAPHORE
from error_handler import log_error_with_context

# ==========================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ==========================================

async def get_latest_medical_timeline(user_id: int, limit: int = 10) -> List[Dict]:
    """Получить последние записи медицинской карты пользователя"""
    conn = await get_db_connection()
    try:
        query = """
        SELECT id, event_date, category, importance, description, source_document_id
        FROM medical_timeline 
        WHERE user_id = $1 
        ORDER BY event_date DESC, created_at DESC 
        LIMIT $2
        """
        
        rows = await conn.fetch(query, user_id, limit)
        
        timeline = []
        for row in rows:
            timeline.append({
                'id': row['id'],
                'event_date': row['event_date'].strftime('%d.%m.%Y') if row['event_date'] else '',
                'category': row['category'],
                'importance': row['importance'],
                'description': row['description'],
                'source_document_id': row['source_document_id']
            })
        
        return timeline
        
    except Exception as e:
        log_error_with_context(e, {"function": "get_latest_medical_timeline", "user_id": user_id})
        return []
    finally:
        await release_db_connection(conn)

async def delete_medical_timeline_entries(user_id: int, entry_ids: List[int]) -> bool:
    """Удалить указанные записи медицинской карты"""
    if not entry_ids:
        return True
        
    conn = await get_db_connection()
    try:
        # Формируем список плейсхолдеров для SQL
        placeholders = ','.join([f'${i+2}' for i in range(len(entry_ids))])
        query = f"DELETE FROM medical_timeline WHERE user_id = $1 AND id IN ({placeholders})"
        
        await conn.execute(query, user_id, *entry_ids)
        print(f"✅ Удалено {len(entry_ids)} записей медкарты для пользователя {user_id}")
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "delete_medical_timeline_entries", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def save_medical_timeline_entries(user_id: int, entries: List[Dict], source_document_id: int) -> bool:
    """Сохранить новые записи медицинской карты"""
    if not entries:
        return True
        
    conn = await get_db_connection()
    try:
        query = """
        INSERT INTO medical_timeline (user_id, source_document_id, event_date, category, importance, description)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        for entry in entries:
            # Парсим дату
            event_date = datetime.now().date()  # fallback
            if 'event_date' in entry and entry['event_date']:
                try:
                    # Пробуем разные форматы дат
                    date_str = entry['event_date']
                    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
                        try:
                            event_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                except:
                    pass  # Используем текущую дату
            
            await conn.execute(
                query,
                user_id,
                source_document_id,
                event_date,
                entry.get('category', 'general'),
                entry.get('importance', 'normal'),
                entry.get('description', '')
            )
        
        print(f"✅ Сохранено {len(entries)} записей медкарты для пользователя {user_id}")
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "save_medical_timeline_entries", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

# ==========================================
# ФУНКЦИИ ИЗВЛЕЧЕНИЯ ЧЕРЕЗ GPT И GEMINI
# ==========================================

async def extract_medical_events_gpt(document_text: str, existing_timeline: List[Dict], lang: str = "ru") -> List[Dict]:
    """Извлечение КРИТИЧЕСКИ ВАЖНЫХ медицинских событий через GPT-4o-mini"""
    
    # Форматируем существующую медкарту
    timeline_text = ""
    if existing_timeline:
        timeline_text = "\n".join([
            f"{entry['event_date']} | {entry['category']} | {entry['importance']} | \"{entry['description']}\""
            for entry in existing_timeline
        ])
    else:
        timeline_text = "Медкарта пустая"
    
    # Определяем язык ответа
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian',
        'en': 'English'
    }
    response_lang = lang_names.get(lang, 'Russian')
    
    system_prompt = f"""You are a medical timeline curator. Extract ONLY the most CRITICAL medical events that would be essential for any future doctor to know.

TASK: From the new document, extract MAXIMUM 1-2 most important medical facts and ADD them to existing timeline.

STRICT CRITERIA - Extract ONLY:
• Life-threatening diagnoses (heart attack, stroke, cancer, etc.)
• Major surgical procedures (operations, stent implantations, etc.)
• Critical medication changes (new chronic medications)
• Severe complications or hospitalizations
• Major diagnostic findings that change treatment approach

CRITICAL IMPORTANCE RANKING:
• "critical" = Life-threatening conditions, major surgery, emergency situations
• "important" = Chronic conditions, significant procedures, key medications
• "normal" = Routine findings (DO NOT EXTRACT unless exceptional)

EXAMPLES OF WHAT TO EXTRACT:
✅ "Инфаркт миокарда, стентирование ПКА" (critical)
✅ "Сахарный диабет 2 типа впервые выявлен" (important) 
✅ "Хроническая сердечная недостаточность" (important)

EXAMPLES OF WHAT NOT TO EXTRACT:
❌ Individual medication names unless it's a major new chronic treatment
❌ Routine test results within normal ranges
❌ Standard procedure details
❌ Blood pressure readings unless extremely abnormal
❌ Heart rate measurements

Rules:
1. Extract dates from document text or use current date
2. Categories: diagnosis, treatment, test, procedure, general
3. Maximum 1-2 events per document - only the most critical
4. Description: 3-8 words, focus on medical essence
5. If nothing is critically important, return "NO_CHANGES"

FORMAT:
[
  {{
    "event_date": "DD.MM.YYYY",
    "category": "diagnosis|treatment|procedure", 
    "importance": "critical|important",
    "description": "Brief critical fact (3-8 words)"
  }}
]

LANGUAGE: Respond in {response_lang} language only."""

    user_prompt = f"""EXISTING MEDICAL TIMELINE:
{timeline_text}

NEW DOCUMENT:
{document_text}

Extract ONLY 1-2 most critical medical facts. If nothing is critically important, return "NO_CHANGES"."""

    try:
        async with OPENAI_SEMAPHORE:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,  # Меньше токенов = короче ответ
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Проверяем на "NO_CHANGES"
            if result.upper() in ['NO_CHANGES', 'БЕЗ ИЗМЕНЕНИЙ', 'БЕЗ_ИЗМЕНЕНИЙ']:
                print("📋 GPT: Нет критически важных событий для медкарты")
                return []
            
            # Пробуем парсить JSON
            try:
                events = json.loads(result)
                if isinstance(events, list):
                    # Ограничиваем до 2 событий максимум
                    events = events[:2]
                    print(f"📋 GPT извлек {len(events)} критических событий")
                    return events
                else:
                    print(f"⚠️ GPT вернул не массив: {result[:100]}")
                    return []
            except json.JSONDecodeError:
                print(f"⚠️ GPT вернул некорректный JSON: {result[:200]}")
                return []
                
    except Exception as e:
        log_error_with_context(e, {"function": "extract_medical_events_gpt"})
        return []

async def _validate_extracted_events(events: List[Dict], lang: str) -> List[Dict]:
    """Валидация извлеченных событий через второй запрос к GPT"""
    
    if not events:
        return []
    
    # Форматируем события для проверки
    events_text = "\n".join([
        f"{i+1}. {event.get('event_date', 'N/A')} | {event.get('category', 'N/A')} | {event.get('description', 'N/A')}"
        for i, event in enumerate(events)
    ])
    
    validation_prompt = f"""You are a medical quality assessor. Review these extracted medical events and filter out any that are NOT concrete medical facts.

KEEP ONLY events that contain:
• Specific measurements, values, or numbers
• Concrete medical diagnoses
• Specific medications with dosages
• Completed procedures with findings
• Objective examination results

REMOVE events that are:
• General recommendations 
• Future appointments
• Referrals or consultations
• Lifestyle advice
• Administrative notes
• Vague statements

EXTRACTED EVENTS TO REVIEW:
{events_text}

Return ONLY the numbers of events that should be KEPT (e.g., "1,3,5" or "2,4" or "NONE").
Respond in {lang} but use only numbers and commas."""

    try:
        async with OPENAI_SEMAPHORE:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical quality assessor. Be strict about what constitutes a concrete medical fact."},
                    {"role": "user", "content": validation_prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            validation_result = response.choices[0].message.content.strip()
            
            # Парсим результат валидации
            if validation_result.upper() in ['NONE', 'НЕТ', 'НЕМАЄ']:
                print("🚫 Валидация: все события отфильтрованы")
                return []
            
            # Извлекаем номера валидных событий
            try:
                valid_indices = []
                for num_str in validation_result.replace(' ', '').split(','):
                    if num_str.isdigit():
                        idx = int(num_str) - 1  # Конвертируем в 0-based индекс
                        if 0 <= idx < len(events):
                            valid_indices.append(idx)
                
                validated_events = [events[i] for i in valid_indices]
                
                # Логируем что было отфильтровано
                for i, event in enumerate(events):
                    if i not in valid_indices:
                        print(f"🚫 Отфильтровано валидацией: {event.get('description', '')}")
                
                return validated_events
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Ошибка парсинга валидации: {validation_result}")
                # В случае ошибки возвращаем исходные события
                return events
            
    except Exception as e:
        print(f"⚠️ Ошибка валидации событий: {e}")
        # В случае ошибки возвращаем исходные события  
        return events

async def extract_medical_events_gemini(document_text: str, existing_timeline: List[Dict], lang: str = "ru") -> List[Dict]:
    """Извлечение медицинских событий через Gemini (будет реализовано в gemini_analyzer.py)"""
    
    # Импортируем функцию из gemini_analyzer
    try:
        from gemini_analyzer import extract_medical_timeline_gemini
        return await extract_medical_timeline_gemini(document_text, existing_timeline, lang)
    except ImportError:
        print("⚠️ Функция extract_medical_timeline_gemini не найдена в gemini_analyzer.py")
        return []
    except Exception as e:
        log_error_with_context(e, {"function": "extract_medical_events_gemini"})
        return []

# ==========================================
# ОСНОВНАЯ ФУНКЦИЯ ОБНОВЛЕНИЯ МЕДКАРТЫ
# ==========================================

async def update_medical_timeline_on_document_upload(user_id: int, document_id: int, document_text: str, use_gemini: bool = False) -> bool:
    """
    ИСПРАВЛЕННАЯ функция обновления медкарты - ДОБАВЛЯЕТ новые события, НЕ удаляет старые
    """
    
    print(f"\n🏥 Обновление медкарты пользователя {user_id} для документа {document_id}")
    
    try:
        # Шаг 1: Получаем последние 15 записей медкарты для контекста
        existing_timeline = await get_latest_medical_timeline(user_id, limit=15)
        print(f"📋 Текущих записей в медкарте: {len(existing_timeline)}")
        
        # Шаг 2: Извлекаем ТОЛЬКО критические события из нового документа
        from db_postgresql import get_user_language
        lang = await get_user_language(user_id)
        
        if use_gemini:
            new_events = await extract_medical_events_gemini(document_text, existing_timeline, lang)
        else:
            new_events = await extract_medical_events_gpt(document_text, existing_timeline, lang)
        
        if not new_events:
            print("📋 Нет критически важных событий для добавления в медкарту")
            return True
        
        # Шаг 3: ДОБАВЛЯЕМ новые события (НЕ удаляем старые!)
        success = await save_medical_timeline_entries(user_id, new_events, document_id)
        
        # Шаг 4: Если медкарта стала слишком большой (>20 записей), удаляем самые старые
        await cleanup_old_timeline_entries(user_id, max_entries=20)
        
        if success:
            print(f"✅ В медкарту добавлено {len(new_events)} критических событий")
        else:
            print("❌ Ошибка сохранения медкарты")
        
        return success
        
    except Exception as e:
        log_error_with_context(e, {"function": "update_medical_timeline_on_document_upload", "user_id": user_id})
        return False

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

async def get_medical_timeline_for_prompt(user_id: int, limit: int = 10) -> str:
    """Получить медкарту в формате для промпта GPT"""
    
    timeline = await get_latest_medical_timeline(user_id, limit)
    
    if not timeline:
        return "Медкарта пустая"
    
    lines = []
    for entry in timeline:
        lines.append(f"📅 {entry['event_date']} | {entry['category']} | {entry['importance']} | {entry['description']}")
    
    return "\n".join(lines)

async def format_medical_timeline_for_user(user_id: int, lang: str, limit: int = 10) -> str:
    """Форматировать медкарту для показа пользователю"""
    
    timeline = await get_latest_medical_timeline(user_id, limit)
    
    if not timeline:
        return t("medical_timeline_empty", lang)
    
    lines = [f"{t('medical_timeline_header', lang)}\n"]
    
    for entry in timeline:
        # Эмодзи по категориям
        emoji = {
            'diagnosis': '🩺',
            'treatment': '💊', 
            'test': '🔬',
            'procedure': '🏥',
            'general': '📄'
        }.get(entry['category'], '📄')
        
        # Важность
        importance_mark = {
            'critical': '🔴',
            'important': '🟡', 
            'normal': '⚪'
        }.get(entry['importance'], '⚪')
        
        lines.append(f"{emoji} {importance_mark} **{entry['event_date']}** - {entry['description']}")
    
    return "\n".join(lines)

async def cleanup_old_timeline_entries(user_id: int, max_entries: int = 20) -> bool:
    """Удаляет старые записи медкарты, оставляя только последние max_entries"""
    
    conn = await get_db_connection()
    try:
        # Подсчитываем общее количество записей
        count_query = "SELECT COUNT(*) FROM medical_timeline WHERE user_id = $1"
        total_count = await conn.fetchval(count_query, user_id)
        
        if total_count <= max_entries:
            return True  # Чистка не нужна
        
        # Удаляем старые записи, оставляя только последние max_entries
        cleanup_query = """
        DELETE FROM medical_timeline 
        WHERE user_id = $1 
        AND id NOT IN (
            SELECT id FROM medical_timeline 
            WHERE user_id = $1 
            ORDER BY event_date DESC, created_at DESC 
            LIMIT $2
        )
        """
        
        result = await conn.execute(cleanup_query, user_id, max_entries)
        deleted_count = total_count - max_entries
        print(f"🧹 Удалено {deleted_count} старых записей медкарты для пользователя {user_id}")
        
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "cleanup_old_timeline_entries", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)