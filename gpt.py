# gpt.py - МОДИФИЦИРОВАННАЯ ВЕРСИЯ с асинхронными функциями
# Все названия функций остаются теми же, просто добавляем async/await

import os
import base64
import asyncio
from openai import AsyncOpenAI  # 🔄 ИЗМЕНЕНИЕ: AsyncOpenAI вместо OpenAI
from datetime import datetime
from dotenv import load_dotenv
from error_handler import safe_openai_call, OpenAIError, log_error_with_context, FileProcessingError

load_dotenv()

# 🔄 ИЗМЕНЕНИЕ: AsyncOpenAI клиент
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📊 Семафор для ограничения одновременных запросов
OPENAI_SEMAPHORE = asyncio.Semaphore(5)

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

@async_safe_openai_call(max_retries=3, delay=2.0)
async def ask_gpt(user_prompt: str) -> str:  # 🔄 Просто добавили async
    """Безопасный вызов GPT с обработкой ошибок"""
    response = await client.chat.completions.create(  # 🔄 Добавили await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "Ты — вежливый и внимательный ИИ-врач, который ведёт пациента в течение длительного времени. "
                "У тебя есть доступ к истории общения, медицинским документам и пользовательским записям. "
                "Если пациент просит что-то запомнить — считается, что информация сохранена, даже если это делает другая система. "
                "Отвечай подробно, с объяснениями, избегай сухих фраз. Будь доброжелательным, неформальным и понятным."
            )},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1500,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

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
async def send_to_gpt_vision(image_path: str, lang: str, prompt: str = None):  # 🔄 async
    """Безопасный анализ медицинского снимка"""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except FileNotFoundError:
        raise FileProcessingError(f"Файл {image_path} не найден", "Файл не найден для обработки")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = (
        "You are a senior radiologist with 15+ years of experience in interpreting all types of medical imaging — "
        "including X-rays, MRI, CT, ultrasound, endoscopic photos, dermatological photos, and wound images.\n\n"
        "Your task:\n"
        "1. Analyze the medical image carefully and describe all relevant visual findings.\n"
        "2. Use proper clinical terminology: anatomy, annotations, abnormalities.\n"
        "3. DO NOT provide diagnosis or treatment suggestions.\n"
        "4. If the image is NOT medical or is unreadable — say this clearly and directly.\n"
        f"⚠️ ALWAYS respond strictly in the '{lang}' language, regardless of the input or image content."
    )

    user_prompt = prompt or (
        "Please analyze this medical image and describe all visible clinical features: structures, measurements, anomalies, and technical notes. "
        "If the image is not medical, say so directly."
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
        temperature=0.4
    )
    return response.choices[0].message.content.strip(), ""

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
async def ask_structured(text: str, lang: str = "ru", max_tokens: int = 1200) -> str:  # 🔄 async
    """Безопасное создание структурированного ответа"""
    system_prompt = (
        "You are a medical assistant helping the patient understand the content of a medical document. "
        "You must convey all medical facts accurately, preserving all clinical values, terminology, and findings. "
        f"⚠️ Always respond strictly in the '{lang}' language, regardless of the input language."
    )

    user_prompt = (
        "⚠️ STRICT INSTRUCTIONS:\n"
        "Read the medical document and create a concise and clear summary that a patient can understand.\n\n"
        
        "• Preserve all clinically important information: document date, lab values, diagnoses, findings, procedures, medications, dosages, medical terms, scales, parameters, anomalies, and names of tests or exams.\n"
        "• Do NOT add your own interpretations or conclusions. Do NOT summarize beyond what is in the document.\n"
        "• Remove all personal data: full names, age, gender, addresses, clinic names, doctor names.\n"
        "• If the document includes structured data (e.g. lab results), present them as lists or clearly formatted sections.\n"
        "• Otherwise, write in logical paragraphs, grouped by meaning.\n"
        "• Avoid phrases like «the patient was advised» or «the patient came in with...» — focus on the document content itself.\n"
        "• Your goal is to preserve clarity and structure, as if a doctor were explaining the document to a patient, without simplifications.\n\n"
        
        f"{text}"
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

@async_safe_openai_call(max_retries=2, delay=1.0)
async def enrich_query_for_vector_search(user_question: str) -> str:  # 🔄 async
    """Безопасное улучшение запроса для векторного поиска"""
    prompt = f"""
    Пользователь задал вопрос: "{user_question}"

    Переформулируй его как расширенный медицинский запрос, чтобы лучше найти нужную информацию в медицинских записях.
    Сделай его точным, но не меняй суть. Добавь термины: вид обследования, параметры, диагноз, части тела, симптомы — если они логично подразумеваются.

    Примеры:
    - "что по узи?" → "Результаты последнего УЗИ с описанием положения плода, параметров головы, срока беременности"
    - "анализы крови?" → "Расшифровка последнего анализа крови: гемоглобин, лейкоциты, СОЭ, глюкоза"
    - "что с почками?" → "Данные по почкам из анализов мочи и УЗИ: размеры, структура, эхогенность, отклонения"

    Ответ:
    """
    return await ask_gpt(prompt.strip())  # 🔄 await

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
async def extract_keywords(text: str) -> list[str]:  # 🔄 async
    """Безопасное извлечение ключевых слов из текста"""
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
        raw = await ask_gpt_keywords(prompt)  # 🔄 await
        print("\n[🔎 GPT raw keywords]:")
        print(raw)
        return [w.strip().lower() for w in raw.split(",") if len(w.strip()) > 1]
    except Exception as e:
        log_error_with_context(e, {"function": "extract_keywords", "text_length": len(text)})
        return []

@async_safe_openai_call(max_retries=3, delay=2.0)
async def ask_doctor(profile_text: str, summary_text: str, last_summary: str, 
               chunks_text: str, context_text: str, user_question: str, lang: str) -> str:  # 🔄 async
    """Безопасный вызов доктора-ассистента"""
    system_prompt = (
        "You are a compassionate and knowledgeable virtual physician who guides the user through their medical journey. "
        "You speak in a friendly, human tone and provide explanations when needed. "
        f"Always respond in the '{lang}' language."
    )

    instruction_prompt = (
        "You have access to the user's health profile, medical documents, imaging reports, conversation history, and memory notes. "
        "Answer only questions related to the user's health — symptoms, diagnostics, treatment, risks, interpretation of reports, etc. "
        "If the question is not directly related to medical symptoms, diagnostics, treatment, or documented findings — but still relevant to health (e.g., vitamins, lifestyle, prevention) — you may give helpful information."
        "Only decline if the question is clearly off-topic (e.g., movies, politics).\n"
        "Do not repeat that you're an AI. Do not ask follow-up questions unless critical.\n"
        "Use the document summaries and analysis results as clinical findings. Do not say you can't see images.\n"
        "If information is missing, offer a preliminary suggestion and explain what's lacking."
    )

    context_block = (
        f"📌 Patient profile:\n{profile_text}\n\n"
        f"🧠 Conversation summary:\n{summary_text}\n\n"
        f"📄 Recent document interpretations:\n{last_summary}\n\n"
        f"🔎 Related historical data:\n{chunks_text}\n\n"
        f"💬 Recent messages:\n{context_text}\n\n"
    )

    full_prompt = f"{instruction_prompt}\n\n{context_block}\n\nPatient: {user_question}"

    print("\n=== SYSTEM PROMPT ===\n")
    print(system_prompt)
    print("\n=== USER PROMPT ===\n")
    print(full_prompt)
    print("\n=====================\n")

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=1500,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

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
async def generate_medical_summary(text: str, lang: str) -> str:  # 🔄 async
    """Безопасное создание медицинского резюме"""
    system_prompt = (
        "You are a medical assistant creating a structured summary of a medical document. "
        "You do not draw conclusions or add comments. You simply organize important information into paragraphs."
        f"⚠️ Always respond strictly in the '{lang}' language, regardless of the document language."
    )

    user_prompt = (
        "⚠️ STRICT INSTRUCTION:\n"
        "⚠️ Never include any personal or identifying information — such as full names, age, gender, addresses, card numbers, clinic names, or hospital departments. Completely remove such data from the summary, even if it appears in the document. Do not begin the paragraph with phrases like 'the patient is a 67-year-old male'.\n"
        "The date must be on the first line of the paragraph and part of the sentence — not on a separate line. Do not repeat this date later in the paragraph. Do not include any other dates inside the paragraph.\n"
        "⚠️ Include only content that may be clinically relevant or useful for AI-driven medical analysis. Do not include paragraphs that contain only formal phrases, disclaimers, missing data notes, or administrative remarks without medical value.\n"
        "Create a structured summary of a medical document.\n"
        "It can be any type of document: report, discharge summary, examination protocol, consultation, lab result, etc.\n"
        "Divide the text into paragraphs by meaning and size — from 100 to 150 words. If a paragraph is too short, merge it with a neighboring one.\n"
        "The first paragraph is the main one: include all key and diagnostically important information from the entire document.\n"
        "The first paragraph must contain all critical clinical data, diagnoses, and observations, even if they are repeated elsewhere in the document.\n"
        "Strive for logically complete fragments; do not break sentences or leave incomplete thoughts.\n"
        "If a date is provided in the document — begin each paragraph with it in the format [dd.mm.yyyy]. If no date is given — use the current date.\n"
        "Always preserve all parameters, even if they are contradictory or incomplete.\n"
        "Do not interpret, do not draw conclusions, do not omit ambiguous or conflicting data — just keep them as they are.\n"
        "Include all numerical values, reference ranges, signs, diagnoses, scales, dosages, medications, test result descriptions, and technical parameters.\n"
        "Do not add any introductory or concluding sentences.\n"
        "If there is little information, do not create extra paragraphs — limit to 1–2 chunks.\n"
        "This summary is intended for internal AI analysis.\n"
        "Example paragraph: [01.03.2024] Liver ultrasound: diffuse changes in the parenchyma, 8 mm hyperechoic inclusion found.\n"
        "Before returning the answer, verify that:\n"
        "- No full names are present\n" 
        "- Each paragraph starts with ONE date only\n"
        "- No other dates are mentioned inside paragraphs\n"
        "- All text is logically grouped and follows the format\n"
        "The answer must be in the form of such paragraphs, separated by double line breaks.\n\n" + text
    )

    response = await client.chat.completions.create(  # 🔄 await
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1200,
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
        "📅 If the document contains a date, add it to the title in the format DD.MM.YYYY.\n"
        "🧾 Focus only on the essence: type of exam, organ, diagnosis, etc. No extra words, no quotes, no formal phrases.\n"
        "Examples:\n"
        "- Liver ultrasound 05.03.2024\n"
        "- Blood test 21.02.2023\n"
        "- Lumbar spine MRI\n\n"
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

def fallback_response(user_question: str, lang: str = "ru") -> str:
    """Простой ответ если OpenAI недоступен"""
    messages = {
        "ru": "🤖 ИИ-ассистент временно недоступен. Ваш вопрос сохранен, я отвечу как только сервис восстановится.",
        "en": "🤖 AI assistant is temporarily unavailable. Your question is saved, I'll respond once the service is restored.",
        "uk": "🤖 ШІ-асистент тимчасово недоступний. Ваше питання збережено, я відповім щойно сервіс відновиться."
    }
    return messages.get(lang, messages["ru"])

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