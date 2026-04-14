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

def async_safe_openai_call(max_retries: int = 3, delay: float = 2.0, timeout: float = 90.0):
    """Асинхронный декоратор для безопасных вызовов OpenAI API"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            
            async with OPENAI_SEMAPHORE:
                for attempt in range(max_retries):
                    try:
                        return await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout
                        )
                        
                    except asyncio.TimeoutError:
                        last_error = Exception(f"OpenAI timeout after {timeout}s")
                        logger.warning(f"OpenAI timeout on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay * (attempt + 1))
                        
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
async def ask_structured(text: str = "", lang: str = "ru", max_tokens: int = 2500, 
                        assistant_analysis: str = "", specialist_analysis: str = "",
                        patient_context: str = "") -> str:
    """
    Создание клинической сводки для пользователя на основе анализов ассистента и специалиста
    
    Args:
        text: Полный анализ (legacy fallback)
        lang: Язык ответа
        max_tokens: Максимум токенов для ответа
        assistant_analysis: Анализ от ассистента
        specialist_analysis: Анализ от специалиста
    """
    
    # ✅ Fallback для обратной совместимости
    if not assistant_analysis and not specialist_analysis and text:
        specialist_analysis = text
    
    # ✅ Маппинг языка
    lang_map = {
        "ru": "Russian",
        "uk": "Ukrainian",
        "en": "English",
        "de": "German"
    }
    response_language = lang_map.get(lang, "Russian")
    
    system_prompt = f"""ROLE:
You are a clinical interpretation system for medical documents.

Your task is to synthesize the assistant’s and physician’s analyses
into a single, clear, and calm summary
for a person without medical education,
while strictly preserving the accuracy of the clinical meaning.

The summary must provide a clear answer, not just describe the data.

Write as a physician explaining findings to a patient: calm, direct, and in accessible language, without unnecessary jargon or alarmist wording, while preserving clinical accuracy.
The text does not constitute an official medical conclusion.

---

DATA SOURCES:

You have TWO analytical texts:
— an analytical text from the Assistant
— an analytical text from the Physician (Expert)

Assistant:
• performs structured data analysis
• identifies key patterns, deviations, and relationships

Physician (Expert):
• validates the assistant’s conclusions
• refines the clinical interpretation
• builds a hierarchy of scenarios and clinical context

When forming the summary:
— rely on both sources
— in case of discrepancies, prioritize the physician’s logic and conclusions
— the final text must be cohesive and must not be divided by roles

---

PATIENT CONTEXT:
If patient context is provided, take it into account when forming the summary.
Reflect it where clinically relevant — do not ignore it.

---

BOUNDARIES:

✔️ Allowed:
— State the most probable clinical explanation (non-final, probabilistic)
— Name conditions if clearly supported by the data
— Describe clinical relevance and possible implications in neutral terms

❌ Forbidden:
— Definitive diagnosis or official medical conclusion
— Treatment, recommendations, or advice
— Addressing the user directly or using imperative language
— Alarmist or emotionally charged wording
— Mentioning or implying alternative scenarios
  unless they are clearly dominant in the physician analysis
— Escalating to critical or oncological framing
  when findings are within reference ranges or lack supporting data

---

DATA LIMITATIONS:
- Use only the provided analytical texts.
- Do not add new medical facts or assumptions not present in the input data.

---

SUMMARY STRUCTURE (MANDATORY):

1. DOCUMENT OVERVIEW

Essence:
Clearly and directly describe
the medical situation reflected in the document.

Format:
2–4 sentences.
No academic language or abstractions.

Requirement:
This section must explicitly state
the SINGLE most probable clinical explanation
(in a probabilistic, non-final form).

If the findings are within reference ranges
and no pathological pattern is identified,
the explanation should be framed as a normal or baseline finding,
without escalation or risk-focused language.

---

2. KEY FINDINGS AND OBSERVATIONS

Essence:
List the key facts
that form the basis of the conclusion.

Format:
Bullet points.
From most significant to secondary.

---

3. INTERPRETATION OF THE FINDINGS

Essence:
Explain how such a pattern
is usually interpreted in clinical practice.

Mandatory:
— describe the SINGLE leading clinical scenario only
— focus on explanatory logic of this scenario
— use neutral, probabilistic explanatory wording
— DO NOT mention, compare, imply, or contrast alternative interpretations
  or less probable scenarios in this section,
  explicitly or implicitly

---

4. WHY THIS MATTERS

Essence:
Explain why this situation is important from a medical perspective.
Focus on why this finding is clinically relevant for understanding the overall situation — not on repeating what was already described.
Anchor the explanation to the main clinical scenario.

Allowed:
— to discuss metabolic, functional, or systemic relevance
— to describe possible implications directly related to the identified pattern,
  proportional to the actual findings

If the findings are within normal limits:
— emphasize the absence of clinically significant abnormalities
— avoid discussion of rare, theoretical, or false-negative scenarios

Forbidden:
— to predict progression over time
— to use words such as “dangerous”, “critical”, “urgent”
— to speculate beyond the presented data

---

5. LIMITATIONS AND UNCERTAINTIES

