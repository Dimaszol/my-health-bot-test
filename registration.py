from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from db import save_user, update_user_field, user_exists, t, get_user_language, get_user_name
from keyboards import language_keyboard, skip_keyboard, gender_keyboard, smoking_keyboard, \
    alcohol_keyboard, activity_keyboard, registration_keyboard, show_main_menu
from datetime import datetime
from user_state_manager import user_state_manager, user_states

# Старт регистрации
async def start_registration(user_id: int, message: Message):
    lang = await get_user_language(user_id)
    user_states[user_id] = {"step": "awaiting_name"}
    await message.answer(t("intro_1", lang))
    await message.answer(t("intro_2", lang))
    await message.answer(t("ask_name", lang), reply_markup=language_keyboard())

# Обработка регистрации по шагам
async def handle_registration_step(user_id: int, message: Message) -> bool:
    lang = await get_user_language(user_id)
    state = user_states.get(user_id)

    if not state:
        return False

    if isinstance(state, dict) and state.get("step") == "awaiting_name":
        name = message.text.strip()
        if not name:
            await message.answer(t("name_missing", lang))
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
                year = int(message.text.strip())
                if year < 1900 or year > datetime.now().year:
                    raise ValueError
                state["birth_year"] = year
            except ValueError:
                await message.answer(t("birth_year_invalid", lang))
                return True
        state["step"] = "awaiting_gender"
        await message.answer(t("gender_prompt", lang), reply_markup=gender_keyboard(lang))
        return True

    if step == "awaiting_gender":
        if message.text == t("skip", lang):
            state["gender"] = None
        else:
            state["gender"] = message.text.strip()
        state["step"] = "awaiting_height"
        await message.answer(t("height_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if step == "awaiting_height":
        if message.text == t("skip", lang):
            state["height_cm"] = None
        else:
            try:
                height = int(message.text.strip())
                if height < 100 or height > 250:
                    raise ValueError
                state["height_cm"] = height
            except ValueError:
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
                weight = float(message.text.strip())
                if weight < 30 or weight > 300:
                    raise ValueError
                state["weight_kg"] = weight
            except ValueError:
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
            await update_user_field(user_id, "chronic_conditions", message.text.strip())
        state["step"] = "allergies"
        await message.answer(t("allergies_prompt", lang), reply_markup=skip_keyboard(lang))
        return True
    
    if step == "allergies":
        if message.text != t("skip", lang):
            await update_user_field(user_id, "allergies", message.text.strip())
        state["step"] = "smoking"
        await message.answer(t("smoking_prompt", lang), reply_markup=smoking_keyboard(lang))
        return True

    if step == "smoking":
        if message.text != t("skip", lang):
            await update_user_field(user_id, "smoking", message.text.strip())
        state["step"] = "alcohol"
        await message.answer(t("alcohol_prompt", lang), reply_markup=alcohol_keyboard(lang))
        return True

    if step == "alcohol":
        if message.text != t("skip", lang):
            await update_user_field(user_id, "alcohol", message.text.strip())
        state["step"] = "physical_activity"
        await message.answer(t("activity_prompt", lang), reply_markup=activity_keyboard(lang))
        return True

    if step == "physical_activity":
        if message.text != t("skip", lang):
            activity_map = {
                "❌ Нет активности": "Нет активности",
                "🚶 Низкая": "Низкая",
                "🏃 Средняя": "Средняя",
                "💪 Высокая": "Высокая",
                "🏆 Профессиональная": "Профессиональная"
            }
            value = activity_map.get(message.text.strip(), message.text.strip())
            await update_user_field(user_id, "physical_activity", value)
        state["step"] = "family_history"
        await message.answer(t("family_prompt", lang), reply_markup=skip_keyboard(lang))
        return True

    if step == "family_history":
        if message.text != t("skip", lang):
            await update_user_field(user_id, "family_history", message.text.strip())
        user_states[user_id] = None
        await message.answer(t("profile_thanks", lang))
        await message.answer(t("welcome", lang, name=await get_user_name(user_id)))
        await message.answer(t("how_to_use_1", lang))
        await show_main_menu(message, lang)
        return True

    return False
