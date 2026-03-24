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
        SELECT mt.id, mt.event_date, mt.category, mt.importance, mt.description, mt.source_document_id
        FROM medical_timeline mt
        INNER JOIN documents d ON mt.source_document_id = d.id
        WHERE mt.user_id = $1 AND d.confirmed = true
        ORDER BY mt.event_date DESC, mt.created_at DESC 
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

async def get_timeline_by_document(document_id: int, user_id: int) -> List[Dict]:
    """
    Получить записи medical_timeline для конкретного документа
    
    Используется на странице документов для отображения извлеченных данных
    
    Параметры:
    - document_id: ID документа
    - user_id: ID пользователя (для безопасности)
    
    Возвращает:
    - Список словарей с записями timeline
    """
    conn = await get_db_connection()
    
    try:
        # 🔐 БЕЗОПАСНОСТЬ: Проверяем что документ принадлежит пользователю
        # через JOIN с таблицей documents
        query = """
        SELECT 
            mt.id,
            mt.event_date,
            mt.category,
            mt.importance,
            mt.description
        FROM medical_timeline mt
        INNER JOIN documents d ON mt.source_document_id = d.id
        WHERE mt.source_document_id = $1 
            AND d.user_id = $2
        ORDER BY mt.event_date DESC, mt.created_at DESC
        """
        
        rows = await conn.fetch(query, document_id, user_id)
        
        # Преобразуем в список словарей
        timeline_entries = []
        for row in rows:
            timeline_entries.append({
                'id': row['id'],
                'event_date': row['event_date'].strftime('%d.%m.%Y') if row['event_date'] else '',
                'category': row['category'],
                'importance': row['importance'],
                'description': row['description']
            })
        
        return timeline_entries
        
    except Exception as e:
        log_error_with_context(e, {
            "function": "get_timeline_by_document",
            "document_id": document_id
        })
        return []
        
    finally:
        await release_db_connection(conn)

async def get_document_importance(document_id: int, user_id: int) -> str:
    """
    Получить importance первой записи medical_timeline для документа
    
    Возвращает: "normal" | "important" | "critical" | "normal" (по умолчанию)
    """
    conn = await get_db_connection()
    
    try:
        row = await conn.fetchrow("""
            SELECT mt.importance
            FROM medical_timeline mt
            INNER JOIN documents d ON mt.source_document_id = d.id
            WHERE mt.source_document_id = $1 
                AND d.user_id = $2
            ORDER BY mt.created_at ASC
            LIMIT 1
        """, document_id, user_id)
        
        return row['importance'] if row else 'normal'
        
    except Exception as e:
        log_error_with_context(e, {
            "function": "get_document_importance",
            "document_id": document_id
        })
        return 'normal'
        
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

async def update_medical_timeline_on_document_upload(user_id: int, document_id: int, document_text: str, document_date: date = None, use_gemini: bool = False, document_type: str = None) -> bool:
    """
    Универсальная функция обновления медкарты - добавляет ОДНУ сжатую запись с самыми важными данными
    """
    try:
        # Получаем язык пользователя
        from db_postgresql import get_user_language
        lang = await get_user_language(user_id)
        
        # Извлекаем самую важную информацию
        if use_gemini:
            medical_summary = await extract_medical_summary_universal_gemini(document_text, lang, document_type)
        else:
            medical_summary = await extract_medical_summary_universal_gpt(document_text, lang, document_type)
        
        if not medical_summary:
            return True
        # Сохраняем одну запись с датой из классификатора
        success = await save_single_medical_entry(user_id, medical_summary, document_id, document_date)
        return success
        
    except Exception as e:
        log_error_with_context(e, {"function": "update_medical_timeline_on_document_upload", "user_id": user_id})
        return False

def _get_objective_data_rules(document_type: str) -> str:
    rules = {
        'lab_results': (
            "- Extract only laboratory measurements with values and units\n"
            "- Format: parameter_name value unit (e.g. blood_glucose 20.6 mmol/L; hba1c 10.4 %)\n"
            "- NO interpretation, NO reference ranges, NO conclusions"
        ),
        'ecg': (
            "- Extract numeric ECG parameters only\n"
            "- Format: parameter value unit (e.g. heart_rate 72 bpm; qrs_duration 90 ms)\n"
            "- NO rhythm descriptions unless accompanied by numeric values"
        ),
        'imaging': (
            "- Extract only measurable sizes or quantitative findings\n"
            "- Format: structure_name size unit (e.g. liver_size 165 mm; lesion_size 12 mm)\n"
            "- NO descriptive findings without measurements"
        ),
        'clinical_report': (
            "- Extract measurable clinical parameters or vital signs if present\n"
            "- Format: parameter value unit (e.g. blood_pressure 120/80 mmHg; temperature 37.2 C)\n"
            "- If no vital signs present, return null"
        ),
        'prescription': (
            "- objective_data must always be null for prescriptions"
        ),
        'pathology': (
            "- Extract tumor size or numeric pathology scores only if present\n"
            "- Format: finding size unit (e.g. tumor_size 15 mm; mitotic_index 3/hpf)\n"
            "- If no numeric findings, return null"
        ),
    }
    return rules.get(document_type, (
        "- Extract measurable values with units when present\n"
        "- Format: parameter value unit\n"
        "- NO interpretations or conclusions"
    ))