— List 2–4 key limitations only (1 line each)
— Include only factors that meaningfully affect interpretation
— Group related missing data (e.g., “no clinical context”)
— Avoid minor or redundant details

Add one final sentence stating impact on certainty
(e.g., low / moderate / significant impact).

---

6. FOLLOW-UP CONTEXT

Essence:
Provide a neutral, non-directive orientation
on how such findings are typically approached in clinical practice.
Anchor the explanation to the identified clinical scenario.

Purpose:
— reduce uncertainty
— define the general time horizon
— clearly indicate whether the situation appears non-urgent or requires medical attention

Allowed:
— describe typical follow-up logic in general terms
— indicate when findings are usually reassessed in dynamics
— explicitly state if the current pattern does NOT indicate an acute or critical process

Forbidden:
— prescriptions, treatment, supplementation, or lifestyle advice
— imperative or directive language
— addressing the user directly
— introducing new medical facts not present in the input data

Format:
2–4 concise paragraphs or bullet points.

---

STYLE AND TONE:

— Professional, calm, and direct
— No moralizing or excessive detail
— The text should feel like
  an honest physician’s summary
  that provides clarity and psychological safety
  proportional to the findings

IMPORTANT:
You MUST respond in {response_language} language.
All section titles and headings MUST be written
in the same language as the response.
"""
    context_block = f"\n\nPatient Context:\n{patient_context.strip()}" if patient_context and patient_context.strip() else ""

    user_prompt = f"""Assistant's analytical text:
{assistant_analysis}

Physician (Expert)'s analytical text:
{specialist_analysis}{context_block}

