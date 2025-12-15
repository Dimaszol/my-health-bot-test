# gpt.py - МОДИФИЦИРОВАННАЯ ВЕРСИЯ с асинхронными функциями
# Все названия функций остаются теми же, просто добавляем async/await

import os
import base64
import asyncio
import logging
import re
from openai import AsyncOpenAI  # 🔄 ИЗМЕНЕНИЕ: AsyncOpenAI вместо OpenAI
from datetime import datetime
from dotenv import load_dotenv
from error_handler import OpenAIError, log_error_with_context, FileProcessingError
from subscription_manager import check_gpt4o_limit, spend_gpt4o_limit
from gemini_analyzer import send_to_gemini_vision

load_dotenv()
logger = logging.getLogger(__name__)
# 🔄 ИЗМЕНЕНИЕ: AsyncOpenAI клиент
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📊 Семафор для ограничения одновременных запросов
OPENAI_SEMAPHORE = asyncio.Semaphore(5)

def safe_telegram_text(text: str) -> str:
    """
    ИСПРАВЛЕННАЯ версия: преобразует Markdown в HTML для Telegram
    """
    if not text:
        return ""
    
    # 1. Преобразуем Markdown заголовки в жирный текст
    # ## Заголовок -> <b>Заголовок</b>
    text = re.sub(r'^### (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # 2. Преобразуем жирный текст: **текст** -> <b>текст</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # 3. Преобразуем курсив: *текст* -> <i>текст</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    
    # 4. Преобразуем подчеркивание: _текст_ -> <u>текст</u>
    text = re.sub(r'_(.+?)_', r'<u>\1</u>', text)
    
    # 5. Преобразуем код: `код` -> <code>код</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # 6. Преобразуем списки: - пункт -> • пункт
    text = re.sub(r'^- (.+)$', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'• \1', text, flags=re.MULTILINE)
    
    # 7. Экранируем HTML символы (но не наши теги)
    # Сначала заменяем наши теги на временные маркеры
    temp_markers = {}
    html_tags = ['<b>', '</b>', '<i>', '</i>', '<u>', '</u>', '<code>', '</code>']
    
    for i, tag in enumerate(html_tags):
        marker = f"__TEMP_TAG_{i}__"
        temp_markers[marker] = tag
        text = text.replace(tag, marker)
    
    # Экранируем остальные HTML символы
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Возвращаем наши теги обратно
    for marker, tag in temp_markers.items():
        text = text.replace(marker, tag)
    
    # 8. Убираем лишние переносы строк (больше 2 подряд)
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    
    return text.strip()


def split_long_message(text: str, max_length: int = 4000) -> list:
    """
    Разбивает длинные сообщения на части для Telegram (с поддержкой HTML)
    """
    if len(text) <= max_length:
        return [text]
    
    # Разбиваем по абзацам (двойной перенос строки)
    paragraphs = text.split('\n\n')
    messages = []
    current_message = ""
    
    for paragraph in paragraphs:
        # Если абзац помещается в текущее сообщение
        if len(current_message + paragraph + '\n\n') <= max_length:
            current_message += paragraph + '\n\n'
        else:
            # Сохраняем текущее сообщение и начинаем новое
            if current_message:
                messages.append(current_message.strip())
            
            # Если сам абзац слишком длинный, разбиваем его
            if len(paragraph) > max_length:
                # Разбиваем по предложениям
                sentences = paragraph.split('. ')
                temp_paragraph = ""
                
                for sentence in sentences:
                    if len(temp_paragraph + sentence + '. ') <= max_length:
                        temp_paragraph += sentence + '. '
                    else:
                        if temp_paragraph:
                            messages.append(temp_paragraph.strip())
                        temp_paragraph = sentence + '. '
                
                if temp_paragraph:
                    current_message = temp_paragraph
            else:
                current_message = paragraph + '\n\n'
    
    # Добавляем последнее сообщение
    if current_message:
        messages.append(current_message.strip())
    
    return messages

def async_safe_openai_call(max_retries: int = 3, delay: float = 2.0):
    """Асинхронный декоратор для безопасных вызовов OpenAI API"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            
            async with OPENAI_SEMAPHORE:
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                        
                    except Exception as e:
                        last_error = e
                        log_error_with_context(e, {
                            "function": func.__name__, 
                            "attempt": attempt + 1
                        })
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay * (attempt + 1))
                        
                raise OpenAIError(f"OpenAI API недоступен: {last_error}")
        
        return wrapper
    return decorator

# 🔄 ВСЕ ФУНКЦИИ ОСТАЮТСЯ С ТЕМИ ЖЕ НАЗВАНИЯМИ, просто добавляем async

@async_safe_openai_call(max_retries=2, delay=1.0)
async def summarize_note_text(note: str, lang: str = "ru") -> str:  # 🔄 async
    """Безопасное создание резюме заметки"""
    lang_instruction = {
        "ru": "Ответь на русском языке.",
        "uk": "Відповідай українською мовою.",
        "en": "Respond in English language.",
        "de": "Antworte auf Deutsch."
    }

    today_str = datetime.now().strftime("%d.%m.%Y")

    system_prompt = (
        "Summarize the input briefly and medically, suitable for an AI health assistant. "
        "Do not include phrases like 'the patient says' or 'patient reports'. "
        "Focus only on clinical content and key observations. "
        f"Begin the summary with the current date in this format: [{today_str}] "
        + lang_instruction.get(lang, "Respond in English language.")
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": note}
        ],
        max_tokens=300,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=1.5)
async def generate_title_for_note(note: str) -> str:  # 🔄 async
    """Безопасное создание заголовка для заметки"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = (
        "You are an AI medical assistant. Create a short title for this health-related note.\n"
        "Requirements:\n"
        "- Use the same language as the input note.\n"
        "- Keep the title concise (2 to 5 words).\n"
        f"- Begin the title with today's date: {today_str}:\n"
        "Examples:\n"
        f"{today_str}: Chest Pain After Jogging\n"
        f"{today_str}: Mild Cough and Fatigue\n"
    )
    
    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": note}
        ],
        max_tokens=25,
        temperature=0.6
    )
    
    title = response.choices[0].message.content.strip().strip('"\'')
    return title

