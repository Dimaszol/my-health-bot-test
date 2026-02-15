# document_questions.py - Генерация первого сообщения в document-chat

import os
from openai import AsyncOpenAI
from typing import Optional
import logging

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_and_save_first_message(
    document_id: int,
    user_id: int,
    full_analysis: str,
    importance: str,
    lang: str
) -> bool:
    """
    Генерирует и сохраняет первое сообщение от ИИ в document-chat
    
    Args:
        document_id: ID документа
        user_id: ID пользователя
        full_analysis: Полный анализ документа от Gemini
        importance: Уровень важности ("normal" | "important" | "critical")
        lang: Язык пользователя
    
    Returns:
        True если успешно, False если нет
    """
    
    # Пропускаем для normal
    if importance == "normal":
        return False
    
    # Языковые настройки
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian',
        'en': 'English',
        'de': 'German'
    }
    response_lang = lang_names.get(lang, 'Russian')
    
    # System prompt
    system_prompt = f"""You are generating the first message in a personalized medical document discussion chat.
    The user has already read the clinical analysis and summary.

    Your goal:
    1. Translate the key meaning of the findings into simple, everyday language.
    2. Briefly explain what this means in practical terms for the user.
    3. Show why clarifying details may be useful.
    4. Encourage further discussion through short, focused questions.
    5. Do NOT repeat the clinical text.
    6. Do NOT introduce new diagnoses.
    7. Do NOT deepen differential reasoning or expand the medical analysis.

    Structure:
    - First paragraph (2–4 short sentences): explain the core meaning of the findings in clear, non-medical language and indicate what this could mean practically.
    - Second paragraph: 1–3 short clarification questions that connect the findings to the user's personal context.
    - Avoid bullet points. Keep the text compact and readable.

    Tone:
    Calm, supportive, human.
    Clear and accessible for a non-medical person.
    Engaging but not alarming.

    Importance handling:
    If importance = normal:
    - Reassure calmly.
    - Emphasize that results look stable.
    - Mention that further clarification is optional but can help better understand the situation.
    If importance = important:
    - Explain that some findings deserve attention.
    - Briefly indicate why it is useful to clarify them.
    - Ask 2–3 focused questions.
    If importance = critical:
    - Explain that findings may be significant.
    - Briefly state why this matters.
    - Calmly suggest discussing with a doctor.
    - Ask 1–2 questions to better understand context.
    - Do not create panic or emotional pressure.
    
    Maximum length: 120–150 words.
    Keep sentences relatively short.
    Respond strictly in {response_lang}
    """

    # User prompt
    user_prompt = f"""Clinical analysis:
{full_analysis}

Document importance level: {importance}

Generate the first message for the document discussion chat."""

    try:
        response = await client.responses.create(
            model="gpt-5.2",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            max_output_tokens=300,
            temperature=0.5
        )
        
        first_message = (response.output_text or "").strip()
        
        if not first_message:
            return False
        
        # Сохраняем в document_chat_history
        from db_postgresql import get_db_connection, release_db_connection
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                """INSERT INTO document_chat_history (document_id, user_id, role, message)
                   VALUES ($1, $2, 'assistant', $3)""",
                document_id, user_id, first_message
            )
            logger.info(f"✅ Первое сообщение сохранено для документа {document_id}")
            return True
            
        finally:
            await release_db_connection(conn)
        
    except Exception as e:
        logger.error(f"Ошибка генерации первого сообщения: {e}")
        return False