from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from db_postgresql import get_user_language, t

async def show_main_menu(message: Message, lang: str = None):
    if lang is None:
        lang = await get_user_language(message.from_user.id)
    await message.answer(
        t("main_menu", lang),
        reply_markup=main_menu_keyboard(lang)
    )

def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇦 Українська")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )

def main_menu_keyboard(lang):
    """Главное меню с кнопкой настроек"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("main_upload_doc", lang)), KeyboardButton(text=t("main_note", lang))],
            [KeyboardButton(text=t("main_documents", lang)), KeyboardButton(text=t("main_schedule", lang))],
            [KeyboardButton(text=t("main_settings", lang))]
        ],
        resize_keyboard=True
    )

def settings_keyboard(lang):
    """Inline клавиатура меню настроек"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("settings_profile", lang), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("settings_faq", lang), callback_data="settings_faq")],
        [InlineKeyboardButton(text=t("settings_subscription", lang), callback_data="settings_subscription")]
    ])

def skip_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("skip", lang))]],
        resize_keyboard=True
    )

def gender_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("gender_male", lang)), KeyboardButton(text=t("gender_female", lang))],
            [KeyboardButton(text=t("gender_other", lang)), KeyboardButton(text=t("skip", lang))]
        ],
        resize_keyboard=True
    )

def smoking_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("smoking_yes", lang)), KeyboardButton(text=t("smoking_no", lang))],
            [KeyboardButton(text="Vape"), KeyboardButton(text=t("skip", lang))]
        ],
        resize_keyboard=True
    )

def alcohol_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("alcohol_never", lang)), KeyboardButton(text=t("alcohol_sometimes", lang))],
            [KeyboardButton(text=t("alcohol_often", lang)), KeyboardButton(text=t("skip", lang))]
        ],
        resize_keyboard=True
    )

def activity_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("activity_none", lang)), KeyboardButton(text=t("activity_low", lang))],
            [KeyboardButton(text=t("activity_medium", lang)), KeyboardButton(text=t("activity_high", lang))],
            [KeyboardButton(text=t("activity_pro", lang)), KeyboardButton(text=t("skip", lang))]
        ],
        resize_keyboard=True
    )

def registration_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("complete_profile", lang))],
            [KeyboardButton(text=t("finish_registration", lang))]
        ],
        resize_keyboard=True
    )
