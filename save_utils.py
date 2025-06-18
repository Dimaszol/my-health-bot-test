import openai
import base64
import mimetypes
import os
from pdf2image import convert_from_path
from db_postgresql import get_conversation_summary, get_messages_after, save_conversation_summary, \
    get_user_medications_text, update_user_field

from gpt import ask_gpt, extract_text_from_image
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

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
    old_summary, last_id = await get_conversation_summary(user_id)
    new_messages = await get_messages_after(user_id, last_id)

    user_messages = []
    for msg in new_messages:
        if isinstance(msg, dict):
            if msg.get('role') == 'user':
                user_messages.append(msg)
        elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
            if msg[1] == 'user':  # или msg[0] в зависимости от формата
                user_messages.append(msg)
    
    if len(user_messages) < 6:
        return  # ждём пока пользователь напишет хотя бы 6 новых сообщений

    dialogue = format_dialogue(new_messages)
    today = datetime.now().strftime("%d.%m.%Y")

    prompt = (
        f"Ниже приведена краткая сводка общения между врачом и пациентом, составленная ранее. "
        f"Также представлены новые сообщения. Сегодняшняя дата: {today}.\n\n"
        f"🛠 Твоя задача — обновить summary, строго следуя правилам:\n"
        f"- Каждая жалоба, симптом или рекомендация в сводке должна иметь дату первого или последнего упоминания.\n"
        f"- Если в новых сообщениях снова говорится об уже существующей проблеме — обнови дату на текущую ({today}).\n"
        f"- Если тема **не упоминалась** в новых сообщениях, **оставь её с предыдущей датой**.\n"
        f"- Если какая-то проблема **не обновлялась более 7 дней**, и в новых сообщениях она не упоминается — **удали её**.\n"
        f"- Итоговая сводка должна быть краткой, с датами, 2–3 абзаца максимум. Не дублируй и не усложняй.\n\n"
        f"📘 Предыдущая сводка:\n{old_summary}\n\n"
        f"💬 Новые сообщения:\n{dialogue}\n\n"
        f"Обнови сводку с учётом дат:"
    )

    # ⚠️ Ограничиваем объём промта по символам (~токены)
    if len(prompt) > 5000:
        prompt = prompt[:5000]
    new_summary = await ask_gpt(prompt)

    if new_summary.strip() != old_summary.strip():
        last_message_id = new_messages[-1][0]
        await save_conversation_summary(user_id, new_summary, last_message_id)

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