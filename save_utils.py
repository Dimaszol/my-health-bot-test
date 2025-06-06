import openai
import base64
import mimetypes
import os
from pdf2image import convert_from_path
from db import get_conversation_summary, get_messages_after, save_conversation_summary, \
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

async def send_to_gpt_vision(file_path: str):  # ✅ ИСПРАВЛЕНО: добавлен async
    """Обёртка для Vision, использующая обновлённый промт с удалением персональных данных"""
    with open(file_path, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    system_prompt = (
        "You are a medical assistant specialized in extracting text from scanned documents and images. "
        "⚠️ Your task is to accurately extract all readable medical text **in the original language** of the document. "
        "⚠️ However, you must remove all personal and identifying information — including full names of patients or doctors, age, gender, addresses, card numbers, clinic or hospital names. "
        "Do not summarize, skip, or interpret the content. Do not add explanations."
        "Just extract the pure medical content, keeping only one key date (the most relevant or latest) if multiple dates are present."
    )

    user_prompt = (
        "This is a scanned medical document (e.g., discharge summary, lab report, consultation, prescription, or form). "
        "Extract the entire readable text **in the same language as in the image**, but remove all of the following:\n"
        "- Full names of any individuals (patients, doctors, lab staff)\n"
        "- Age, gender\n"
        "- Addresses, contact details, ID or card numbers\n"
        "- Clinic, hospital, laboratory names or logos\n\n"
        "Return only the medical text with just one key date — the date of the conclusion or result. Ignore and remove all other dates."
        "Do NOT explain your actions or mention what was removed. Do NOT translate the content. Just return the clean medical text."
    )

    # ✅ ИСПРАВЛЕНО: используем асинхронный клиент
    from gpt import client
    response = await client.chat.completions.create(
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

    raw_text = response.choices[0].message.content.strip()
    print("\n[Vision Output]:")
    print(raw_text)

    summary = raw_text  # временно оставляем одинаково
    return raw_text, summary


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
    return "\n".join([f"{role.upper()}: {msg[:max_len]}" for _, role, msg in messages])

async def maybe_update_summary(user_id):
    old_summary, last_id = await get_conversation_summary(user_id)
    new_messages = await get_messages_after(user_id, after_id=last_id)

    user_messages = [m for m in new_messages if m[1] == "user"]
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

def format_user_profile(profile: dict) -> str:
    parts = []

    # Базовая строка: имя, возраст, пол, рост и вес
    base = []
    if profile.get("name"):
        base.append(profile["name"])
    if profile.get("birth_year"):
        age = datetime.now().year - profile["birth_year"]
        base.append(f"{age} y/o")
    if profile.get("gender"):
        base.append(profile["gender"])
    if profile.get("height_cm"):
        base.append(f"{profile['height_cm']} cm")
    if profile.get("weight_kg"):
        base.append(f"{profile['weight_kg']} kg")
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

    return "\n".join(parts)

async def update_user_profile_medications(user_id: int):
    text = await get_user_medications_text(user_id)
    await update_user_field(user_id, "medications", text)