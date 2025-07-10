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
        'en': 'English',
        'de': 'German' 
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
                return []
            
            # Пробуем парсить JSON
            try:
                events = json.loads(result)
                if isinstance(events, list):
                    # Ограничиваем до 2 событий максимум
                    events = events[:2]
                    return events
                else:
                    return []
            except json.JSONDecodeError:
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
                return validated_events
                
            except (ValueError, IndexError) as e:
                return events
            
    except Exception as e:
        return events

async def extract_medical_events_gemini(document_text: str, existing_timeline: List[Dict], lang: str = "ru") -> List[Dict]:
    """Извлечение медицинских событий через Gemini (будет реализовано в gemini_analyzer.py)"""
    
    # Импортируем функцию из gemini_analyzer
    try:
        from gemini_analyzer import extract_medical_timeline_gemini
        return await extract_medical_timeline_gemini(document_text, existing_timeline, lang)
    except ImportError:
        return []
    except Exception as e:
        log_error_with_context(e, {"function": "extract_medical_events_gemini"})
        return []

# ==========================================
# УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ИЗВЛЕЧЕНИЯ МЕДИЦИНСКИХ ДАННЫХ
# ==========================================

async def update_medical_timeline_on_document_upload(user_id: int, document_id: int, document_text: str, use_gemini: bool = False) -> bool:
    """
    Универсальная функция обновления медкарты - добавляет ОДНУ сжатую запись с самыми важными данными
    """
    try:
        # Получаем язык пользователя
        from db_postgresql import get_user_language
        lang = await get_user_language(user_id)
        
        # Извлекаем самую важную информацию
        if use_gemini:
            medical_summary = await extract_medical_summary_universal_gemini(document_text, lang)
        else:
            medical_summary = await extract_medical_summary_universal_gpt(document_text, lang)
        
        if not medical_summary:
            return True
        # Сохраняем одну запись
        success = await save_single_medical_entry(user_id, medical_summary, document_id)
        return success
        
    except Exception as e:
        log_error_with_context(e, {"function": "update_medical_timeline_on_document_upload", "user_id": user_id})
        return False

async def extract_medical_summary_universal_gpt(document_text: str, lang: str = "ru") -> Dict:
    """
    GPT: Универсальное извлечение самой важной медицинской информации (любой тип документа)
    """
    
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian', 
        'en': 'English',
        'de': 'German'
    }
    response_lang = lang_names.get(lang, 'Russian')
    
    system_prompt = f"""You are a medical data extraction specialist. Create a SINGLE comprehensive medical timeline entry from any medical document.

TASK: Extract and combine ALL important medical information into ONE timeline entry (max 20 words).

UNIVERSAL APPROACH: Works with any medical document - reports, lab results, imaging, consultations, prescriptions, etc.

APPROACH: If multiple important findings exist, combine them into one concise entry. Prioritize the most critical, but include other significant findings if space allows.

IMPORTANCE LEVELS:
🔴 CRITICAL: New diagnoses, surgeries, emergency conditions, life-threatening findings
🟡 IMPORTANT: Chronic conditions, abnormal results, new treatments, significant recommendations
⚪ NORMAL: Routine findings, minor issues, general advice

IMPORTANT RULES:
- ALWAYS include specific numerical values when available (glucose 5.76, cholesterol 6.95, etc.)
- Record ONLY what was found/done/reported, do NOT add your own recommendations
- Extract ONLY factual findings from the document

RESPONSE FORMAT (JSON only):
{{
    "event_date": "DD.MM.YYYY",
    "category": "diagnosis|treatment|test|procedure|general",
    "importance": "critical|important|normal",
    "description": "Combined summary with specific values in {response_lang} (max 20 words)"
}}

If no important medical info found, return: {{"no_data": true}}

EXAMPLES:
- Critical finding: "New serious medical condition identified" → critical/diagnosis
- Multiple results: "Several test values outside normal range" → important/test
- Procedure with outcome: "Medical procedure completed successfully" → important/procedure

Adapt format and language to match the document content and user's language."""

    user_prompt = f"""MEDICAL DOCUMENT:
{document_text}

Create ONE comprehensive timeline entry combining all important medical findings. Max 20 words. Return JSON:"""

    try:
        async with OPENAI_SEMAPHORE:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                data = json.loads(result)
                
                if data.get("no_data"):
                    return None
                
                required_fields = ['event_date', 'category', 'importance', 'description']
                if all(field in data for field in required_fields):
                    return data
                else:
                    return None
                    
            except json.JSONDecodeError:
                return None
                
    except Exception as e:
        log_error_with_context(e, {"function": "extract_medical_summary_universal_gpt"})
        return None

