# document_chat_processor.py
# Обработка контекста и генерация ответов для чата по документу

import re
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)


def _format_objective_data(raw: str) -> str:
    """Форматирует objective_data из строки 'param value unit; ...' в читаемый вид"""
    if not raw:
        return "No data"
    parts = raw.split(";")
    formatted = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        pieces = part.split(" ", 1)
        if len(pieces) == 2:
            formatted.append(f"{pieces[0].capitalize()}: {pieces[1]}")
        else:
            formatted.append(part)
    return "\n".join(formatted)


async def _get_medical_timeline_excluding_document(user_id: int, document_id: int, limit: int = 6) -> str:
    """
    Получает медкарту пользователя, исключая текущий документ.
    Аналог get_medical_timeline_simple из prompt_logger, но без текущего документа.
    """
    try:
        from db_postgresql import get_db_connection, release_db_connection
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT mt.event_date, mt.description, mt.importance, mt.objective_data,
                       d.document_type, mt.category, d.subtype
                FROM medical_timeline mt
                INNER JOIN documents d ON mt.source_document_id = d.id
                WHERE mt.user_id = $1
                  AND mt.source_document_id != $2
                  AND d.confirmed = true
                ORDER BY mt.event_date DESC, mt.created_at DESC
                LIMIT $3
            """, user_id, document_id, limit)

            if not rows:
                return ""

            lines = ["🏥 Medical timeline (latest first)", "---"]
            for row in rows:
                date_str = row['event_date'].strftime('%Y-%m-%d') if row['event_date'] else 'N/A'
                doc_type = (row['document_type'] or row['category'] or 'general').upper()
                subtype = row['subtype'] or "N/A"

                line = f"{date_str} | {doc_type} | {subtype}"
                if row['objective_data']:
                    line += f"\nOBJECTIVE:\n{_format_objective_data(row['objective_data'])}"
                line += f"\nINTERPRETATION:\n{(row['description'] or '')[:150]}"
                line += "\n---"
                lines.append(line)

            return "\n".join(lines)

        finally:
            await release_db_connection(conn)

    except Exception:
        return ""


async def process_document_chat_question(
    user_id: int,
    document_id: int,
    user_message: str,
    lang: str = "ru"
) -> Dict:
    """
    Обрабатывает вопрос пользователя по документу

    Returns:
        Dict с ключами:
        - document_title: str
        - full_analysis: str - полный анализ документа
        - recent_messages: List - последние 3 пары сообщений (6 сообщений)
        - file_path: str
        - file_type: str
        - medical_timeline: str - медкарта других документов пользователя
    """
    from db_postgresql import get_db_connection, release_db_connection

    conn = await get_db_connection()
    try:
        doc = await conn.fetchrow(
            """SELECT title, full_analysis, file_path, file_type FROM documents
               WHERE id = $1 AND user_id = $2""",
            document_id, user_id
        )

        if not doc:
            return None

        # Получаем последние 7 сообщений: 1 текущее + 6 предыдущих (3 пары)
        history = await conn.fetch(
            """SELECT role, message FROM document_chat_history
               WHERE document_id = $1 AND user_id = $2
               ORDER BY id DESC
               LIMIT 7""",
            document_id, user_id
        )

    finally:
        await release_db_connection(conn)

    # Медкарта других документов пользователя (текущий исключён)
    medical_timeline = await _get_medical_timeline_excluding_document(user_id, document_id)

    # Формируем историю: пропускаем history[0] (текущее сообщение пользователя)
    # Последнее сообщение ассистента передаём полностью, остальные режем до 500
    # Все сообщения пользователя режем до 800
    recent_messages = []
    last_assistant_done = False

    for msg in reversed(history[1:]):
        role = msg['role']
        content = msg['message']

        if role == 'assistant' and not last_assistant_done:
            # Последнее сообщение ассистента — передаём полностью
            last_assistant_done = True
        elif role == 'assistant':
            if len(content) > 500:
                content = content[:497] + "..."
        elif role == 'user':
            if len(content) > 800:
                content = content[:797] + "..."

        recent_messages.append({
            'role': role,
            'content': content
        })

        if len(recent_messages) >= 6:
            break

    return {
        'document_title': doc['title'],
        'full_analysis': doc['full_analysis'],
        'recent_messages': recent_messages,
        'file_path': doc['file_path'],
        'file_type': doc['file_type'],
        'medical_timeline': medical_timeline,
    }


def build_document_input(document_base64: str, file_type: str) -> dict:
    """
    Формирует правильный блок контента в зависимости от типа файла
    """
    file_type = file_type.lower().strip()

    if file_type == "pdf":
        return {
            "type": "input_file",
            "file_data": f"data:application/pdf;base64,{document_base64}",
            "filename": "document.pdf"
        }

    elif file_type == "image" or file_type in ["jpg", "jpeg", "png", "webp"]:
        if file_type == "image":
            media_type = "image/jpeg"
        else:
            media_type = get_media_type(file_type)

        return {
            "type": "input_image",
            "image_url": f"data:{media_type};base64,{document_base64}"
        }

    else:
        logger.warning(f"Unsupported file type: '{file_type}'")
        return None


async def generate_document_chat_response(
    context_data: Dict,
    user_message: str,
    lang: str = "ru",
    conversation_summary: str = ""
) -> str:
    """
    Генерирует ответ AI для чата по документу.
    История передаётся как настоящие messages с ролями — не как текст.
    """

    # Обрезаем full_analysis для предотвращения dilution внимания
    full_analysis = (context_data['full_analysis'] or "")[:6000]

    system_prompt = f"""You are a medical document explainer helping a patient understand their own medical document.

