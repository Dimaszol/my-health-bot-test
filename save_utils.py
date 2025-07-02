import openai
import asyncio
import base64
import mimetypes
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from db_postgresql import get_last_message_id, get_conversation_summary, get_messages_after, save_conversation_summary, get_user_medications_text, update_user_field, get_user_language

from gpt import client, OPENAI_SEMAPHORE
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
# Семафор для ограничения одновременных запросов
OPENAI_SEMAPHORE = asyncio.Semaphore(5)

def encode_file_to_base64(file_path, user_id):
    """Безопасное кодирование файла в base64"""
    from file_utils import safe_file_exists
    
    # Проверяем, что файл существует в разрешенной директории
    if not safe_file_exists(file_path, user_id):
        raise ValueError("Файл не найден или недоступен")
    
    with open(file_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    mime_type, _ = mimetypes.guess_type(file_path)
    return f"data:{mime_type};base64,{encoded}"

async def send_to_gpt_vision(image_path: str, lang: str = "ru", prompt: str = None):
    """Перенаправляем на Gemini вместо GPT Vision"""
    from gemini_analyzer import send_to_gemini_vision
    return await send_to_gemini_vision(image_path, lang, prompt)


def convert_pdf_to_images(pdf_path: str, output_dir: str, max_pages: int = 5):
    os.makedirs(output_dir, exist_ok=True)
    
    # Удаляем старые страницы
    for f in os.listdir(output_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(output_dir, f))
            
    images = convert_from_path(
        pdf_path,
        first_page=1,
        last_page=max_pages,
        poppler_path=os.path.join(os.getcwd(), "poppler", "Library", "bin")
    )

    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path, "PNG")
        image_paths.append(image_path)

    return image_paths

def format_dialogue(messages, max_len=300):
    """
    ✅ ИСПРАВЛЕННАЯ ВЕРСИЯ: Работает и со словарями (PostgreSQL) и с кортежами (SQLite)
    """
    result = []
    
    for msg in messages:
        try:
            if isinstance(msg, dict):
                # ✅ Новый формат PostgreSQL: {'id': 123, 'role': 'user', 'message': 'текст'}
                role = msg.get('role', 'unknown')
                message_text = msg.get('message', '')
                result.append(f"{role.upper()}: {message_text[:max_len]}")
                
            elif isinstance(msg, (list, tuple)) and len(msg) >= 3:
                # ✅ Старый формат SQLite: (id, role, message)
                role = msg[1]
                message_text = msg[2]
                result.append(f"{role.upper()}: {message_text[:max_len]}")
                
            elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
                # ✅ Упрощенный формат: (role, message)
                role = msg[0]
                message_text = msg[1]
                result.append(f"{role.upper()}: {message_text[:max_len]}")
                
            else:
                # ❌ Неизвестный формат - пропускаем
                print(f"⚠️ Неизвестный формат сообщения: {type(msg)} - {msg}")
                continue
                
        except (KeyError, IndexError, TypeError) as e:
            # ❌ Ошибка доступа к данным - пропускаем это сообщение
            print(f"⚠️ Ошибка обработки сообщения: {e} - {msg}")
            continue
    
    return "\n".join(result)

