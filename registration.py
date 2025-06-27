from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from db_postgresql import save_user, update_user_field, user_exists, t, get_user_language, get_user_name
from keyboards import language_keyboard, skip_keyboard, gender_keyboard, smoking_keyboard, \
    alcohol_keyboard, activity_keyboard, registration_keyboard, show_main_menu
from datetime import datetime
from user_state_manager import user_state_manager, user_states
import re

# Старт регистрации
async def start_registration(user_id: int, message: Message):
    """
    Старт регистрации - теперь всегда с опцией смены языка
    """
    lang = await get_user_language(user_id)
    
    # Устанавливаем состояние ожидания имени
    user_states[user_id] = {"step": "awaiting_name"}
    
    # Формируем интро-текст
    intro_text = f"{t('intro_1', lang)}\n\n{t('intro_2', lang)}\n\n{t('ask_name', lang)}"
    
    # Клавиатура с кнопкой смены языка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("change_language", lang), 
            callback_data="change_language_registration"
        )]
    ])
    
    await message.answer(
        intro_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ✅ ФУНКЦИИ ВАЛИДАЦИИ
def validate_name(name: str) -> bool:
    """Валидация имени"""
    if not name or len(name.strip()) < 1:
        return False
    # Убираем лишние пробелы и проверяем длину
    clean_name = name.strip()
    if len(clean_name) > 50:  # Максимум 50 символов
        return False
    # Проверяем, что имя содержит хотя бы одну букву
    if not re.search(r'[a-zA-Zа-яА-ЯёЁіІїЇєЄ]', clean_name):
        return False
    return True

def validate_text_field(text: str, max_length: int = 200) -> bool:
    """Валидация текстовых полей (аллергии, хронические заболевания и т.д.)"""
    if not text:
        return True  # Пустые поля допустимы
    clean_text = text.strip()
    if len(clean_text) > max_length:
        return False
    return True

def get_valid_smoking_values(lang: str) -> list:
    """Получить валидные значения для курения"""
    return [
        t("smoking_yes", lang), t("smoking_no", lang), "Vape", t("skip", lang),
        # Дополнительные варианты на разных языках
        "Да", "Нет", "Так", "Ні", "Yes", "No", "Ja", "Nein"
    ]

def get_valid_alcohol_values(lang: str) -> list:
    """Получить валидные значения для алкоголя"""
    return [
        t("alcohol_never", lang), t("alcohol_sometimes", lang), t("alcohol_often", lang), t("skip", lang),
        # Дополнительные варианты
        "Не употребляю", "Иногда", "Часто", "Не вживаю", "Іноді", 
        "Never", "Sometimes", "Often", "Nie", "Manchmal", "Oft"
    ]

def get_valid_activity_values(lang: str) -> list:
    """Получить валидные значения для активности"""
    return [
        "❌ Нет активности", "🚶 Низкая", "🏃 Средняя", "💪 Высокая", "🏆 Профессиональная",
        "❌ Відсутня активність", "🚶 Низька", "🏃 Середня", "💪 Висока", "🏆 Професійна",
        "❌ No activity", "🚶 Low", "🏃 Medium", "💪 High", "🏆 Professional",
        "❌ Keine Aktivität", "🚶 Niedrig", "🏃 Mittel", "💪 Hoch", "🏆 Professionell",
        t("skip", lang)
    ]

def get_valid_gender_values(lang: str) -> list:
    """Получить валидные значения для пола"""
    return [
        t("gender_male", lang), t("gender_female", lang), t("gender_other", lang), t("skip", lang),
        # Дополнительные варианты
        "Мужской", "Женский", "Другое", "Чоловіча", "Жіноча", "Інше",
        "Male", "Female", "Other", "Männlich", "Weiblich", "Andere"
    ]

# Обработка регистрации по шагам
async def handle_registration_step(user_id: int, message: Message) -> bool:
    lang = await get_user_language(user_id)
    state = user_states.get(user_id)

    if not state:
        return False

    if isinstance(state, dict) and state.get("step") == "awaiting_name":
        name = message.text.strip() if message.text else ""
        
        # ✅ ВАЛИДАЦИЯ ИМЕНИ
        if not validate_name(name):
            if not name:
                await message.answer(t("name_missing", lang))
            elif len(name) > 50:
                await message.answer("⚠️ Имя слишком длинное. Максимум 50 символов.")
            else:
                await message.answer("⚠️ Введите корректное имя (должно содержать буквы).")
            return True
        
        user_states[user_id] = {
            "step": "awaiting_birth_year",
            "name": name
        }
        await message.answer(t("birth_year_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if not isinstance(state, dict):
        return False

    step = state.get("step")

    if step == "awaiting_birth_year":
        if message.text == t("skip", lang):
            state["birth_year"] = None
        else:
            try:
                year_text = message.text.strip() if message.text else ""
                year = int(year_text)
                current_year = datetime.now().year
                if year < 1900 or year > current_year:
                    raise ValueError
                # Дополнительная проверка возраста
                age = current_year - year
                if age > 120:  # Максимальный возраст
                    raise ValueError
                state["birth_year"] = year
            except (ValueError, TypeError):
                await message.answer(t("birth_year_invalid", lang))
                return True
        state["step"] = "awaiting_gender"
        await message.answer(t("gender_prompt", lang), reply_markup=gender_keyboard(lang))
        return True

    if step == "awaiting_gender":
        # ✅ ВАЛИДАЦИЯ ПОЛА
        valid_genders = get_valid_gender_values(lang)
        
        if message.text == t("skip", lang):
            state["gender"] = None
        elif message.text in valid_genders:
            state["gender"] = message.text.strip()
        else:
            await message.answer(
                "⚠️ Пожалуйста, выберите пол, используя кнопки:",
                reply_markup=gender_keyboard(lang)
            )
            return True
            
        state["step"] = "awaiting_height"
        await message.answer(t("height_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if step == "awaiting_height":
        if message.text == t("skip", lang):
            state["height_cm"] = None
        else:
            try:
                height_text = message.text.strip() if message.text else ""
                height = int(height_text)
                if height < 100 or height > 250:
                    raise ValueError
                state["height_cm"] = height
            except (ValueError, TypeError):
                await message.answer(t("height_invalid", lang))
                return True
        state["step"] = "awaiting_weight"
        await message.answer(t("weight_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if step == "awaiting_weight":
        if message.text == t("skip", lang):
            state["weight_kg"] = None
        else:
            try:
                weight_text = message.text.strip() if message.text else ""
                weight = float(weight_text)
                if weight < 30 or weight > 300:
                    raise ValueError
                state["weight_kg"] = weight
            except (ValueError, TypeError):
                await message.answer(t("weight_invalid", lang))
                return True

        await save_user(user_id=user_id, name=state.get("name"), birth_year=state.get("birth_year"))
        await update_user_field(user_id, "gender", state.get("gender"))
        await update_user_field(user_id, "height_cm", state.get("height_cm"))
        await update_user_field(user_id, "weight_kg", state.get("weight_kg"))

        state["step"] = "ask_full_profile"
        await message.answer(
            t("registration_done", lang),
            reply_markup=registration_keyboard(lang)
        )
        return True

    if step == "ask_full_profile":
        valid_profile_options = [t("complete_profile", lang), t("finish_registration", lang)]
        
        if message.text not in valid_profile_options:
            await message.answer(
                "⚠️ Пожалуйста, выберите один из вариантов, используя кнопки:",
                reply_markup=registration_keyboard(lang)
            )
            return True
            
        if message.text == t("complete_profile", lang):
            state["step"] = "chronic_conditions"
            await message.answer(t("profile_extra_prompt", lang), reply_markup=skip_keyboard(lang))
        else:
            user_states[user_id] = None
            await message.answer(t("welcome", lang, name=await get_user_name(user_id)))
            await message.answer(t("how_to_use_1", lang))
            await show_main_menu(message, lang)
        return True

    if step == "chronic_conditions":
        if message.text != t("skip", lang):
            text = message.text.strip() if message.text else ""
            # ✅ ВАЛИДАЦИЯ ТЕКСТОВОГО ПОЛЯ
            if not validate_text_field(text, 100):
                await message.answer("⚠️ Слишком длинный текст. Максимум 100 символов.")
                return True
            await update_user_field(user_id, "chronic_conditions", text)
        state["step"] = "allergies"
        await message.answer(t("allergies_prompt", lang), reply_markup=skip_keyboard(lang))
        return True
    
    if step == "allergies":
        if message.text != t("skip", lang):
            text = message.text.strip() if message.text else ""
            # ✅ ВАЛИДАЦИЯ ТЕКСТОВОГО ПОЛЯ
            if not validate_text_field(text, 50):
                await message.answer("⚠️ Слишком длинный текст. Максимум 50 символов.")
                return True
            await update_user_field(user_id, "allergies", text)
        state["step"] = "smoking"
        await message.answer(t("smoking_prompt", lang), reply_markup=smoking_keyboard(lang))
        return True

    if step == "smoking":
        # ✅ ВАЛИДАЦИЯ КУРЕНИЯ
        valid_smoking = get_valid_smoking_values(lang)
        
        if message.text not in valid_smoking:
            await message.answer(
                "⚠️ Пожалуйста, выберите один из вариантов, используя кнопки:",
                reply_markup=smoking_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            await update_user_field(user_id, "smoking", message.text.strip())
        state["step"] = "alcohol"
        await message.answer(t("alcohol_prompt", lang), reply_markup=alcohol_keyboard(lang))
        return True

    if step == "alcohol":
        # ✅ ВАЛИДАЦИЯ АЛКОГОЛЯ
        valid_alcohol = get_valid_alcohol_values(lang)
        
        if message.text not in valid_alcohol:
            await message.answer(
                "⚠️ Пожалуйста, выберите один из вариантов, используя кнопки:",
                reply_markup=alcohol_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            await update_user_field(user_id, "alcohol", message.text.strip())
        state["step"] = "physical_activity"
        await message.answer(t("activity_prompt", lang), reply_markup=activity_keyboard(lang))
        return True

    if step == "physical_activity":
        # ✅ ВАЛИДАЦИЯ АКТИВНОСТИ
        valid_activity = get_valid_activity_values(lang)
        
        if message.text not in valid_activity:
            await message.answer(
                "⚠️ Пожалуйста, выберите один из вариантов, используя кнопки:",
                reply_markup=activity_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            # ✅ ИСПРАВЛЕННЫЙ маппинг активности с немецким языком
            activity_map = {
                # Русские варианты
                "❌ Нет активности": "Нет активности",
                "🚶 Низкая": "Низкая",
                "🏃 Средняя": "Средняя", 
                "💪 Высокая": "Высокая",
                "🏆 Профессиональная": "Профессиональная",
                
                # Украинские варианты
                "❌ Відсутня активність": "Нет активности",
                "🚶 Низька": "Низкая",
                "🏃 Середня": "Средняя",
                "💪 Висока": "Высокая", 
                "🏆 Професійна": "Профессиональная",
                
                # Английские варианты
                "❌ No activity": "No activity",
                "🚶 Low": "Low",
                "🏃 Medium": "Medium",
                "💪 High": "High",
                "🏆 Professional": "Professional",
                
                # Немецкие варианты
                "❌ Keine Aktivität": "No activity",
                "🚶 Niedrig": "Low",
                "🏃 Mittel": "Medium",
                "💪 Hoch": "High",
                "🏆 Professionell": "Professional"
            }
            
            # Получаем унифицированное значение
            unified_value = activity_map.get(message.text.strip(), message.text.strip())
            await update_user_field(user_id, "physical_activity", unified_value)
        
        state["step"] = "family_history"
        await message.answer(t("family_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if step == "family_history":
        if message.text != t("skip", lang):
            text = message.text.strip() if message.text else ""
            # ✅ ВАЛИДАЦИЯ ТЕКСТОВОГО ПОЛЯ
            if not validate_text_field(text, 300):
                await message.answer("⚠️ Слишком длинный текст. Максимум 300 символов.")
                return True
            await update_user_field(user_id, "family_history", text)
        user_states[user_id] = None
        await message.answer(t("profile_thanks", lang))
        await message.answer(t("welcome", lang, name=await get_user_name(user_id)))
        await message.answer(t("how_to_use_1", lang))
        await show_main_menu(message, lang)
        return True

    return False