@async_safe_openai_call(max_retries=2, delay=3.0)
async def extract_text_from_image(image_path: str) -> str:  # 🔄 async
    """Безопасное извлечение текста из изображения"""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except FileNotFoundError:
        raise FileProcessingError(f"Файл {image_path} не найден", "Файл не найден для обработки")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = (
        "You are a medical assistant specialized in extracting text from scanned documents and images. "
        "⚠️ Your task is to accurately extract all readable medical text **in the original language** of the document. "
        "⚠️ However, you must remove all personal and identifying information — including full names of patients or doctors, age, gender, addresses, card numbers, clinic or hospital names. "
        "Do not summarize, skip, or interpret the content. Do not add explanations. Just extract the pure medical content."
    )

    user_prompt = (
        "This is a scanned medical document (e.g., discharge summary, lab report, consultation, prescription, or form). "
        "Extract the entire readable text **in the same language as in the image**, but remove all of the following:\n"
        "- Full names of any individuals (patients, doctors, lab staff)\n"
        "- Age, gender\n"
        "- Addresses, contact details, ID or card numbers\n"
        "- Clinic, hospital, laboratory names or logos\n\n"
        "Do NOT explain your actions or mention what was removed. Do NOT translate the content. Just return the clean medical text."
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ],
        max_tokens=1500,
        temperature=0
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=3.0)
async def send_to_gpt_vision(image_path: str, lang: str, prompt: str = None):
    return await send_to_gemini_vision(image_path, lang, prompt)

