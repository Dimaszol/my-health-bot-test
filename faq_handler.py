# faq_handler.py - Обработчики для FAQ раздела

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db_postgresql import get_user_language
from faq_texts import get_faq_text

class FAQHandler:
    """Класс для обработки FAQ раздела"""
    
    @staticmethod
    def create_faq_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
        """Создает компактную клавиатуру FAQ (одинаковая для всех разделов)"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_faq_text("faq_getting_started", lang),
                    callback_data="faq_getting_started"
                ),
                InlineKeyboardButton(
                    text=get_faq_text("faq_subscriptions", lang),
                    callback_data="faq_subscriptions"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_faq_text("faq_documents", lang),
                    callback_data="faq_documents"
                ),
                InlineKeyboardButton(
                    text=get_faq_text("faq_notes", lang),
                    callback_data="faq_notes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_faq_text("faq_medications", lang),
                    callback_data="faq_medications"
                ),
                InlineKeyboardButton(
                    text=get_faq_text("faq_profile", lang),
                    callback_data="faq_profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_faq_text("faq_security", lang),
                    callback_data="faq_security"
                ),
                InlineKeyboardButton(
                    text=get_faq_text("faq_support", lang),
                    callback_data="faq_support"
                )
            ]
        ])
        return keyboard
    
    @staticmethod
    async def show_faq_main(message_or_callback, lang: str = None):
        """Показывает главное меню FAQ"""
        if isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id
            message = message_or_callback.message
        else:
            user_id = message_or_callback.from_user.id
            message = message_or_callback
        
        if not lang:
            lang = await get_user_language(user_id)
        
        text = get_faq_text("faq_main_title", lang)
        keyboard = FAQHandler.create_faq_keyboard(lang)
        
        if isinstance(message_or_callback, types.CallbackQuery):
            await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await message_or_callback.answer()
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    @staticmethod
    async def show_faq_section(callback: types.CallbackQuery, section: str):
        """Показывает конкретный раздел FAQ с тем же меню"""
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Получаем заголовок из переводов
        section_title = get_faq_text(section, lang)
        content_key = f"{section}_content"
        content_text = get_faq_text(content_key, lang)
        
        # Объединяем заголовок и контент
        full_text = f"{section_title}\n\n{content_text}"
        
        keyboard = FAQHandler.create_faq_keyboard(lang)
        
        await callback.message.edit_text(
            full_text, 
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await callback.answer()

# Функции для интеграции в main.py
async def handle_faq_main(callback: types.CallbackQuery):
    """Обработчик главного меню FAQ"""
    await FAQHandler.show_faq_main(callback)

async def handle_faq_section(callback: types.CallbackQuery):
    """Обработчик разделов FAQ"""
    section = callback.data  # faq_getting_started, faq_subscriptions, etc.
    await FAQHandler.show_faq_section(callback, section)