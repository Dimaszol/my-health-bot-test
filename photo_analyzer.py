# photo_analyzer.py - Анализ фотографий с вопросом пользователя

import os
import logging
from typing import Optional, Tuple
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from gemini_analyzer import send_to_gemini_vision
from db_postgresql import get_user_language, t
from subscription_manager import spend_gpt4o_limit
from file_utils import create_simple_file_path, validate_file_size
from notification_system import NotificationSystem
from registration import user_states

logger = logging.getLogger(__name__)

async def handle_photo_analysis(message: types.Message, bot):
    """
    Основная функция обработки фото для анализа
    
    Args:
        message: Сообщение с фото
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        
        # ✅ НАПРЯМУЮ проверяем лимиты из базы (без лишних вызовов)
        from db_postgresql import get_user_limits
        limits = await get_user_limits(user_id)
        gpt4o_limit = limits.get('gpt4o_queries_left', 0)
        
        if gpt4o_limit <= 0:
            
            # ✅ ИСПРАВЛЕНИЕ: Показываем уведомление и останавливаемся
            await NotificationSystem._show_limits_exceeded_notification(
                message, user_id, action_type="image"
            )
            return  # ✅ Останавливаемся сразу
        
        # Получаем фото (берем самое большое разрешение)
        if not message.photo:
            await message.answer(t("please_send_file", lang))
            return
        
        photo = message.photo[-1]  # Самое большое разрешение
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        
        # Создаем временный путь для сохранения
        try:
            local_file = create_simple_file_path(user_id, f"photo_{photo.file_id[:8]}.jpg")
        except ValueError as e:
            # Локализуем ошибки файловой системы
            error_key = {
                "Empty filename": "file_empty_name_error",
                "Invalid filename: contains dangerous characters": "file_invalid_name_error", 
                "Filename too long": "file_name_too_long_error",
                "File path outside allowed directory": "file_path_security_error",
            }.get(str(e), "file_creation_error")
            
            await message.answer(t(error_key, lang))
            return
        except Exception as e:
            await message.answer(t("file_creation_error", lang))
            return
        
        # Скачиваем файл
        await bot.download_file(file_path, destination=local_file)
        
        # Проверяем размер
        if not validate_file_size(local_file):
            os.remove(local_file)
            await message.answer(t("photo_too_large", lang))
            return
        
        # Сохраняем путь к фото в состоянии пользователя
        user_states[user_id] = {
            "type": "awaiting_photo_question",
            "photo_path": local_file,
            "photo_file_id": photo.file_id
        }
        
        # Спрашиваем вопрос
        await message.answer(
            f"{t('photo_saved_for_analysis', lang)}\n\n"
            f"{t('photo_question_prompt', lang)}\n\n"
            f"{t('photo_question_examples', lang)}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("cancel_analysis", lang), callback_data="cancel_photo_analysis")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке фото")
        await message.answer(t("photo_analysis_error", lang))
        # Очищаем состояние
        if user_id in user_states:
            user_states[user_id] = None

async def handle_photo_question(message: types.Message, bot):
    """
    Обработка вопроса пользователя к фото
    
    Args:
        message: Сообщение с вопросом
        bot: Экземпляр бота
    """
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        # Получаем состояние пользователя
        state = user_states.get(user_id)
        if not state or state.get("type") != "awaiting_photo_question":
            await message.answer(t("photo_state_not_found", lang))
            return
        
        photo_path = state.get("photo_path")
        user_question = message.text
        
        if not photo_path or not os.path.exists(photo_path):
            await message.answer(t("photo_file_not_found", lang))
            user_states[user_id] = None
            return
        
        # ✅ ВАЖНО: Сохраняем вопрос пользователя в историю сообщений
        from db_postgresql import save_message
        await save_message(user_id, "user", user_question)
        
        # Отправляем сообщение о начале анализа
        processing_msg = await message.answer(
            t("photo_analyzing", lang)
            # ✅ УБИРАЕМ reply_markup=types.ReplyKeyboardRemove() чтобы клавиатура не пропадала
        )
        
        # Собираем контекст пользователя
        context = await prepare_user_context(user_id, lang)
        
        # Создаем промпт с вопросом пользователя
        custom_prompt = create_photo_analysis_prompt(user_question, context, lang)
        
        # Отправляем на анализ в Gemini
        analysis_result, error_message = await send_to_gemini_vision(
            photo_path, lang, custom_prompt
        )
        
        # Удаляем сообщение о процессе
        try:
            await bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            pass
        
        if error_message:
            await message.answer(t("photo_analysis_error_detail", lang, error=error_message))
            return
        
        if not analysis_result:
            await message.answer(t("photo_analysis_failed", lang))
            return
                
        # ✅ ВАЖНО: Очищаем состояние ДО отправки ответа
        await cleanup_photo_analysis(user_id, photo_path)
        
        # Отправляем результат анализа
        await send_analysis_result(message, analysis_result, lang)
        await spend_gpt4o_limit(user_id, message, bot)
        # ✅ ВАЖНО: Сохраняем ответ бота в историю чата
        from db_postgresql import save_message
        await save_message(user_id, "assistant", f"Image analysis: {analysis_result}")
        
    except Exception as e:
        logger.error(f"Ошибка при анализе фото")
        await message.answer(t("photo_analysis_general_error", lang))
        await cleanup_photo_analysis(user_id, photo_path if 'photo_path' in locals() else None)

async def prepare_user_context(user_id: int, lang: str) -> str:
    """
    Подготавливает контекст пользователя для анализа
    """
    try:
        # ✅ ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩИЕ ФУНКЦИИ
        from save_utils import format_user_profile
        from db_postgresql import get_last_messages
        
        # Получаем профиль пользователя (как в основном чате)
        profile_text = await format_user_profile(user_id)
        
        # Получаем последние сообщения (как в основном чате)
        recent_messages = await get_last_messages(user_id, limit=6)
        
        # Форматируем недавние сообщения
        context_lines = []
        for msg in recent_messages:
            if isinstance(msg, (tuple, list)) and len(msg) >= 2:
                role = "USER" if msg[0] == 'user' else "BOT"
                content = str(msg[1])[:100]  # Ограничиваем длину
                context_lines.append(f"{role}: {content}")
        
        context_text = "\n".join(context_lines) if context_lines else "Нет недавних сообщений"
        
        # Объединяем профиль и контекст
        context_parts = []
        if profile_text and profile_text != "Профиль пациента не заполнен":
            context_parts.append(f"📌 Профиль пациента:\n{profile_text}")
        
        if context_text and context_text != "Нет недавних сообщений":
            context_parts.append(f"💬 Недавние сообщения:\n{context_text}")
        
        return "\n\n".join(context_parts) if context_parts else "Нет дополнительного контекста"
        
    except Exception as e:
        logger.error(f"Ошибка подготовки контекста для пользователя")
        return "Нет дополнительного контекста"

def create_photo_analysis_prompt(user_question: str, context: str, lang: str) -> str:
    """
    Создает промпт для анализа фото с учетом вопроса пользователя
    
    Args:
        user_question: Вопрос пользователя
        context: Контекст пользователя
        lang: Язык ответа
        
    Returns:
        str: Готовый промпт
    """
    lang_names = {
        'ru': 'Russian',
        'uk': 'Ukrainian', 
        'en': 'English',
        'de': 'German' 
    }
    response_language = lang_names.get(lang, 'Russian')
    
    return f"""You are an experienced medical consultant analyzing images.

