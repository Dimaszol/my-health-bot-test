# document_chat_processor.py
# Обработка контекста и генерация ответов для чата по документу

import re
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI  # ✅ ИСПРАВЛЕНО: AsyncOpenAI вместо OpenAI
import os

logger = logging.getLogger(__name__)

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
        - full_analysis: str - полный анализ документа
        - recent_messages: List - последние 3 пары сообщений (обрезанные)
        - last_bot_paragraph: str - последний абзац последнего AI ответа
        - file_path: str - путь к файлу документа
        - file_type: str - тип файла (pdf, jpg, png и т.д.)
    """
    from db_postgresql import get_db_connection, release_db_connection
    
    conn = await get_db_connection()
    try:
        # Получаем документ (включая file_path и file_type)
        doc = await conn.fetchrow(
            """SELECT title, full_analysis, file_path, file_type FROM documents 
               WHERE id = $1 AND user_id = $2""",
            document_id, user_id
        )
        
        if not doc:
            return None
        
        # Получаем последние 7 сообщений (текущее + 6 предыдущих)
        history = await conn.fetch(
            """SELECT role, message FROM document_chat_history
               WHERE document_id = $1 AND user_id = $2
               ORDER BY id DESC
               LIMIT 7""",
            document_id, user_id
        )
        
    finally:
        await release_db_connection(conn)
    
    # Извлекаем последний абзац последнего AI ответа
    last_bot_paragraph = ""
    for msg in reversed(history[1:7]):
        if msg['role'] == 'assistant':
            last_bot_paragraph = extract_last_paragraph(msg['message'])
            break
    
    # Обрезаем сообщения для контекста
    recent_messages = []
    for msg in reversed(history[1:7]):  # Пропускаем текущее сообщение
        role = msg['role']
        content = msg['message']
        
        # Обрезаем для экономии токенов
        if role == 'user':
            if len(content) > 500:
                content = content[:497] + "..."
        else:
            if len(content) > 150:
                content = content[:147] + "..."
        
        recent_messages.append({
            'role': role,
            'content': content
        })
    
    return {
        'document_title': doc['title'],
        'full_analysis': doc['full_analysis'],
        'recent_messages': recent_messages,
        'last_bot_paragraph': last_bot_paragraph,
        'file_path': doc['file_path'],
        'file_type': doc['file_type']
    }


def build_document_input(document_base64: str, file_type: str) -> dict:
    """
    Формирует правильный блок контента в зависимости от типа файла
    
    Args:
        document_base64: Base64 строка документа
        file_type: Тип файла (pdf, image, jpg, png и т.д.)
    
    Returns:
        dict: Блок контента для responses API или None
    """
    logger.debug(f"Processing file type: '{file_type}'")
    
    file_type = file_type.lower().strip()
    
    if file_type == "pdf":
        return {
            "type": "input_file",
            "file_data": f"data:application/pdf;base64,{document_base64}",
            "filename": "document.pdf"
        }
    
    # ✅ ИСПРАВЛЕНО: правильная структура для изображений
    elif file_type == "image" or file_type in ["jpg", "jpeg", "png", "webp"]:
        # Определяем media_type
        if file_type == "image":
            media_type = "image/jpeg"  # По умолчанию
        else:
            media_type = get_media_type(file_type)
        
        return {
            "type": "input_image",
            "image_url": f"data:{media_type};base64,{document_base64}"  # ✅ image_url!
        }
    
    else:
        logger.warning(f"⚠️ Неподдерживаемый тип файла: '{file_type}'")
        return None


async def generate_document_chat_response(
    context_data: Dict,
    user_message: str,
    lang: str = "ru",
    conversation_summary: str = ""
) -> str:
    """
    Генерирует ответ AI для чата по документу
    
    Args:
        context_data: Данные из process_document_chat_question
        user_message: Вопрос пользователя
        lang: Язык ответа
    
    Returns:
        str: Ответ AI
    """
    
    # System prompt
    system_prompt = f"""You are a calm medical explainer helping a patient understand their own medical document.

    CONTEXT:
    - Document title: {context_data['document_title']}
    - You have access to a previous AI-generated clinical analysis of this document.
    - The original document is NOT attached. Base your answers solely on the analysis provided below.

    SOURCE FRAMEWORK:
    - The AI analysis below represents an interpretation of the original document findings.
    - Use it as your primary source of factual data.
    - If something is not mentioned in the analysis, clearly state that the information is not available.
    - Do not invent or assume findings not present in the analysis.

    YOUR ROLE:
    - Help the patient understand what is written in their document.
    - Clarify medical terms in simple language.
    - Answer the patient’s specific question directly.
    - Provide context and explanation without rewriting the entire report.
    - Adjust interpretation if the patient provides new relevant context.

    IMPORTANT BEHAVIOR RULES:
    - Prioritize clarity over medical jargon.
    - Do NOT restate the full summary unless explicitly asked.
    - Answer only what the patient is asking.
    - If information is not present in the document, clearly state that it is not available.
    - If the question goes beyond the scope of the document, explain the limitation and avoid speculation.
    - Do not invent additional findings.
    - Do not provide definitive diagnoses.
    - Do not provide medication-specific advice (start, stop, adjust dose) unless explicitly stated in the document.
    Assume the patient has already read the summary and analysis. 
    Do not repeat factual listings unless specifically asked. 
    Refer to findings briefly without re-enumerating values.

    RISK COMMUNICATION:
    - Avoid amplifying fear.
    - Do not overemphasize worst-case scenarios.
    - When discussing risk, use proportional and neutral language.
    - Distinguish between “requires attention”, “commonly seen”, and “potentially serious” carefully.
    - Encourage consultation with a doctor for medical decisions, but do not repeat this in every paragraph.

    TONE:
    - Calm
    - Clear
    - Reassuring but not dismissive
    - Structured in short paragraphs when helpful
    - Focused and concise

    Respond in {get_language_name(lang)} language.

    PREVIOUS AI ANALYSIS (for context only):
    {context_data['full_analysis']}
    """

    summary_block = ""
    if conversation_summary:
        summary_block = f"""PATIENT HISTORY FROM RECENT CONVERSATIONS (last 7 days):
    {conversation_summary}

    """
    
    # Формируем контекст из истории
    history_context = ""
    if context_data['recent_messages']:
        history_context = "\n\nRECENT CONVERSATION:\n"
        for msg in context_data['recent_messages']:
            role_label = "Patient" if msg['role'] == 'user' else "Assistant"
            history_context += f"{role_label}: {msg['content']}\n"
    
    # Добавляем последний абзац
    if context_data['last_bot_paragraph']:
        history_context += f"\n🔸 LAST CONTEXT FROM ASSISTANT:\n{context_data['last_bot_paragraph']}\n"
    
    # Получаем оригинал документа в base64
    # document_base64 = await get_document_as_base64(
    #    context_data['file_path'],
    #    context_data['file_type']
    # )
    
   # Формируем user_prompt с контекстом
    user_prompt = f"""{summary_block}
{history_context}

