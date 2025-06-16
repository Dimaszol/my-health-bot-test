# profile_keyboards.py - НОВЫЙ ФАЙЛ, создать в корне проекта

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db_postgresql import t

def profile_view_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("profile_edit_button", lang), callback_data="edit_profile")],
        [InlineKeyboardButton(text=t("profile_back_button", lang), callback_data="back_to_settings")]
    ])

def profile_edit_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора поля редактирования"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("edit_name_button", lang), callback_data="edit_field_name")],
        [InlineKeyboardButton(text=t("edit_height_button", lang), callback_data="edit_field_height_cm")],  # ✅ ИСПРАВЛЕНО
        [InlineKeyboardButton(text=t("edit_weight_button", lang), callback_data="edit_field_weight_kg")],   # ✅ ИСПРАВЛЕНО
        [InlineKeyboardButton(text=t("edit_allergies_button", lang), callback_data="edit_field_allergies")],
        [InlineKeyboardButton(text=t("edit_smoking_button", lang), callback_data="edit_field_smoking")],
        [InlineKeyboardButton(text=t("edit_alcohol_button", lang), callback_data="edit_field_alcohol")],
        [InlineKeyboardButton(text=t("edit_activity_button", lang), callback_data="edit_field_physical_activity")],  # ✅ ИСПРАВЛЕНО
        [InlineKeyboardButton(text=t("edit_language_button", lang), callback_data="edit_field_language")],
        [InlineKeyboardButton(text=t("back_to_profile", lang), callback_data="back_to_profile")]
    ])

def smoking_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора курения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("smoking_yes", lang), callback_data="smoking_yes")],
        [InlineKeyboardButton(text=t("smoking_no", lang), callback_data="smoking_no")],
        [InlineKeyboardButton(text="Vape", callback_data="smoking_vape")],
        [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_edit")]
    ])

def alcohol_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора алкоголя"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("alcohol_never", lang), callback_data="alcohol_never")],
        [InlineKeyboardButton(text=t("alcohol_sometimes", lang), callback_data="alcohol_sometimes")],
        [InlineKeyboardButton(text=t("alcohol_often", lang), callback_data="alcohol_often")],
        [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_edit")]
    ])

def activity_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора активности"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("activity_none", lang), callback_data="activity_none")],
        [InlineKeyboardButton(text=t("activity_low", lang), callback_data="activity_low")],
        [InlineKeyboardButton(text=t("activity_medium", lang), callback_data="activity_medium")],
        [InlineKeyboardButton(text=t("activity_high", lang), callback_data="activity_high")],
        [InlineKeyboardButton(text=t("activity_pro", lang), callback_data="activity_pro")],
        [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_edit")]
    ])

def language_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
    ])

def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены для текстового ввода"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("cancel", lang))]],
        resize_keyboard=True,
        one_time_keyboard=True,  # ✅ ДОБАВЛЕНО: автоматически убирает клавиатуру после нажатия
        input_field_placeholder="Введите значение или нажмите Отмена"  # ✅ ДОБАВЛЕНО: подсказка
    )