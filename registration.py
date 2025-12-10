# registration.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с полной локализацией

from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from db_postgresql import save_user, update_user_field, t, get_user_language, get_user_name, get_user
from keyboards import skip_keyboard, gender_keyboard, smoking_keyboard, alcohol_keyboard, activity_keyboard, registration_keyboard, show_main_menu
from datetime import datetime
from user_state_manager import user_state_manager, user_states
import re
import asyncio

async def send_long_message(message, text: str, max_length: int = 4000):
    """Отправка длинного сообщения частями"""
    if len(text) <= max_length:
        await message.answer(text, parse_mode="HTML")
        return
    
    # Разбиваем по разделам (заголовки с **)
    parts = text.split('\n\n')
    current_part = ""
    
    for part in parts:
        if len(current_part + part + '\n\n') <= max_length:
            current_part += part + '\n\n'
        else:
            if current_part:
                await message.answer(current_part.strip(), parse_mode="HTML")
                await asyncio.sleep(1)  # Пауза между частями
            current_part = part + '\n\n'
    
    # Отправляем последнюю часть
    if current_part:
        await message.answer(current_part.strip(), parse_mode="HTML")

async def show_gdpr_welcome(user_id: int, message: Message, lang: str):
    """
    НОВЫЙ ПЕРВЫЙ ШАГ: Показать GDPR дисклеймер с согласием
    Это теперь самый первый экран для новых пользователей
    """
    
    # Формируем GDPR дисклеймер
    disclaimer_text = f"{t('gdpr_welcome_title', lang)}\n\n{t('gdpr_welcome_text', lang)}"
    
    # ✅ ИСПРАВЛЕННЫЕ КНОПКИ:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("gdpr_consent_button", lang),
            callback_data="gdpr_consent_agree"
        )],
        [InlineKeyboardButton(
            text=t("change_language", lang),
            callback_data="change_language_registration"
        )],
        [InlineKeyboardButton(
            text=t("open_web_version", lang),
            url="https://pulsebook.health"
        )]
    ])
    
    try:
        # Проверяем, это callback или обычное сообщение
        if hasattr(message, 'message_id') and hasattr(message, 'bot'):
            # Это CallbackQuery.message - можно редактировать
            await message.edit_text(
                disclaimer_text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        else:
            # Это обычное Message - отправляем новое
            await message.answer(
                disclaimer_text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    except Exception as e:
        # Fallback - ВСЕГДА отправляем новое сообщение
        await message.answer(
            disclaimer_text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

async def start_registration(user_id: int, message: Message):
    """
    УПРОЩЕННАЯ регистрация: сразу начинаем с года рождения (имя уже есть из Telegram)
    """
    lang = await get_user_language(user_id)
    
    # СРАЗУ устанавливаем состояние ожидания года рождения (пропускаем имя)
    user_states[user_id] = {"step": "awaiting_birth_year"}
    
    # Получаем имя пользователя из базы (уже сохранено из Telegram)
    user_data = await get_user(user_id)
    user_name = user_data.get('name', 'Пользователь') if user_data else 'Пользователь'
    
    # Формируем приветственный текст через ключи локализации
    intro_text = f"{t('intro_1', lang, name=user_name)}\n\n{t('intro_2', lang)}\n\n{t('birth_year_prompt', lang)}"
    
    await message.answer(
        intro_text,
        reply_markup=skip_keyboard(lang),  # Добавляем кнопку "Пропустить"
        parse_mode="HTML"
    )

# ✅ ФУНКЦИИ ВАЛИДАЦИИ (оставляем, могут пригодиться для других полей)
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

def validate_text_field(text: str, max_length: int = 50) -> bool:  # ✅ ИЗМЕНЕНО: по умолчанию 50
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
                current_year = datetime.now().year - 16
                if year < 1900 or year > current_year:
                    raise ValueError
                state["birth_year"] = year
            except (ValueError, TypeError):
                await message.answer(t("birth_year_invalid", lang))
                return True
        state["step"] = "awaiting_gender"
        await message.answer(t("gender_prompt", lang), reply_markup=gender_keyboard(lang))
        return True

    if step == "awaiting_gender":
        # ✅ ИСПРАВЛЕНО: Локализованная валидация пола
        valid_genders = get_valid_gender_values(lang)
        
        if message.text == t("skip", lang):
            state["gender"] = None
        elif message.text in valid_genders:
            state["gender"] = message.text.strip()
        else:
            await message.answer(
                t("use_buttons_please", lang),  # ✅ ЛОКАЛИЗОВАНО
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

        await save_user(user_id=user_id, name=None, birth_year=state.get("birth_year"))
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
                t("use_buttons_please", lang),  # ✅ ЛОКАЛИЗОВАНО
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
            # ✅ ИСПРАВЛЕНО: унифицируем до 50 символов
            if not validate_text_field(text, 50):  # БЫЛО: 100
                await message.answer(t("text_too_long", lang, max_len=50))  # БЫЛО: 100
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
                await message.answer(t("text_too_long", lang, max_len=50))
                return True
            await update_user_field(user_id, "allergies", text)
        state["step"] = "smoking"
        await message.answer(t("smoking_prompt", lang), reply_markup=smoking_keyboard(lang))
        return True

    if step == "smoking":
        # ✅ ИСПРАВЛЕНО: Локализованная валидация курения
        valid_smoking = get_valid_smoking_values(lang)
        
        if message.text not in valid_smoking:
            await message.answer(
                t("use_buttons_please", lang),  # ✅ ЛОКАЛИЗОВАНО
                reply_markup=smoking_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            await update_user_field(user_id, "smoking", message.text.strip())
        state["step"] = "alcohol"
        await message.answer(t("alcohol_prompt", lang), reply_markup=alcohol_keyboard(lang))
        return True

    if step == "alcohol":
        # ✅ ИСПРАВЛЕНО: Локализованная валидация алкоголя
        valid_alcohol = get_valid_alcohol_values(lang)
        
        if message.text not in valid_alcohol:
            await message.answer(
                t("use_buttons_please", lang),  # ✅ ЛОКАЛИЗОВАНО
                reply_markup=alcohol_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            await update_user_field(user_id, "alcohol", message.text.strip())
        state["step"] = "physical_activity"
        await message.answer(t("activity_prompt", lang), reply_markup=activity_keyboard(lang))
        return True

    if step == "physical_activity":
        # ✅ ИСПРАВЛЕНО: Локализованная валидация активности
        valid_activity = get_valid_activity_values(lang)
        
        if message.text not in valid_activity:
            await message.answer(
                t("use_buttons_please", lang),  # ✅ ЛОКАЛИЗОВАНО
                reply_markup=activity_keyboard(lang)
            )
            return True
            
        if message.text != t("skip", lang):
            # ✅ ИСПРАВЛЕННЫЙ маппинг активности - сохраняем оригинальные значения по языкам
            activity_map = {
                # Русские варианты
                "❌ Нет активности": "Нет активности",
                "🚶 Низкая": "Низкая",
                "🏃 Средняя": "Средняя", 
                "💪 Высокая": "Высокая",
                "🏆 Профессиональная": "Профессиональная",
                
                # Украинские варианты
                "❌ Відсутня активність": "Відсутня активність",
                "🚶 Низька": "Низька",
                "🏃 Середня": "Середня",
                "💪 Висока": "Висока", 
                "🏆 Професійна": "Професійна",
                
                # Английские варианты
                "❌ No activity": "No activity",
                "🚶 Low": "Low",
                "🏃 Medium": "Medium",
                "💪 High": "High",
                "🏆 Professional": "Professional",
                
                # ✅ ИСПРАВЛЕНО: Немецкие варианты сохраняют немецкие значения
                "❌ Keine Aktivität": "Keine Aktivität",
                "🚶 Niedrig": "Niedrig",
                "🏃 Mittel": "Mittel",
                "💪 Hoch": "Hoch",
                "🏆 Professionell": "Professionell"
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
            if not validate_text_field(text, 50):
                await message.answer(t("text_too_long", lang, max_len=50))
                return True
            await update_user_field(user_id, "family_history", text)
        
        # ✅ ЗАВЕРШЕНИЕ АНКЕТЫ
        await message.answer(t("profile_thanks", lang))
        
        # ✅ СНАЧАЛА ПРИВЕТСТВИЕ И ИНСТРУКЦИИ
        await message.answer(t("welcome", lang, name=await get_user_name(user_id)))
        await message.answer(t("how_to_use_1", lang))
        await show_main_menu(message, lang)
        await asyncio.sleep(1)
        
        # 🔥 ПОТОМ ГЕНЕРИРУЕМ АНАЛИЗ ЗДОРОВЬЯ
        # Отправляем сообщение о подготовке и сохраняем его для удаления
        preparing_msg = await message.answer(t("preparing_health_analysis", lang), parse_mode="HTML")
        
        try:
            # Получаем данные пользователя для анализа
            user_data = await get_user(user_id)
            
            # Импортируем функцию из gpt.py
            from gpt import generate_health_analysis
            
            # Генерируем анализ
            analysis = await generate_health_analysis(user_data, lang)
            
            # Удаляем сообщение "готовлю анализ"
            try:
                await preparing_msg.delete()
            except:
                pass  # Игнорируем если не удалось удалить
            
            # Отправляем только анализ без лишнего текста
            await send_long_message(message, analysis)
            
        except Exception as e:
            # Удаляем сообщение "готовлю анализ"
            try:
                await preparing_msg.delete()
            except:
                pass
            
            # Локализованная ошибка
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating health analysis: {str(e)[:100]}")
            await message.answer(t("analysis_error", lang), parse_mode="HTML")
        
        # Очищаем состояние
        user_states[user_id] = None
        return True

    return False