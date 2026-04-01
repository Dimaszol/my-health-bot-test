# medical_timeline.py - Работа с медицинской картой пациента

import json
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
        SELECT mt.id, mt.event_date, mt.category, mt.importance, mt.description, mt.source_document_id, mt.objective_data, d.document_type, d.subtype
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
                'source_document_id': row['source_document_id'],
                'objective_data': row['objective_data'],
                'document_type': row['document_type'],
                'subtype': row['subtype']
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
# УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ИЗВЛЕЧЕНИЯ МЕДИЦИНСКИХ ДАННЫХ
# ==========================================

async def update_medical_timeline_on_document_upload(user_id: int, document_id: int, document_text: str, document_date: date = None, document_type: str = None, assistant_text: str = None) -> bool:
    """
    Универсальная функция обновления медкарты - добавляет ОДНУ сжатую запись с самыми важными данными
    """
    try:
        from db_postgresql import get_user_language
        lang = await get_user_language(user_id)

        medical_summary = await extract_medical_summary_universal_gpt(document_text, lang, document_type, assistant_text)

        if not medical_summary:
            return True

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

async def extract_medical_summary_universal_gpt(document_text: str, lang: str = "ru", document_type: str = None, assistant_text: str = None) -> Dict:
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

You receive TWO SOURCES of information:

SOURCE A (PRIMARY — RAW DOCUMENT DATA):
- Contains extracted data strictly from the current medical document
- This is the ONLY allowed source for introducing measurements

SOURCE B (SECONDARY — CLINICAL INTERPRETATION):
- Contains interpretation based on the document + patient history
- This source may contain additional or inferred information
- It is NOT a reliable source for new measurements

---

YOUR TASK:
Create ONE structured medical timeline entry.

You must return TWO fields:
1. description → user-friendly summary
2. objective_data → strict factual measurements

---

CRITICAL: SOURCE USAGE RULES

OBJECTIVE_DATA LOGIC (STRICT, MUST FOLLOW STEP-BY-STEP):

STEP 1 — Extract:
- Extract ALL measurable parameters ONLY from SOURCE A

STEP 2 — Match:
- For each parameter from SOURCE A:
  Try to find the SAME parameter in SOURCE B
  Matching can be based on:
  - exact name (e.g. glucose, WBC)
  - or clinical meaning (e.g. blood sugar = glucose)

STEP 3 — Override:
- If the same parameter exists in SOURCE B:
    - If values differ → USE value from SOURCE B (it overrides)
    - If values match → keep the value

STEP 4 — Restriction:
- If a parameter exists ONLY in SOURCE B:
    → IGNORE it completely
    → DO NOT include it in objective_data

STEP 5 — Finalization:
- objective_data must contain ONLY parameters originating from SOURCE A (with possible corrected values from SOURCE B)

---

ABSOLUTE RULES (objective_data):

- MUST be written in ENGLISH
- STRICT factual extraction only
- NO interpretations
- NO conclusions
- NO invented data
- Preserve exact numbers and units
- Ignore reference ranges
- Format: parameter value unit; parameter value unit
- Max 12 measurements
- If no measurable data → return null

---

DESCRIPTION RULES:

- description should be based primarily on SOURCE B
- Use SOURCE A values when needed for accuracy
- Combine key findings into a concise summary
- ALWAYS include important numerical values if present
- DO NOT invent diagnoses
- DO NOT add conclusions unless explicitly stated
- Max 20 words
- Language must match user language: {response_lang}

---

IMPORTANCE CLASSIFICATION:

🔴 critical: life-threatening conditions, extremely abnormal values
🟡 important: significant abnormalities, notable findings
⚪ normal: values within or near normal range

---

CATEGORY:

Return ONE of: diagnosis, treatment, test, procedure, general

---

DOCUMENT TYPE: {doc_type}

objective_data EXTRACTION RULES (Document type: {doc_type}):
{_get_objective_data_rules(doc_type)}

---

OUTPUT FORMAT (JSON ONLY):

{{
    "category": "diagnosis|treatment|test|procedure|general",
    "importance": "critical|important|normal",
    "description": "short summary in {response_lang} (max 20 words)",
    "objective_data": "parameter value unit; parameter value unit" | null
}}

If no important medical info found, return: {{"no_data": true}}"""

    # Формируем user prompt в зависимости от наличия assistant_text
    if assistant_text:
        user_prompt = f"""SOURCE A (DOCUMENT ONLY):
{assistant_text}

SOURCE B (FULL CONTEXT):
{document_text}

Analyze and return JSON."""
    else:
        user_prompt = f"""SOURCE A (DOCUMENT ONLY):
{document_text}

SOURCE B (FULL CONTEXT):
{document_text}

Analyze and return JSON."""

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