@async_safe_openai_call(max_retries=2, delay=1.0)
async def update_medications_via_gpt(user_input: str, current_list: list, user_lang: str = 'ru') -> list:
    """
    Мультиязычное безопасное обновление списка лекарств
    
    Args:
        user_input: Ввод пользователя на любом языке
        current_list: Текущий список лекарств
        user_lang: Язык пользователя для названий времени
    
    Returns:
        Обновленный список лекарств в формате JSON
    """
    
    # Словарь языков для GPT
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian', 
        'en': 'English',
        'de': 'German'
    }
    response_language = lang_names.get(user_lang, 'Russian')
    
    # Примеры времени на разных языках
    time_examples = {
        'ru': {
            'morning': 'утром → 08:00',
            'afternoon': 'днём → 13:00', 
            'evening': 'вечером → 20:00',
            'night': 'перед сном → 22:00'
        },
        'uk': {
            'morning': 'вранці → 08:00',
            'afternoon': 'вдень → 13:00',
            'evening': 'ввечері → 20:00', 
            'night': 'перед сном → 22:00'
        },
        'en': {
            'morning': 'morning → 08:00',
            'afternoon': 'afternoon → 13:00',
            'evening': 'evening → 20:00',
            'night': 'before bed → 22:00'
        },
        'de': {
            'morning': 'morgens → 08:00',
            'afternoon': 'nachmittags → 13:00', 
            'evening': 'abends → 20:00',
            'night': 'vor dem Schlafengehen → 22:00'
        }
    }
    
    examples = time_examples.get(user_lang, time_examples['ru'])
    
    # Английский промпт для стабильности
    prompt = (
        f"You are a medical assistant. The user has a list of medications in JSON format, "
        f"and they input changes in natural language: add, remove, change time. "
        f"Return the updated list in JSON format with the following fields:\n"
        f"- name (medication name in {response_language})\n"
        f"- time (time in HH:MM format)\n"
        f"- label (original time phrase as user wrote it in {response_language})\n\n"
        f"Match phrases with intake times. Examples for {response_language}:\n"
        f"- {examples['morning']}\n"
        f"- {examples['afternoon']}\n" 
        f"- {examples['evening']}\n"
        f"- {examples['night']}\n\n"
        f"📋 Current medication list:\n{current_list}\n\n"
        f"📨 User input (in {response_language}):\n{user_input}\n\n"
        f"Return the updated list as a JSON array without comments or explanations. "
        f"The response should start and end with square brackets, containing objects with keys: name, time, label. "
        f"If user asks to remove all medications (e.g., 'remove all', 'clear list', 'delete everything'), return an empty array: []. "
        f"Keep medication names and time labels in {response_language} language.\n\n"
        f"Example of correct format:\n"
        f"[{{\"name\": \"Aspirin\", \"time\": \"18:00\", \"label\": \"evening\"}}, {{\"name\": \"Omeprazole\", \"time\": \"22:00\", \"label\": \"before bed\"}}]"
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": f"You are a helpful assistant that updates medication lists based on user descriptions. Always respond with medication names and time labels in {response_language} language."
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2
    )
    
    raw_text = response.choices[0].message.content.strip()

    import json
    try:
        result = json.loads(raw_text)
        
        # Дополнительная валидация для мультиязычности
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and all(key in item for key in ['name', 'time', 'label']):
                    # Проверяем что время в правильном формате
                    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', item['time']):
                        item['time'] = '08:00'  # Fallback
                else:
                    return current_list  # Возвращаем старый список
        
        return result
        
    except Exception as e:
        log_error_with_context(e, {
            "function": "update_medications_via_gpt", 
            "raw_response": raw_text[:200],
            "user_lang": user_lang
        })
        return current_list  # Возвращаем старый список при ошибке

@async_safe_openai_call(max_retries=2, delay=1.0)
async def ask_structured(text: str, lang: str = "ru", max_tokens: int = 3000) -> str:
    """Создание красивого отображения медицинского документа для пользователя - raw_text в таблице documents"""
    
    system_prompt = (
        "You are a medical information designer who creates clear, beautiful, and patient-friendly "
        "medical document summaries. Your goal is to make medical information easily readable and "
        "well-organized for patients while preserving all important clinical details. "
        f"⚠️ Always respond strictly in '{lang}' language, regardless of input language."
    )

    user_prompt = (
        "⚠️ DOCUMENT FORMATTING TASK:\n"
        "Transform this medical information into a beautiful, clear summary that a patient can easily read and reference.\n\n"
        
        "🔒 PRIVACY & CONTENT RULES:\n"
        "• REMOVE ALL personal identifiers: patient names, doctor names, medical record numbers, addresses, phone numbers\n"
        "• REMOVE phrases like 'the patient', 'patient reports', 'patient was advised' - focus on medical content only\n"
        "• REMOVE administrative text, disclaimers, legal notices, and non-medical formal phrases\n"
        "• KEEP all medical data: diagnoses, test results, measurements, medications, recommendations\n\n"
        
        "📋 STRUCTURE & FORMATTING:\n"
        "⚠️ DO NOT include a document title at the beginning - the title will be added separately.\n"
        "⚠️ Start directly with the content sections using **bold headers** for main sections.\n"
        "• Use bullet points (•) for lists of findings, medications, or recommendations\n"
        "• Group related information logically (lab results by system, imaging by organ, etc.)\n"
        "• Highlight abnormal values with 🔍 emoji when values are outside normal ranges\n"
        "• Use clear, scannable formatting that's easy to read on mobile devices\n\n"
        
        "🏥 MEDICAL CONTENT GUIDELINES:\n"
        "• Include ALL numerical values with units and reference ranges when available\n"
        "• Clearly indicate when values are elevated, decreased, or normal\n"
        "• Preserve exact medical terminology but add brief explanations in parentheses when helpful\n"
        "• Maintain diagnostic codes (ICD, medical classifications) when present\n"
        "• Group medications with dosages and frequencies clearly\n"
        "• Make recommendations actionable and specific\n\n"
        
        "✨ READABILITY OPTIMIZATION:\n"
        "• Use short paragraphs and clear sections\n"
        "• Make key findings easy to spot and understand\n"
        "• Organize information from most important to supporting details\n"
        "• Use consistent formatting throughout\n"
        "• Ensure the summary serves as a complete reference the patient can save and review\n\n"
        
        "🚫 AVOID:\n"
        "• Complex medical tables (convert to readable lists)\n"
        "• Redundant information or unnecessary repetition\n"
        "• Overly technical explanations without context\n"
        "• Poor formatting that's hard to read on small screens\n\n"
        
        "GOAL: Create a document that patients will want to save, reference, and easily understand while preserving complete medical accuracy.\n\n"
        
        f"MEDICAL DOCUMENT TO FORMAT:\n{text}"
    )

    full_input = f"{system_prompt}\n\n{user_prompt}"
    
    response = await client.responses.create(
        model="gpt-5.2",
        input=full_input,
        max_output_tokens=2500
    )
    
    return (response.output_text or "").strip()