Patient's question: {user_message}"""

    # Вызываем GPT-5.2 через responses API с документом
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_content_blocks = [
        {
            "type": "input_text",
            "text": user_prompt
        }
    ]

    #if document_base64:
    #    document_block = build_document_input(document_base64, context_data['file_type'])
    #    if document_block:
    #       user_content_blocks.append(document_block)

    response = await client.responses.create(
        model="gpt-5.2",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}]
            },
            {
                "role": "user",
                "content": user_content_blocks
            }
        ],
        max_output_tokens=2000
    )

    answer = (response.output_text or "").strip()
    logger.info("Document chat response generated")
    return answer


async def get_document_as_base64(file_path: str, file_type: str) -> str:
    """
    Загружает документ из Supabase и конвертирует в base64
    
    Args:
        file_path: Путь в Supabase Storage (например: users/123/medical_doc_xxx.pdf)
        file_type: Тип файла
    
    Returns:
        str: Base64 строка или пустая строка если не удалось
    """
    import base64
    
    try:
        # Получаем Supabase Storage manager
        from supabase_storage import get_storage_manager
        storage = get_storage_manager()
        
        # Скачиваем файл из Supabase
        response = storage.supabase.storage.from_(storage.bucket_name).download(file_path)
        
        # Проверяем что получили bytes
        if isinstance(response, bytes):
            return base64.b64encode(response).decode('utf-8')
        else:
            logger.error(f"Неверный тип ответа от Supabase: {type(response)}")
            return ""
            
    except Exception as e:
        logger.error(f"Ошибка загрузки документа для чата: {e}")
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


def extract_last_paragraph(text: str) -> str:
    """
    Извлекает последний абзац из текста (обычно это вопрос/контекст от AI)
    """
    # Убираем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Разбиваем на абзацы (двойной перенос или одинарный)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    if paragraphs:
        return paragraphs[-1]
    
    return ""


def get_language_name(lang: str) -> str:
    """Получить полное название языка"""
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian',
        'en': 'English',
        'de': 'German'
    }
    return lang_names.get(lang, 'Russian')