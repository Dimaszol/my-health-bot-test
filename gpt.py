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
        "en": "Respond in English language."
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
async def update_medications_via_gpt(user_input: str, current_list: list) -> list:  # 🔄 async
    """Безопасное обновление списка лекарств"""
    prompt = (
        "Ты — медицинский ассистент. У пользователя есть список принимаемых лекарств в формате JSON, "
        "и он вводит изменения обычным языком: добавь, удали, измени время. "
        "Верни обновлённый список в формате JSON со следующими полями:\n"
        "- name (название лекарства)\n"
        "- time (время в формате HH:MM)\n"
        "- label (оригинальная фраза времени, как пользователь написал)\n\n"
        "Сопоставь фразы со временем приёма. Примеры:\n"
        "- утром → 08:00\n"
        "- днём → 13:00\n"
        "- вечером → 20:00\n"
        "- перед сном → 22:00\n"
        f"📋 Текущий список лекарств:\n{current_list}\n\n"
        f"📨 Ввод пользователя:\n{user_input}\n\n"
        "Верни обновлённый список как JSON-массив без комментариев и пояснений. "
        "Ответ должен начинаться и заканчиваться квадратными скобками, содержать объекты с ключами name, time, label. "
        "Если пользователь просит удалить все лекарства (например: «удали все», «больше не принимаю», «очистить список»), "
        "Пример правильного формата:\n\n"
        "[{\"name\": \"Анальгин\", \"time\": \"18:00\", \"label\": \"вечером\"}, {\"name\": \"Омепразол\", \"time\": \"22:00\", \"label\": \"перед сном\"}]"
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты — помощник, который обновляет список лекарств по описанию пользователя."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2
    )
    
    raw_text = response.choices[0].message.content.strip()
    print("\n[🧪 GPT ответ — update_medications_via_gpt]:")
    print(raw_text)

    import json
    try:
        return json.loads(raw_text)
    except Exception as e:
        print("❌ Ошибка парсинга JSON:", e)
        log_error_with_context(e, {"function": "update_medications_via_gpt", "raw_response": raw_text[:200]})
        return []

@async_safe_openai_call(max_retries=2, delay=1.0)
async def ask_structured(text: str, lang: str = "ru", max_tokens: int = 2500) -> str:  # 🔄 async
    """Создание красивого отображения медицинского документа для пользователя"""
    
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

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.2  # Низкая для консистентности форматирования
    )
    return response.choices[0].message.content.strip()

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
        
        print(f"   🔎 Ключевые слова: {keywords_list}")
        return keywords_list
        
    except Exception as e:
        print(f"   🔎 Ключевые слова: Ошибка - {e}")
        log_error_with_context(e, {"function": "extract_keywords", "text_length": len(text)})
        return []

@async_safe_openai_call(max_retries=3, delay=2.0)
async def ask_doctor(context_text: str, user_question: str, 
                    lang: str, user_id: int = None, use_gemini: bool = False) -> str:
    """
    ✅ УЛУЧШЕННАЯ версия — учитывает недавнее общение, не здоровается каждый раз
    Добавлена поддержка Gemini 2.5 Flash
    """
    
    # ✅ АНАЛИЗИРУЕМ НЕДАВНЮЮ ИСТОРИЮ
    recent_interaction = False
    if context_text and len(context_text.strip()) > 0:
        # Если есть недавние сообщения, значит общение продолжается
        recent_interaction = True
    
    # ✅ ОПРЕДЕЛЯЕМ ТИП ОБЩЕНИЯ
    greeting_words = ['привет', 'здравствуй', 'добро пожаловать', 'hello', 'hi', 'вітаю', 'добрий день']
    is_greeting = any(word in user_question.lower() for word in greeting_words)
    
    system_prompt = (
        "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
        "You speak in a friendly, human tone and provide explanations when needed. "
        f"Always respond in the '{lang}' language."
    )

    # ✅ ОБНОВЛЕННЫЕ ИНСТРУКЦИИ с учетом контекста общения
    if recent_interaction and not is_greeting:
        # Продолжаем разговор — НЕ здороваемся
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
        # Первое сообщение или явное приветствие — можно поздороваться
        instruction_prompt = (
            "You have access to the user's health profile, medical documents, imaging reports, conversation history, and memory notes. "
            "Answer only questions related to the user's health — symptoms, diagnostics, treatment, risks, interpretation of reports, etc. "
            "If the question is not directly related to medical symptoms, diagnostics, treatment, or documented findings — but still relevant to health (e.g., vitamins, lifestyle, prevention) — you may give helpful information. "
            "Only decline if the question is clearly off-topic (e.g., movies, politics). "
            "Do not repeat that you're an AI. Do not ask follow-up questions unless critical. "
            "Use the document summaries and analysis results as clinical findings. Do not say you can't see images. "
            "If information is missing, offer a preliminary suggestion and explain what's lacking."
        )

    full_prompt = f"{instruction_prompt}\n\n{context_text}"

    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Определяем какая модель будет использоваться
        model_info = "Gemini 2.5 Flash" if use_gemini else "GPT-4o/GPT-4o-mini"
        
        with open("prompts_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"🕐 {timestamp} | User {user_id} | {model_info}\n")
            f.write(f"🌐 Язык: {lang} | Взаимодействие: {'Продолжение' if recent_interaction and not is_greeting else 'Новое/Приветствие'}\n")
            f.write(f"❓ Вопрос: {user_question}\n")
            f.write(f"📊 Длина system: {len(system_prompt)} симв. | user: {len(full_prompt)} симв. | ~{(len(system_prompt) + len(full_prompt)) // 4} токенов\n")
            f.write(f"{'='*80}\n")
            f.write("🔧 SYSTEM PROMPT:\n")
            f.write(system_prompt)
            f.write("\n\n👤 USER PROMPT:\n")
            f.write(full_prompt)
            f.write(f"\n{'='*80}\n\n")
        
        print(f"💾 Промпт сохранен в prompts_log.txt (User {user_id})")
        
    except Exception as e:
        print(f"⚠️ Не удалось сохранить промпт в файл: {e}")

    # ✅ НОВАЯ ЛОГИКА: Gemini или GPT
    if use_gemini:
        # Проверяем лимиты перед вызовом
        if user_id and await check_gpt4o_limit(user_id):
            try:
                # Вызываем Gemini
                response = await ask_doctor_gemini(system_prompt, full_prompt, lang)
                
                # ✅ ВАЖНО: Тратим лимит после успешного ответа
                
                print(f"💎 Лимит потрачен для пользователя {user_id} (Gemini)")
                
                return response
                
            except Exception as e:
                logger.warning(f"⚠️ Gemini недоступен, fallback на GPT-4o-mini: {e}")
                # При ошибке Gemini переходим на GPT-4o-mini (без трат лимитов)
                print(f"🔄 Fallback на GPT-4o-mini для пользователя {user_id}")
        else:
            # Нет лимитов → используем GPT-4o-mini
            print(f"🆓 Нет лимитов, используем GPT-4o-mini для пользователя {user_id}")
    
    # ✅ ОРИГИНАЛЬНАЯ ЛОГИКА GPT (без изменений)
        
    interaction_type = "🔄 Продолжение" if recent_interaction and not is_greeting else "🆕 Новое/Приветствие"
    print(f"💬 {interaction_type} | Вопрос: '{user_question[:50]}{'...' if len(user_question) > 50 else ''}'")
    
    if not use_gemini and user_id and await check_gpt4o_limit(user_id):
        model = "gpt-4o"
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=2500,
                temperature=0.5
            )
            
            
            answer = response.choices[0].message.content.strip()
            return safe_telegram_text(answer)
            
        except Exception as e:
            logger.warning(f"⚠️ GPT-4o недоступен, fallback на mini: {e}")
            model = "gpt-4o-mini"
    else:
        model = "gpt-4o-mini"

    # ✅ Вызов API (GPT-4o-mini или fallback)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=2500,
        temperature=0.5
    )
    
    answer = response.choices[0].message.content.strip()
    return safe_telegram_text(answer)