@async_safe_openai_call(max_retries=2, delay=1.0)
async def enrich_query_for_vector_search(user_question: str) -> str:
    """✅ ИСПРАВЛЕННАЯ ВЕРСИЯ: Прямой вызов без лишних функций"""
    
    prompt = f"""
User asked a medical question: "{user_question}"

Task: Create a CONCISE medical search query for vector database.

RULES:
• Remove filler words ("what can you tell me", "please explain", "help me")
• Add relevant medical terminology
• DO NOT explain, DO NOT say "we can rephrase this"
• Respond ONLY with the expanded query, no commentary
• Respond in the SAME LANGUAGE as the user's question

EXAMPLES:
Question: "что по узи?" → Answer: "Результаты УЗИ обследования с описанием структур органов, размеров, эхогенности"
Question: "blood test results?" → Answer: "Blood test results: hemoglobin, leukocytes, ESR, glucose, biochemical parameters"
Question: "що з МРТ?" → Answer: "Результати МРТ дослідження з описом змін у тканинах, структурах, можливі патології"

Your answer for "{user_question}":
"""
    
    # 🎯 ПРЯМОЙ ВЫЗОВ с правильными параметрами для технической задачи
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are a medical query processor. Create concise search queries without explanations."
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,      # ✅ Достаточно для короткого запроса
        temperature=0.2      # ✅ Низкая креативность для технической задачи
    )
    
    # Простая очистка
    cleaned_response = response.choices[0].message.content.strip().strip('"\'')
    
    # Ограничиваем длину
    if len(cleaned_response) > 300:
        cleaned_response = cleaned_response[:300].strip()
    
    # Fallback
    if len(cleaned_response) < 10:
        cleaned_response = user_question
    
    return cleaned_response

@async_safe_openai_call(max_retries=2, delay=1.0)
async def ask_gpt_keywords(prompt: str) -> str:  # 🔄 async
    """Безопасное извлечение ключевых слов"""
    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a medical keyword extractor."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=1.0)
async def extract_keywords(text: str) -> list[str]:
    """✅ КРАТКАЯ версия извлечения ключевых слов"""
    
    prompt = f"""
        You are a medical expert. Extract **core medical terms** from the following text that best represent its clinical meaning and can be used for semantic search. Include only the most essential:

        – disease names  
        – histological diagnoses  
        – medical procedures  
        – anatomical structures  
        – classification systems (e.g., Gleason, Grade Group, ICD)

        Then, add **2 additional terms** that are common synonyms or broader medical concepts related to the content — terms that could help retrieve this text in a keyword-based search.

        🔹 Do not include:
        – general language (e.g., color, size, shape)  
        – administrative or technical terms (e.g., code, document, date)  
        – numbers or measurement values  
        – repeated or irrelevant words

        ⚠️ Return exactly **5–7 terms total**:
        – up to 5 essential terms  
        – plus 2 synonym or related terms

        All terms must be:
        – in **dictionary form**  
        – in **English only**, even if the original text is in another language
        – **comma-separated**, with no explanations.

        "{text}"
        """
    
    try:
        raw = await ask_gpt_keywords(prompt)
        keywords_list = [w.strip().lower() for w in raw.split(",") if len(w.strip()) > 1]
        return keywords_list
        
    except Exception as e:
        log_error_with_context(e, {"function": "extract_keywords", "text_length": len(text)})
        return []