USER QUESTION: "{user_question}"

USER CONTEXT:
{context}

INSTRUCTIONS:
1. Analyze the image in the context of the user's specific question
2. Consider the provided user information when giving recommendations  
3. Give a comprehensive but understandable answer
4. If this appears to be a medical condition, suggest whether medical consultation is needed
5. Be supportive and informative, but avoid definitive diagnoses
6. Always respond in {response_language} language

Focus your analysis specifically on answering the user's question while considering their medical context."""

async def send_analysis_result(message: types.Message, analysis_result: str, lang: str):
    """
    Отправляет результат анализа пользователю
    
    Args:
        message: Сообщение пользователя
        analysis_result: Результат анализа
        lang: Язык пользователя
    """
    try:
        # Добавляем заголовок к результату
        result_text = f"{t('photo_analysis_result', lang)}\n\n{analysis_result}"
        
        # Если текст слишком длинный, разбиваем на части
        if len(result_text) > 4000:
            # Отправляем первую часть с заголовком
            await message.answer(result_text[:4000] + "...", parse_mode="HTML")
            
            # Отправляем остальные части
            remaining_text = result_text[4000:]
            while remaining_text:
                chunk = remaining_text[:4000]
                remaining_text = remaining_text[4000:]
                await message.answer(chunk, parse_mode="HTML")
        else:
            await message.answer(result_text, parse_mode="HTML")
        
        # ✅ Убираем disclaimer - ИИ и так пишет про консультацию врача
        
    except Exception as e:
        logger.error(f"Ошибка отправки результата анализа")
        await message.answer(t("analysis_complete_send_error", lang))

async def cleanup_photo_analysis(user_id: int, photo_path: Optional[str] = None):
    """
    Очищает временные файлы и состояние после анализа
    
    Args:
        user_id: ID пользователя
        photo_path: Путь к временному файлу фото
    """
    try:
        # Очищаем состояние пользователя
        user_states[user_id] = None
        
        # Удаляем временный файл
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            
    except Exception as e:
        logger.error(f"Ошибка очистки после анализа фото")

async def cancel_photo_analysis(callback_query: types.CallbackQuery):
    """
    Отменяет анализ фото по запросу пользователя
    
    Args:
        callback_query: Callback query отмены
    """
    user_id = callback_query.from_user.id
    lang = await get_user_language(user_id)
    
    try:
        state = user_states.get(user_id)
        photo_path = None
        
        if state and state.get("type") == "awaiting_photo_question":
            photo_path = state.get("photo_path")
        
        await cleanup_photo_analysis(user_id, photo_path)
        
        await callback_query.message.edit_text(
            t("photo_analysis_canceled", lang),
            reply_markup=None
        )
        
        await callback_query.answer(t("canceled", lang))
        
    except Exception as e:
        logger.error(f"Ошибка отмены анализа фото")
        await callback_query.answer("Ошибка отмены")