async def extract_medical_summary_universal_gemini(document_text: str, lang: str = "ru") -> Dict:
    """
    Gemini: Универсальное извлечение самой важной медицинской информации (любой тип документа)
    """
    
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        lang_names = {
            'ru': 'Russian',
            'uk': 'Ukrainian',
            'en': 'English',
            'de': 'German'
        }
        response_lang = lang_names.get(lang, 'Russian')
        
        prompt = f"""You are a medical data extraction specialist. Create a SINGLE comprehensive medical timeline entry from any medical document.

TASK: Extract and combine ALL important medical information into ONE timeline entry (max 20 words).

UNIVERSAL APPROACH: Works with any medical document - reports, lab results, imaging, consultations, prescriptions, etc.

APPROACH: If multiple important findings exist, combine them into one concise entry. Prioritize the most critical, but include other significant findings if space allows.

IMPORTANCE LEVELS:
🔴 CRITICAL: New diagnoses, surgeries, emergency conditions, life-threatening findings
🟡 IMPORTANT: Chronic conditions, abnormal results, new treatments, significant recommendations
⚪ NORMAL: Routine findings, minor issues, general advice

IMPORTANT RULES:
- ALWAYS include specific numerical values when available (glucose 5.76, cholesterol 6.95, etc.)
- Record ONLY what was found/done/reported, do NOT add your own recommendations
- Extract ONLY factual findings from the document

RESPONSE FORMAT (JSON only):
{{
    "event_date": "DD.MM.YYYY",
    "category": "diagnosis|treatment|test|procedure|general",
    "importance": "critical|important|normal",
    "description": "Combined summary with specific values in {response_lang} (max 20 words)"
}}

If no important medical info found, return: {{"no_data": true}}

EXAMPLES:
- Critical finding: "New serious medical condition identified" → critical/diagnosis
- Multiple results: "Several test values outside normal range" → important/test
- Procedure with outcome: "Medical procedure completed successfully" → important/procedure

Adapt format and language to match the document content and user's language.

MEDICAL DOCUMENT:
{document_text}

Create ONE comprehensive entry combining all important findings with specific values. Max 20 words. Return ONLY JSON:"""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=300,
                candidate_count=1
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_MEDICAL",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        if not response.candidates:
            return None
        
        result_text = ""
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and candidate.content.parts:
                try:
                    result_text = candidate.content.parts[0].text.strip()
                    break
                except:
                    continue
        
        if not result_text:
            return None
        
        try:
            # Ищем JSON в ответе
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
                data = json.loads(json_text)
                
                if data.get("no_data"):
                    return None
                
                required_fields = ['event_date', 'category', 'importance', 'description']
                if all(field in data for field in required_fields):
                    return data
                else:
                    return None
            else:
                return None
                
        except json.JSONDecodeError as e:
            return None
        
    except Exception as e:
        log_error_with_context(e, {"function": "extract_medical_summary_universal_gemini"})
        return None

async def save_single_medical_entry(user_id: int, entry_data: Dict, source_document_id: int) -> bool:
    """
    Сохраняет одну запись в медицинскую карту
    """
    if not entry_data:
        return True
        
    conn = await get_db_connection()
    try:
        query = """
        INSERT INTO medical_timeline (user_id, source_document_id, event_date, category, importance, description)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        # Парсим дату
        event_date = datetime.now().date()
        if 'event_date' in entry_data and entry_data['event_date']:
            try:
                date_str = entry_data['event_date']
                for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                    try:
                        event_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except:
                pass
        
        await conn.execute(
            query,
            user_id,
            source_document_id,
            event_date,
            entry_data.get('category', 'general'),
            entry_data.get('importance', 'normal'),
            entry_data.get('description', '')
        )

        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "save_single_medical_entry", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)

async def get_medical_timeline_for_prompt(user_id: int, limit: int = 10) -> str:
    """Получить медкарту в компактном формате для промпта GPT"""
    
    timeline = await get_latest_medical_timeline(user_id, limit)
    
    if not timeline:
        return "medical timeline empty"
    
    lines = []
    for entry in timeline:
        # ✅ КОМПАКТНЫЙ ФОРМАТ: только дата и описание
        lines.append(f"{entry['event_date']}: {entry['description']}")
    
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
        
        return True
        
    except Exception as e:
        log_error_with_context(e, {"function": "cleanup_old_timeline_entries", "user_id": user_id})
        return False
    finally:
        await release_db_connection(conn)