Document: {context_data['document_title']}
Response language: {get_language_name(lang)}

=== PRIORITY RULES (strictly enforced) ===
1. Use AI analysis as the primary medical source. You may also use patient-provided information from the conversation as factual context.
2. Do NOT invent or assume findings not present in the analysis.
3. If information is missing → explicitly say it is not available.
4. Do NOT restate the full analysis unless the patient explicitly asks.
5. Do NOT provide definitive diagnoses or medication advice (start/stop/adjust dose) unless explicitly stated in the document.

=== PRODUCT ROLE ===

You are an AI assistant in PulseBook, focused on analyzed document.

Users cannot upload files or photo here — only via the section where they manage their medical documents.

If additional medical results are needed:
- Briefly mention what is missing
- Suggest uploading the document to the medical records section for more accurate analysis

=== CONTEXT PRIORITY ===

1. AI ANALYSIS = primary medical source
2. Patient statements in conversation = factual unless clearly uncertain
3. Do NOT ask again if the patient already provided the information

=== SECONDARY RULES ===
- Answer only what the patient is asking — stay focused.
- Explain medical terms in simple, everyday language.
- Use short paragraphs. Be concise.
- Discuss risk proportionally: distinguish "requires attention" vs "commonly seen" vs "potentially serious".
- Recommend doctor consultation once if relevant — do not repeat it in every paragraph.
- Tone: calm, clear, reassuring but not dismissive.

=== CONTEXT CONSISTENCY RULE ===

Before asking any clarification:
- Check the conversation history for an existing answer
- Treat clear user statements as factual context
- Do not repeat questions that were already answered
- Extract and reuse key facts from prior messages instead of re-asking

=== AI ANALYSIS OF THE DOCUMENT ===
{full_analysis}
"""

    # Блок медкарты других документов
    timeline = context_data.get('medical_timeline', '')
    timeline_block = ""
    if timeline:
        timeline_block = f"""🏥 PATIENT MEDICAL HISTORY (from other documents, for context only):
{timeline}

"""

    # Блок сводки разговоров
    summary_block = ""
    if conversation_summary:
        summary_block = f"""🧠 PATIENT HISTORY FROM RECENT CONVERSATIONS (last 7 days):
{conversation_summary}

"""

    # Собираем messages
    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}]
        }
    ]

    # Контекст (timeline + summary) — как user, чтобы модель воспринимала как данные пациента
    context_text = f"{timeline_block}{summary_block}".strip()
    if context_text:
        messages.append({
            "role": "user",
            "content": [{"type": "input_text", "text": context_text}]
        })

    # История диалога с правильными ролями (не как текст)
    for msg in context_data['recent_messages']:
        if msg['role'] == 'assistant':
            messages.append({
                "role": "assistant",
                "content": [{"type": "output_text", "text": msg['content']}]
            })
        else:
            messages.append({
                "role": "user",
                "content": [{"type": "input_text", "text": msg['content']}]
            })

    # Текущий вопрос пользователя — последним
    messages.append({
        "role": "user",
        "content": [{"type": "input_text", "text": user_message}]
    })

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.responses.create(
        model="gpt-5.2",
        input=messages,
        max_output_tokens=2000
    )

    answer = (response.output_text or "").strip()
    logger.info("Document chat response generated")
    return answer


async def get_document_as_base64(file_path: str, file_type: str) -> str:
    """
    Загружает документ из Supabase и конвертирует в base64
    """
    import base64

    try:
        from supabase_storage import get_storage_manager
        storage = get_storage_manager()

        response = storage.supabase.storage.from_(storage.bucket_name).download(file_path)

        if isinstance(response, bytes):
            return base64.b64encode(response).decode('utf-8')
        else:
            logger.error("Unexpected response type from storage")
            return ""

    except Exception:
        logger.error("Failed to load document for chat")
        return ""


def get_media_type(file_type: str) -> str:
    """Определяет media_type по расширению файла"""
    media_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp'
    }
    return media_types.get(file_type.lower(), 'image/jpeg')


def get_language_name(lang: str) -> str:
    """Получить полное название языка"""
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian',
        'en': 'English',
        'de': 'German'
    }
    return lang_names.get(lang, 'Russian')