@async_safe_openai_call(max_retries=3, delay=2.0)
async def ask_doctor(context_text: str, user_question: str, 
                    lang: str, user_id: int = None, use_gemini: bool = False) -> str:
    """
    Главный промт ответов в чате
    """
    
    # ✅ АНАЛИЗИРУЕМ НЕДАВНЮЮ ИСТОРИЮ
    recent_interaction = False
    if context_text and len(context_text.strip()) > 0:
        recent_interaction = True
    
    # ✅ ОПРЕДЕЛЯЕМ ТИП ОБЩЕНИЯ
    greeting_words = ['привет', 'здравствуй', 'добро пожаловать', 'hello', 'hi', 'вітаю', 'добрий день']
    is_greeting = any(word in user_question.lower() for word in greeting_words)
    
    # 🔧 ЯЗЫКОВАЯ ФИКСАЦИЯ для продвинутых моделей
    if lang == "ru":
        lang_instruction = "КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке."
    elif lang == "uk":
        lang_instruction = "КРИТИЧНО ВАЖЛИВО: Відповідай ТІЛЬКИ українською мовою."
    elif lang == "en":
        lang_instruction = "CRITICAL: Respond ONLY in English."
    elif lang == "de":
        lang_instruction = "KRITISCH WICHTIG: Antworten Sie NUR auf Deutsch."
    else:
        lang_instruction = "КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке."
    
    # Базовый system prompt
    base_system_prompt = (
        "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
        "You speak in a friendly, human tone and provide explanations when needed. "
        f"Always respond in the '{lang}' language."
    )

    # ✅ ПРОСТАЯ ЛОГИКА ВЫБОРА МОДЕЛИ
    if use_gemini:
        # Есть лимиты - используем GPT-5.2 с усиленным промптом
        model = "gpt-5.2"
        system_prompt = f"""
{base_system_prompt}

🚨 LANGUAGE ENFORCEMENT RULES:
{lang_instruction}

🧠 ADVANCED GPT-5 MEDICAL CAPABILITIES (MANDATORY):
- Perform deep step-by-step clinical reasoning with explicit logic chains
- Comprehensive understanding of lab results patterns and anomalies
- Interpret lab values as a physician would, flagging anomalies and patterns
- Base recommendations on evidence and major guidelines (NICE, ADA, ESC, WHO, etc.)
- Personalized risk assessment based on complete medical history
- Evidence-based recommendations with latest medical research insights
- Explicitly separate *observations* (what data shows) from *interpretations* (clinical meaning)

"""
        model_info = "gpt-5.2"
        
    else:
        # Нет лимитов - используем GPT-4o-mini
        model = "gpt-4o-mini"
        system_prompt = base_system_prompt
        model_info = "GPT-4o-mini"

    # ✅ ИНСТРУКЦИИ с учетом контекста общения
    if recent_interaction and not is_greeting:
        instruction_prompt = (
            "Continue the ongoing medical conversation naturally. Do NOT greet the patient again if you've already been talking. "
            "You have access to the user's health profile, medical documents, imaging reports, conversation history, and memory notes. "
            "Answer only questions related to the user's health — symptoms, diagnostics, treatment, risks, interpretation of reports, etc. "
            "If the question is not directly related to medical symptoms, diagnostics, treatment, or documented findings — but still relevant to health (e.g., vitamins, lifestyle, prevention) — you may give helpful information. "
            "Only decline if the question is clearly off-topic (e.g., movies, politics). "
            "Do not repeat that you're an AI. Do not ask follow-up questions unless critical. "
            "Use the document summaries and analysis results as clinical findings. Do not say you can't see images. "
            "If information is missing, offer a preliminary suggestion and explain what's lacking. "
            "⚠️ IMPORTANT: Since you've been talking recently, go straight to answering the question without greeting."
        )
    else:
        instruction_prompt = (
            "You have access to the user's health profile, medical documents, imaging reports, conversation history, and memory notes. "
            "Answer only questions related to the user's health — symptoms, diagnostics, treatment, risks, interpretation of reports, etc. "
            "If the question is not directly related to medical symptoms, diagnostics, treatment, or documented findings — but still relevant to health (e.g., vitamins, lifestyle, prevention) — you may give helpful information. "
            "Only decline if the question is clearly off-topic (e.g., movies, politics). "
            "Do not repeat that you're an AI. Do not ask follow-up questions unless critical. "
            "Use the document summaries and analysis results as clinical findings. Do not say you can't see images. "
            "If information is missing, offer a preliminary suggestion and explain what's lacking."
        )

    enhanced_system_prompt = f"{system_prompt}\n\n{instruction_prompt}"    
       
    # ✅ ЕДИНЫЙ ВЫЗОВ API
    try:
        # GPT-5.2 использует responses API
        if model == "gpt-5.2":
            full_input = f"{enhanced_system_prompt}\n\n{context_text}\n\nI have reviewed the patient's medical information and am ready to answer the question.\n\nPatient's question: {user_question}"
            
            response = await client.responses.create(
                model=model,
                input=full_input,
                max_output_tokens=3000
            )
            
            answer = (response.output_text or "").strip()
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": context_text},
                    {"role": "assistant", "content": "I have reviewed the patient's medical information and am ready to answer the question."},
                    {"role": "user", "content": f"Patient's question: {user_question}"}
                ],
                max_tokens=2500,
                temperature=0.5,
            )
        
            answer = response.choices[0].message.content.strip()
        
        return safe_telegram_text(answer)
        
    except Exception as e:
        logger.error(f"❌ Ошибка модели {model}: {str(e)}")
        
        # Fallback на GPT-4o-mini при любой ошибке
        if model != "gpt-4o-mini":
            try:
                logger.warning(f"⚠️ Fallback на GPT-4o-mini")
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": context_text},
                        {"role": "assistant", "content": "I have reviewed the patient's medical information and am ready to answer the question."},
                        {"role": "user", "content": f"Patient's question: {user_question}"}
                    ],
                    max_tokens=2500,
                    temperature=0.5
                )
                
                answer = response.choices[0].message.content.strip()
                return safe_telegram_text(answer)
                
            except Exception as fallback_error:
                logger.error(f"❌ Fallback тоже не работает: {str(fallback_error)}")
        
        return safe_telegram_text("Извините, временная техническая ошибка. Попробуйте повторить запрос.")