async def extract_medical_summary_universal_gpt(document_text: str, lang: str = "ru", document_type: str = None) -> Dict:
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
    doc_type = document_type or 'unknown'
    
    system_prompt = f"""You are a medical data extraction specialist.
DOCUMENT TYPE: {doc_type}
Create a SINGLE comprehensive medical timeline entry from any medical document.

TASK: Extract and combine ALL important medical information into ONE timeline entry.

UNIVERSAL APPROACH: Works with any medical document - reports, lab results, imaging, consultations, prescriptions, etc.

APPROACH:
If multiple important findings exist, combine them into one concise entry for the user.
Prioritize the most critical, but include other significant findings if space allows.

You must return TWO separate fields:
- description → user-friendly medical timeline entry
- objective_data → strict factual extraction for internal AI memory

RULE SCOPE:
Rules for "description" apply ONLY to the description field.
Rules for "objective_data" apply ONLY to the objective_data field.
Do NOT mix rules between the two fields.

IMPORTANT: These two fields have DIFFERENT purposes.

IMPORTANCE LEVELS:
🔴 CRITICAL: Life-threatening conditions, emergency situations, severe abnormalities
🟡 IMPORTANT: Significant abnormalities, chronic conditions, notable findings
⚪ NORMAL: Routine findings, values within normal ranges

CRITICAL RULES FOR description:
- Combine key findings into a readable medical summary
- ALWAYS include specific numerical values when present
- May include short contextual phrasing for clarity
- DO NOT invent diagnoses
- DO NOT add conclusions unless explicitly stated in the document
- Max 20 words

CRITICAL RULES FOR objective_data:
- objective_data MUST ALWAYS be written in ENGLISH
- STRICT factual extraction only
- Include only measured values or standardized scores
- Preserve original numbers and units exactly as written
- Ignore reference ranges and normal ranges
- Format: parameter value unit; parameter value unit
- NO interpretations
- NO conclusions
- Max 12 measurements
- If no measurable findings exist, return null

objective_data EXTRACTION RULES (Document type: {doc_type}):
{_get_objective_data_rules(doc_type)}

IMPORTANCE CLASSIFICATION:
- Base importance on severity of measured values or explicitly stated conditions
- Critical: Extremely abnormal measurements requiring immediate attention
- Important: Significantly abnormal measurements or new notable findings  
- Normal: Measurements within or near reference ranges

RESPONSE FORMAT (JSON only):
{{
    "category": "ONE OF: diagnosis, treatment, test, procedure, general",
    "importance": "critical|important|normal",
    "description": "User-friendly combined summary in {response_lang} (max 20 words)",
    "objective_data": "Strict factual measurements only (max 12 measurements)" | null
}}

If no important medical info found, return: {{"no_data": true}}

EXAMPLES:
- Lab results with abnormal values → important/test
- Multiple significant measurements → important/test
- Surgical procedure performed → important/procedure
- Routine check with normal values → normal/test

Adapt format and language to match the document content and user's language."""

    user_prompt = f"""MEDICAL DOCUMENT:
{document_text}

TASK:
Analyze the document and produce the JSON response according to the rules defined in the system instructions.

Return JSON only."""

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
                
                required_fields = ['category', 'importance', 'description']
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
        model = genai.GenerativeModel('gemini-2.5-pro')
        
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
    "category": "ONE OF: diagnosis, treatment, test, procedure, general",
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

async def save_single_medical_entry(user_id: int, entry_data: Dict, source_document_id: int, document_date: date = None) -> bool:
    """
    Сохраняет одну запись в медицинскую карту
    """
    if not entry_data:
        return True
        
    conn = await get_db_connection()
    try:
        query = """
        INSERT INTO medical_timeline (user_id, source_document_id, event_date, category, importance, description, objective_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        # Используем дату из классификатора или текущую дату как fallback
        event_date = datetime.now().date()
        
        if document_date:
            # Если document_date - строка, парсим её
            if isinstance(document_date, str):
                try:
                    event_date = datetime.strptime(document_date, '%Y-%m-%d').date()
                except ValueError:
                    # Пробуем другие форматы
                    for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y'):
                        try:
                            event_date = datetime.strptime(document_date, fmt).date()
                            break
                        except ValueError:
                            continue
            elif isinstance(document_date, date):
                event_date = document_date
        
        await conn.execute(
            query,
            user_id,
            source_document_id,
            event_date,
            entry_data.get('category', 'general'),
            entry_data.get('importance', 'normal'),
            entry_data.get('description', ''),
            entry_data.get('objective_data')
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

async def get_objective_history_for_specialist(user_id: int, document_type: str, limit: int = 7) -> str:
    """Получить историю objective_data по типу документа для специалиста"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT mt.event_date, d.subtype, mt.objective_data
            FROM medical_timeline mt
            JOIN documents d ON d.id = mt.source_document_id
            WHERE mt.user_id = $1
              AND d.document_type = $2
              AND d.confirmed = true
              AND mt.objective_data IS NOT NULL
              AND mt.objective_data != ''
            ORDER BY mt.event_date DESC
            LIMIT $3
        """, user_id, document_type, limit)
        
        if not rows:
            return ""
        
        lines = []
        for row in rows:
            date_str = row['event_date'].strftime('%Y-%m-%d') if row['event_date'] else '?'
            subtype = row['subtype']
            obj_data = row['objective_data']
            
            if subtype:
                lines.append(f"{date_str} | {subtype} → {obj_data}")
            else:
                lines.append(f"{date_str} → {obj_data}")
        
        return "\n".join(lines)
        
    except Exception as e:
        log_error_with_context(e, {"function": "get_objective_history_for_specialist"})
        return ""
    finally:
        await release_db_connection(conn)