Create a clinical summary following the structure defined in the system prompt."""

    # ✅ Используем старый формат input (склеиваем system и user)
    full_input = f"{system_prompt}\n\n{user_prompt}"
    
    response = await client.responses.create(
        model="gpt-5.2",
        input=full_input,
        max_output_tokens=max_tokens
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
        – in **English only**, ALWAYS in ENGLISH, NEVER translate to Russian/Ukrainian/German
        – **comma-separated**, with no explanations.

        ⚠️ CRITICAL: Return keywords in ENGLISH ONLY, regardless of input language!

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
    Главный промт ответов в чате (исправленная версия с roles)
    """
    
    # ✅ АНАЛИЗИРУЕМ НЕДАВНЮЮ ИСТОРИЮ
    recent_interaction = bool(context_text and context_text.strip())

    # ✅ ОПРЕДЕЛЯЕМ ТИП ОБЩЕНИЯ
    greeting_words = ['привет', 'здравствуй', 'добро пожаловать', 'hello', 'hi', 'вітаю', 'добрий день']
    is_greeting = any(word in user_question.lower() for word in greeting_words)

    # 🔧 ЯЗЫК
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

    # 🧠 БАЗОВЫЙ SYSTEM PROMPT
    base_system_prompt = (
        "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
        "You speak in a friendly, human tone and provide explanations when needed. "
        f"Always respond in the '{lang}' language.\n\n"
        f"{lang_instruction}"
    )

    # 🧠 ВЫБОР МОДЕЛИ
    if use_gemini:
        model = "gpt-5.2"

        system_prompt = f"""
{base_system_prompt}

🧠 ADVANCED MEDICAL CAPABILITIES (MANDATORY):
- Perform deep clinical reasoning
- Interpret lab values and patterns
- Use evidence-based medicine (NICE, ADA, ESC, WHO)
- Separate observations vs interpretations
- Provide personalized risk assessment
"""

    else:
        model = "gpt-4o-mini"
        system_prompt = base_system_prompt

    # 🧾 ИНСТРУКЦИИ
    if recent_interaction and not is_greeting:
        instruction_prompt = """
🚨 You are a MEDICAL assistant ONLY.

✅ ANSWER: symptoms, diagnostics, lab results, imaging, medications, treatment.
❌ DECLINE: non-medical questions.

- Use medical documents as clinical findings
- Do NOT say you can't see images
- Do NOT repeat you're an AI
- Ask follow-up questions ONLY if critical
- If data is missing — give preliminary guidance

⚠️ Continue conversation WITHOUT greeting
"""
    else:
        instruction_prompt = """
🚨 You are a MEDICAL assistant ONLY.

✅ ANSWER: symptoms, diagnostics, lab results, imaging, medications, treatment.
❌ DECLINE: non-medical questions.

- Use medical documents as clinical findings
- Do NOT say you can't see images
- Do NOT repeat you're an AI
- Ask follow-up questions ONLY if critical
- If data is missing — give preliminary guidance
"""

    enhanced_system_prompt = f"{system_prompt}\n\n{instruction_prompt}"

    # 📦 СТРУКТУРА СООБЩЕНИЙ
    messages = [
        {
            "role": "system",
            "content": enhanced_system_prompt
        }
    ]

    # добавляем контекст, если есть
    if context_text and context_text.strip():
        messages.append({
            "role": "user",
            "content": f"Patient medical context:\n{context_text}"
        })

    # вопрос
    messages.append({
        "role": "user",
        "content": f"Patient's question: {user_question}"
    })

    # 🚀 ВЫЗОВ API
    try:
        if model == "gpt-5.2":
            response = await client.responses.create(
                model=model,
                input=messages,
                max_output_tokens=3000
            )
            answer = (response.output_text or "").strip()

        else:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2500,
                temperature=0.5,
            )
            answer = response.choices[0].message.content.strip()

        return safe_telegram_text(answer)

    except Exception as e:
        logger.error(f"❌ Ошибка модели {model}: {str(e)}")

        # 🔁 fallback
        try:
            logger.warning("⚠️ Fallback на GPT-4o-mini")

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2500,
                temperature=0.5,
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
        "You are a medical text reduction engine for semantic vector embedding. "
        "This is NOT summarization. This is FACT REDUCTION.\n\n"

        "Your task is to REMOVE all non-factual content from the provided medical text "
        "and rewrite the remaining factual statements into ONE compact paragraph.\n\n"

        "A factual statement is ONLY one of the following:\n"
        "- A measured medical parameter with its value and unit\n"
        "- A documented presence or absence of a finding\n"
        "- A clearly stated test result as written in the text\n"
        "- A directly stated limitation or missing data\n\n"

        "You must DELETE, not reinterpret.\n"
        "You must NOT explain, infer, classify, or reason.\n"
        "Loss of information due to deletion is expected and correct behavior.\n\n"

        "STRICTLY FORBIDDEN:\n"
        "- Diagnoses or diagnostic labels\n"
        "- Probabilities, likelihoods, or assumptions\n"
        "- Risk descriptions or stratification\n"
        "- Reference values, physiological norms, or background medical knowledge\n"
        "- Recommendations, actions, or next steps\n\n"

        f"⚠️ Always respond strictly in the '{lang}' language, regardless of the document language."
    )

    user_prompt = (
        "⚠️ CRITICAL TASK:\n"
        "Rewrite the provided medical text by REMOVING all non-factual statements.\n"
        "This is NOT interpretation and NOT summarization.\n\n"

        "⚠️ OUTPUT RULES (NON-NEGOTIABLE):\n"
        "- Produce EXACTLY ONE paragraph\n"
        "- Do NOT use line breaks\n"
        "- Do NOT use lists, headings, or formatting\n\n"

        "⚠️ PRIVACY RULE:\n"
        "Remove any personal or identifying information, including names, age, gender, "
        "addresses, IDs, clinic or hospital names, departments, or doctors.\n\n"

        "⚠️ DATE RULES:\n"
        f"- Start the paragraph with [{fallback_date}] exactly once\n"
        "- Do NOT mention any other dates\n\n"

        "⚠️ KEEP ONLY THESE TYPES OF CONTENT:\n"
        "- Medical parameters with values and units\n"
        "- Presence or absence of findings (e.g., detected / not detected)\n"
        "- Test results as explicitly written\n"
        "- Explicitly stated missing or unavailable data\n\n"

        "⚠️ DELETE IMMEDIATELY IF PRESENT:\n"
        "- Diagnoses (e.g., disease names, syndromes)\n"
        "- Words indicating interpretation or causality\n"
        "- Probability or risk language\n"
        "- Reference ranges or physiological explanations\n"
        "- Clinical conclusions or recommendations\n\n"

        "⚠️ IMPORTANT:\n"
        "If deleting non-factual content significantly shortens the text, this is correct.\n"
        "Do NOT compensate by adding explanations or inferred facts.\n\n"

        "⚠️ FORMAT (MANDATORY):\n"
        f"[{fallback_date}] <single continuous paragraph of factual statements only>\n\n"

        "FINAL CHECK BEFORE ANSWER:\n"
        "- Exactly one paragraph\n"
        "- Starts with the date\n"
        "- Contains ONLY factual medical statements\n"
        "- Contains NO diagnoses, risks, assumptions, or recommendations\n\n"

        + text
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=350,
        temperature=0.2
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
        "Your titles must identify ONLY the type of document and anatomical region. "
        "⚠️ DO NOT include dates, patient names, or medical interpretations. "
        f"⚠️ CRITICAL: You MUST respond ONLY in {target_language} language. "
        f"⚠️ The entire title must be in {target_language}. "
    )
    
    title_prompt = (
        "Read the medical document and generate a short, accurate title.\n"
        "⚠️ NEVER include dates (even if found in the text).\n"
        "⚠️ NEVER include personal names, clinic names, or specific diagnoses.\n\n"
        
        "🧾 FOCUS:\n"
        "Combine the document type with the body part or system (e.g., 'MRI of the brain', 'Complete blood count').\n"
        "Keep it under 5-7 words.\n\n"

        "EXAMPLES:\n" 
        "• Input: MRI of the head, dated 2025-10-12, patient Smith -> 'Brain MRI'\n"
        "• Input: Blood test results for John Doe, showing high glucose -> 'Complete blood count'\n"
        "• Input: Heart ultrasound (Echo) showing valve issues -> 'Echocardiography (Echo)'\n"
        "• Input: Gastroscopy report mentioning acute gastritis -> 'Gastroscopy (EGD)'\n\n"               
        
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