async def ask_doctor_gemini(system_prompt: str, full_prompt: str, lang: str = "ru") -> str:
    """
    Отдельная функция для GPT-5 - С ЖЕСТКОЙ ФИКСАЦИЕЙ ЯЗЫКА
    """
    try:
        # Убираем импорт Gemini, используем уже импортированный OpenAI client
        
        # 🔧 УСИЛЕННАЯ ЯЗЫКОВАЯ ФИКСАЦИЯ на основе переданного lang
        if lang == "ru":
            lang_instruction = "КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке. Никогда не переключайся на украинский или английский."
        elif lang == "uk":
            lang_instruction = "КРИТИЧНО ВАЖЛИВО: Відповідай ТІЛЬКИ українською мовою. Ніколи не переключайся на російську чи англійську."
        elif lang == "en":
            lang_instruction = "CRITICAL: Respond ONLY in English. Never switch to Russian or Ukrainian."
        elif lang == "de":
            lang_instruction = "KRITISCH WICHTIG: Antworten Sie NUR auf Deutsch. Wechseln Sie niemals zu Russisch, Ukrainisch oder Englisch."
        else:
            lang_instruction = "КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке."
        
        # 🔧 МОДИФИЦИРУЕМ ПРОМПТ с жесткой языковой фиксацией
        enhanced_system_prompt = f"""
{system_prompt}

🚨 LANGUAGE ENFORCEMENT RULES:
{lang_instruction}

If you start responding in the wrong language, immediately stop and restart in the correct language.
The user expects consistency in language throughout the entire response.
Never mix languages within a single response.
"""
        
        # Объединяем enhanced system и user промпты
        combined_prompt = f"{enhanced_system_prompt}\n\n{full_prompt}"

        # Заменяем Gemini на GPT-5
        response = await client.chat.completions.create(
            model="gpt-5-chat-latest",
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=2500,
            temperature=0.5,
        )
        
        # Обработка ответа (адаптируем под OpenAI формат)
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content.strip()
            return safe_telegram_text(answer)
        
        raise Exception("GPT-5 не вернул валидный ответ")
        
    except Exception as e:
        error_msg = "Извините, временная техническая ошибка. Попробуйте повторить запрос."
        return safe_telegram_text(error_msg)

@async_safe_openai_call(max_retries=2, delay=1.0)
async def is_medical_text(text: str) -> bool:  # 🔄 async
    """Безопасная проверка медицинского текста"""
    prompt = (
        "The following text was extracted from an image or document. "
        "Determine if it appears to be part of a medical document (e.g., lab report, diagnosis, discharge summary, prescriptions, imaging results).\n\n"
        "Respond strictly with 'yes' or 'no'.\n\n"
        f"{text[:1500]}"
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a medical classification assistant. Your task is to check if a text is medical in nature."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0
    )

    answer = response.choices[0].message.content.strip().lower()
    return "yes" in answer