async def ask_doctor_gemini(system_prompt: str, full_prompt: str, lang: str = "ru") -> str:
    """
    Отдельная функция для Gemini 2.5 Flash - С ЖЕСТКОЙ ФИКСАЦИЕЙ ЯЗЫКА
    """
    try:
        import google.generativeai as genai
        import os
        
        # Получаем API ключ из .env
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY не найден в .env")
        
        # Настраиваем Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 🔧 УСИЛЕННАЯ ЯЗЫКОВАЯ ФИКСАЦИЯ на основе переданного lang
        if lang == "ru":
            lang_instruction = "КРИТИЧЕСКИ ВАЖНО: Отвечай ТОЛЬКО на русском языке. Никогда не переключайся на украинский или английский."
        elif lang == "uk":
            lang_instruction = "КРИТИЧНО ВАЖЛИВО: Відповідай ТІЛЬКИ українською мовою. Ніколи не переключайся на російську чи англійську."
        elif lang == "en":
            lang_instruction = "CRITICAL: Respond ONLY in English. Never switch to Russian or Ukrainian."
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
        
        # 🔧 ДИАГНОСТИКА
        prompt_length = len(combined_prompt)
        estimated_tokens = prompt_length // 2
        print(f"📊 Gemini промпт: {prompt_length} символов ≈ {estimated_tokens} токенов (язык: {lang})")
        
        # Отправляем запрос
        response = model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2500,
                temperature=0.5,  # 🔧 Немного снижаем для более стабильного языка
                candidate_count=1
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        # Обработка ответа
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            
            # Диагностика finish_reason
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                print(f"🔍 Gemini finish_reason: {finish_reason}")
                
                if finish_reason == 2:
                    print("⚠️ Ответ заблокирован системой безопасности")
                elif finish_reason == 3:
                    print("⚠️ Ответ заблокирован из-за авторских прав")
                elif finish_reason == 4:
                    print("⚠️ Ответ заблокирован по другим причинам")
            
            if hasattr(candidate, 'content') and candidate.content.parts:
                answer = candidate.content.parts[0].text.strip()
                
                # 🔧 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ЯЗЫКА
                print(f"✅ Gemini ответ получен: {len(answer)} символов")
                
                # Проверяем первые 100 символов на соответствие языку
                answer_start = answer[:100].lower()
                if lang == "ru" and any(word in answer_start for word in ["що", "відповідь", "зверніться", "рекомендую"]):
                    print("⚠️ Gemini ответил на украинском вместо русского!")
                elif lang == "uk" and any(word in answer_start for word in ["что", "ответ", "обратитесь", "рекомендую"]):
                    print("⚠️ Gemini ответил на русском вместо украинского!")
                
                return safe_telegram_text(answer)
        
        raise Exception("Gemini не вернул валидный ответ")
        
    except Exception as e:
        print(f"❌ Ошибка Gemini: {e}")
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
    """Безопасное создание медицинского резюме с правильной датой"""
    
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
    system_prompt = (
        "You are a medical assistant generating concise titles for documents. "
        f"⚠️ Always reply strictly in the '{lang}' language."
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