async def maybe_update_summary(user_id):
    """
    ✅ МУЛЬТИЯЗЫЧНАЯ версия без использования ask_gpt
    Создает сводки разговоров с прямым вызовом OpenAI API
    """
    # Получаем язык пользователя
    try:
        user_lang = await get_user_language(user_id)
        
        # Проверяем корректность языка
        if user_lang not in ['ru', 'uk', 'en']:
            user_lang = 'ru'  # fallback для неподдерживаемых языков
            
        print(f"🌐 Язык пользователя {user_id}: {user_lang}")
    except Exception as e:
        user_lang = "ru"  # fallback
        print(f"❌ Ошибка получения языка, используем русский: {e}")
    
    old_summary, last_id = await get_conversation_summary(user_id)
    new_messages = await get_messages_after(user_id, last_id)
    
    # ✅ БЕЗОПАСНАЯ ПРОВЕРКА: убеждаемся что old_summary не None
    if not old_summary:
        old_summary = ""  # Пустая строка вместо None

    user_messages = []
    for msg in new_messages:
        try:
            if isinstance(msg, dict):
                if msg.get('role') == 'user':
                    user_messages.append(msg)
            elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
                # ❗ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: проверяем правильный индекс
                # get_messages_after возвращает: [{'id': 123, 'role': 'user', 'message': 'текст'}, ...]
                # НО get_last_messages возвращает: [('user', 'текст'), ...]
                
                # Если это словарь из get_messages_after:
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    user_messages.append(msg)
                # Если это кортеж из get_last_messages:
                elif isinstance(msg, (tuple, list)) and len(msg) >= 2 and msg[0] == 'user':
                    user_messages.append(msg)
                    
        except (KeyError, IndexError, TypeError) as e:
            print(f"⚠️ Ошибка обработки сообщения в maybe_update_summary: {e} - {msg}")
            continue
    
    if len(user_messages) < 6:
        return False  # ждём пока пользователь напишет хотя бы 6 новых сообщений

    dialogue = format_dialogue(new_messages)
    today = datetime.now().strftime("%d.%m.%Y")

    # 🌐 МУЛЬТИЯЗЫЧНЫЙ ПРОМПТ (English prompt, user language response)
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian', 
        'en': 'English'
    }
    
    prompt = (
        f"Below is a brief summary of communication between a doctor and patient, compiled earlier. "
        f"Also provided are new messages. Today's date: {today}.\n\n"
        f"🛠 Your task — update the summary, strictly following the rules:\n"
        f"- Each complaint, symptom or recommendation in the summary should have a date of first or last mention.\n"
        f"- If new messages mention an existing problem again — update the date to current ({today}).\n"
        f"- If a topic was **not mentioned** in new messages, **keep it with the previous date**.\n"
        f"- If any problem **hasn't been updated for more than 7 days** and is not mentioned in new messages — **delete it**.\n"
        f"- The final summary should be brief, with dates, maximum 2-3 paragraphs. Don't duplicate or complicate.\n\n"
        f"📘 Previous summary:\n{old_summary}\n\n"
        f"💬 New messages:\n{dialogue}\n\n"
        f"Update the summary considering dates. IMPORTANT: Respond ONLY in {lang_names.get(user_lang, 'Russian')} language:"
    )

    # ⚠️ Ограничиваем объём промта по символам (~токены)
    if len(prompt) > 5000:
        prompt = prompt[:5000]

    # ✅ ПРЯМОЙ ВЫЗОВ OpenAI API ВМЕСТО ask_gpt
    try:
        async with OPENAI_SEMAPHORE:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are a medical conversation summarizer. Create concise, accurate summaries "
                            "of doctor-patient conversations with dates. Focus on symptoms, diagnoses, "
                            "treatments, and recommendations mentioned in the conversation. "
                            f"Always respond ONLY in {lang_names.get(user_lang, 'Russian')} language, "
                            f"regardless of the input language."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3  # Низкая температура для точности сводок
            )
            
            # ✅ БЕЗОПАСНОЕ получение ответа
            response_content = response.choices[0].message.content
            if not response_content:
                print(f"⚠️ GPT вернул None для пользователя {user_id}")
                return False
                
            new_summary = response_content.strip()
            
            # ✅ ПРОВЕРКА: убеждаемся что получили корректный ответ
            if not new_summary:
                print(f"⚠️ GPT вернул пустую сводку для пользователя {user_id}")
                return False
                
            print(f"✅ Сводка успешно обновлена для пользователя {user_id} на языке {user_lang}")
            print(f"📄 Превью сводки: {new_summary[:100]}...")
            
    except Exception as e:
        print(f"❌ Ошибка создания сводки для пользователя {user_id}: {e}")
        return False  # Не обновляем сводку при ошибке

    # Сохраняем сводку только если она отличается от предыдущей
    # ✅ БЕЗОПАСНАЯ ПРОВЕРКА: убеждаемся что переменные не None
    if (new_summary and old_summary and 
        str(new_summary).strip() != str(old_summary).strip()) or \
       (new_summary and not old_summary):  # Или если старой сводки нет, а новая есть
        # ✅ БЕЗОПАСНОЕ получение last_message_id
        try:
            if new_messages:
                last_msg = new_messages[-1]
                if isinstance(last_msg, dict):
                    # Формат: {'id': 123, 'role': 'user', 'message': 'текст'}
                    last_message_id = last_msg.get('id', 0)
                elif isinstance(last_msg, (list, tuple)) and len(last_msg) >= 1:
                    # Формат: ('user', 'текст') - нет ID, берем из базы
                    last_message_id = await get_last_message_id(user_id)
                else:
                    last_message_id = await get_last_message_id(user_id)
            else:
                last_message_id = await get_last_message_id(user_id)
        except Exception as e:
            print(f"❌ Ошибка получения last_message_id: {e}")
            last_message_id = await get_last_message_id(user_id)  # Fallback
        
        await save_conversation_summary(user_id, new_summary, last_message_id)
        print(f"💾 Сводка сохранена для пользователя {user_id}")
        return True
    else:
        print(f"📝 Сводка не изменилась для пользователя {user_id}")
        return False

async def format_user_profile(user_id: int) -> str:
    """
    ✅ ИСПРАВЛЕННАЯ ВЕРСИЯ: получает профиль по user_id
    """
    try:
        from db_postgresql import get_user_profile
        from datetime import datetime
        
        profile = await get_user_profile(user_id)
        
        # ❗ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: profile может быть None или пустой
        if not profile:
            return "Профиль пациента не заполнен"
        
        parts = []

        # Базовая строка: имя, возраст, пол, рост и вес
        base = []
        if profile.get("name"):
            base.append(str(profile["name"]))
        if profile.get("birth_year"):
            try:
                age = datetime.now().year - int(profile["birth_year"])
                base.append(f"{age} y/o")
            except (ValueError, TypeError):
                pass
        if profile.get("gender"):
            base.append(str(profile["gender"]))
        if profile.get("height_cm"):
            base.append(f"{profile['height_cm']} cm")
        if profile.get("weight_kg"):
            base.append(f"{profile['weight_kg']} kg")
        
        if base:
            parts.append(", ".join(base))

        # Остальные параметры в сжатой строке
        extras = []
        if profile.get("allergies"):
            extras.append(f"Allergies: {profile['allergies']}")
        if profile.get("alcohol"):
            extras.append(f"Alcohol: {profile['alcohol']}")
        if profile.get("physical_activity"):
            extras.append(f"Physical activity: {profile['physical_activity']}")
        if profile.get("chronic_conditions"):
            extras.append(f"Chronic conditions: {profile['chronic_conditions']}")
        if profile.get("smoking"):
            extras.append(f"Smoking: {profile['smoking']}")
        if profile.get("family_history"):
            extras.append(f"Family history: {profile['family_history']}")
        if profile.get("medications"):
            extras.append(f"Medications: {profile['medications']}")    

        if extras:
            parts.append(" | ".join(extras))

        return "\n".join(parts) if parts else "Профиль пациента частично заполнен"
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Ошибка формирования профиля для пользователя {user_id}: {e}")
        return "Ошибка загрузки профиля пациента"

async def update_user_profile_medications(user_id: int):
    text = await get_user_medications_text(user_id)
    await update_user_field(user_id, "medications", text)