@async_safe_openai_call(max_retries=2, delay=1.0)
async def generate_medical_summary(text: str, lang: str, document_date: str = None) -> str:
    """Саммари которое идет в векторы"""
    
    # Получаем текущую дату для fallback
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    # Если дата документа не передана, используем текущую
    fallback_date = document_date or current_date
    
    system_prompt = (
        "You are a medical assistant creating a structured summary of a medical document. "
        "You do not draw conclusions or add comments. You simply organize important information into paragraphs."
        f"⚠️ Always respond strictly in the '{lang}' language, regardless of the document language."
    )

    user_prompt = (
        "⚠️ STRICT INSTRUCTION:\n"
        "⚠️ Never include any personal or identifying information — such as full names, age, gender, addresses, card numbers, clinic names, or hospital departments. Completely remove such data from the summary, even if it appears in the document. Do not begin the paragraph with phrases like 'the patient is a 67-year-old male'.\n"
        
        f"⚠️ DATE RULES:\n"
        f"1. FIRST: Look for dates in the document text (DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY formats)\n"
        f"2. SECOND: If NO date found in document, use this fallback date: {fallback_date}\n"
        f"3. CRITICAL: Use the SAME date for ALL paragraphs - either the document date OR the fallback date\n"
        f"4. Each paragraph must start with [dd.mm.yyyy] format\n"
        f"5. Do not mix different dates between paragraphs\n"
        f"6. Do not repeat dates inside paragraphs\n\n"
        
        "⚠️ Include only content that may be clinically relevant or useful for AI-driven medical analysis. Do not include paragraphs that contain only formal phrases, disclaimers, missing data notes, or administrative remarks without medical value.\n"
        "Create a structured summary of a medical document.\n"
        "It can be any type of document: report, discharge summary, examination protocol, consultation, lab result, etc.\n"
        "Divide the text into paragraphs by meaning and size — from 100 to 150 words. If a paragraph is too short, merge it with a neighboring one.\n"
        "The first paragraph is the main one: include all key and diagnostically important information from the entire document.\n"
        "The first paragraph must contain all critical clinical data, diagnoses, and observations, even if they are repeated elsewhere in the document.\n"
        "Strive for logically complete fragments; do not break sentences or leave incomplete thoughts.\n"
        
        f"⚠️ CRITICAL: Extract date from document first. If no date found, use {fallback_date}.\n"
        
        "Always preserve all parameters, even if they are contradictory or incomplete.\n"
        "Do not interpret, do not draw conclusions, do not omit ambiguous or conflicting data — just keep them as they are.\n"
        "Include all numerical values, reference ranges, signs, diagnoses, scales, dosages, medications, test result descriptions, and technical parameters.\n"
        "Do not add any introductory or concluding sentences.\n"
        "If there is little information, do not create extra paragraphs — limit to 1–2 chunks.\n"
        "This summary is intended for internal AI analysis.\n"
        
        "FORMAT: [DD.MM.YYYY] Medical content of paragraph.\n"
        
        "Before returning the answer, verify that:\n"
        "- No full names are present\n" 
        f"- Each paragraph starts with either document date OR {fallback_date}\n"
        "- No other dates are mentioned inside paragraphs\n"
        "- All text is logically grouped and follows the format\n"
        "The answer must be in the form of such paragraphs, separated by double line breaks.\n\n" + text
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1500,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=1.0)
async def generate_title_from_text(text: str, lang: str) -> str:  # 🔄 async
    """Безопасное создание заголовка из текста"""
    # 🌍 УСИЛЕННЫЕ ЯЗЫКОВЫЕ ИНСТРУКЦИИ
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian',
        'en': 'English',
        'de': 'German'
    }
    
    target_language = lang_names.get(lang, 'Russian')
    system_prompt = (
        "You are a medical assistant generating concise titles for documents. "
        f"⚠️ CRITICAL: You MUST respond ONLY in {target_language} language. "
        f"⚠️ The entire title must be in {target_language}. "
        f"⚠️ DO NOT mix languages - use ONLY {target_language}. "
    )
    
    title_prompt = (
        "Read the medical document and generate a short, accurate title.\n"
        "⚠️ Never include full names of patients, doctors, lab staff, or clinics — completely skip them.\n"
        
        "📅 DATE RULES:\n"
        "• ONLY if the document text contains a real date (DD.MM.YYYY, DD/MM/YYYY, etc.) - add it to the title\n"
        "• If NO date is found in the document - do NOT add any date to the title\n"
        "• NEVER use example dates or make up dates\n\n"
        
        "🧾 Focus only on the essence: type of exam, organ, diagnosis, etc. No extra words, no quotes, no formal phrases.\n"
        
        "EXAMPLES:\n"
        "• If document contains date '15.06.2023': → 'Liver ultrasound 15.06.2023'\n"
        "• If document contains NO date: → 'Blood test'\n"
        "• If document contains NO date: → 'Lumbar spine MRI'\n\n"
        
        "DOCUMENT TEXT TO ANALYZE:\n"
        f"{text[:1500]}"
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{title_prompt}\n\n{text}"}
        ],
        max_tokens=100,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=2.0)
async def generate_health_analysis(user_data: dict, lang: str = "ru") -> str:
    """
    Генерация персонального анализа здоровья через GPT-5
    
    Args:
        user_data: Словарь с данными пользователя из БД
        lang: Язык ответа ('ru', 'uk', 'en')
    
    Returns:
        str: Персональный анализ здоровья
    """
    
    # Вычисляем возраст и BMI
    age = "not specified"
    if user_data.get('birth_year'):
        age = datetime.now().year - user_data['birth_year']
    
    bmi = "not calculated"
    bmi_category = "not determined"
    if user_data.get('height_cm') and user_data.get('weight_kg'):
        height_m = user_data['height_cm'] / 100
        bmi_value = user_data['weight_kg'] / (height_m ** 2)
        bmi = round(bmi_value, 1)
        
        if bmi_value < 18.5:
            bmi_category = "underweight"
        elif bmi_value < 25:
            bmi_category = "normal weight"
        elif bmi_value < 30:
            bmi_category = "overweight"
        else:
            bmi_category = "obesity"
    
    # Собираем данные для промта (всё на английском, убрали medications)
    profile_summary = f"""
Age: {age} years
Gender: {user_data.get('gender', 'not specified')}
Height: {user_data.get('height_cm', 'not specified')} cm
Weight: {user_data.get('weight_kg', 'not specified')} kg
BMI: {bmi} ({bmi_category})
Chronic conditions: {user_data.get('chronic_conditions') or 'none reported'}
Allergies: {user_data.get('allergies') or 'none reported'}
Smoking: {user_data.get('smoking', 'not specified')}
Alcohol: {user_data.get('alcohol', 'not specified')}
Physical activity: {user_data.get('physical_activity', 'not specified')}
Family history: {user_data.get('family_history') or 'none reported'}
""".strip()
    
    # Улучшенный клинически точный и мотивирующий промт
    prompt = f"""You are a virtual physician. Respond in {lang} language.
Create a comprehensive, actionable, and personalized health analysis from the profile below.
Only use provided data; if a field is "not specified" - don't invent details.

PATIENT PROFILE:
{profile_summary}

REQUIRED OUTPUT STRUCTURE:
1) **Personal Health Snapshot** (2-3 sentences acknowledging their proactive approach)

2) **Key Priority Areas** (2-4 specific areas based on their actual data)
   - Connect each priority directly to their age, BMI, conditions, family history
   - Frame as optimization opportunities, not just risks

3) **Your Personal Metrics & Smart Goals** 
   - Calculate and show BMI category with target range if height/weight provided
   - Set SMART goals with specific numbers and timelines (e.g., "lose 3-4kg in 12 weeks")
   - Include activity targets in minutes/week based on current level

4) **Strategic Monitoring Plan**
   - Specific tests/screenings aligned to their profile with exact timing
   - If chronic conditions mentioned → relevant monitoring (HbA1c, etc.)
   - Age-appropriate screenings for their gender

5) **Daily Action Steps** (4-5 micro-behaviors they can start immediately)
   - Tie each recommendation directly to their specific conditions/risk factors
   - Make them small, specific, and achievable
   - Include meal timing, movement triggers, measurement habits

6) **90-Day Transformation Roadmap**
   - Week 1-2: Foundation (specific initial actions and baseline measurements)
   - Week 3-6: Building momentum (progressive goals and specialist consultations)  
   - Week 7-12: Optimization (advanced strategies and progress evaluation)
   - Include measurable milestones for each phase

7) **Your Health Companion Next Steps**
   - Show how the bot helps maintain medical records and understand health data
   - Encourage uploading medical documents for personalized analysis and explanations
   - Mention the bot's ability to help interpret test results and medical reports
   - Emphasize ongoing health guidance and answering specific health questions

WRITING STYLE:
- Use encouraging, confidence-building language
- Include specific numbers, timelines, and measurable outcomes
- Show clear connection between actions and expected improvements
- Make it feel like a premium personalized health optimization plan
- Prioritize actionable content over general advice
- Keep medical accuracy while being motivating

TECHNICAL PARAMETERS:
- Temperature: 0.4 for more consistent structure
- Focus on provided data only
- If key data missing, briefly mention what would enhance the analysis"""

    # Вызов GPT-5 с правильными параметрами
    response = await client.chat.completions.create(
        model="gpt-5-chat-latest",  # ✅ Правильное название модели GPT-5
        messages=[
            {
                "role": "system",
                "content": f"You are an experienced virtual physician providing comprehensive health consultations. Always respond in {lang} language. Be thorough, professional, and encouraging."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1300,  # Увеличенный лимит для полного анализа
        temperature=0.4   # Более детерминированный вывод для стабильной структуры
    )
    
    analysis = response.choices[0].message.content.strip()
    
    # Безопасное логирование
    logger.info(f"Health analysis generated using GPT-5 for user profile")
    
    return safe_telegram_text(analysis)

# FALLBACK ФУНКЦИИ остаются синхронными
def fallback_summarize(text: str, lang: str = "ru") -> str:
    """Простое резюме без ИИ если OpenAI недоступен"""
    today_str = datetime.now().strftime("%d.%m.%Y")
    words = text.split()
    if len(words) > 100:
        summary = " ".join(words[:100]) + "..."
    else:
        summary = text
    return f"[{today_str}] {summary}"

async def check_openai_status() -> bool:  # 🔄 async
    """Асинхронная проверка доступности OpenAI API"""
    try:
        response = await client.chat.completions.create(  # 🔄 await
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )
        return True
    except Exception:
        return False