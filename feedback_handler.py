# === ФАЙЛ: feedback_handler.py ===
# Система обратной связи через команду /support (БЕЗ дополнительных кнопок)

from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from db_postgresql import t  # ✅ ИСПРАВЛЕНО: импортируем из db_postgresql
import logging

logger = logging.getLogger(__name__)

# ID администратора (ВАШЕ! Замените на ваш Telegram ID)
ADMIN_USER_ID = 7374723347


class FeedbackStates(StatesGroup):
    """Состояния для обратной связи"""
    waiting_for_message = State()      # Ждём сообщение от пользователя
    waiting_for_admin_reply = State()  # Ждём ответ от админа


# ===================================
# ЧАСТЬ 1: Пользователь пишет в поддержку
# ===================================

async def start_feedback_from_command(message: types.Message, state: FSMContext, lang: str):
    """
    ШАГ 1: Начало процесса обратной связи через команду /support
    Вызывается когда пользователь нажимает /support в тексте
    """
    
    # Создаём клавиатуру с кнопкой "Отмена"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t("cancel_feedback", lang),  # "❌ Отмена"
                callback_data="cancel_feedback"
            )
        ]
    ])
    
    await message.answer(
        t("feedback_prompt", lang),  # "📝 Напишите ваше сообщение..."
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние ожидания сообщения
    await state.set_state(FeedbackStates.waiting_for_message)
    
    logger.info(f"Пользователь {message.from_user.id} начал обращение в поддержку через команду")


async def cancel_feedback(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """
    ШАГ 1.1: Отмена отправки сообщения (если пользователь передумал)
    """
    await state.clear()  # Сбрасываем состояние
    
    await callback.message.edit_text(
        t("feedback_cancelled", lang),  # "❌ Отправка сообщения отменена"
        parse_mode="HTML"
    )
    await callback.answer()
    
    logger.info(f"Пользователь {callback.from_user.id} отменил обращение в поддержку")


async def receive_feedback_message(message: types.Message, state: FSMContext, bot: Bot, lang: str):
    """
    ШАГ 2: Получение сообщения от пользователя и пересылка админу с кнопкой "Ответить"
    
    Аргументы:
    - message: сообщение пользователя
    - state: состояние FSM
    - bot: экземпляр бота для отправки админу
    - lang: язык пользователя
    """
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    first_name = message.from_user.first_name or "не указано"
    
    # ===== ШАГ 2.1: Формируем сообщение для админа =====
    admin_message = f"""📨 <b>НОВОЕ ОБРАЩЕНИЕ В ПОДДЕРЖКУ</b>

👤 <b>От пользователя:</b>
• ID: <code>{user_id}</code>
• Username: @{username}
• Имя: {first_name}

💬 <b>Сообщение:</b>
{message.text}

---
⏰ {message.date.strftime('%d.%m.%Y %H:%M')}"""
    
    # ===== ШАГ 2.2: Создаём кнопку "Ответить" для админа =====
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Ответить",
                callback_data=f"reply_to_user:{user_id}"
            )
        ]
    ])
    
    try:
        # ===== ШАГ 2.3: Отправляем админу с кнопкой =====
        await bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"Обращение от пользователя {user_id} отправлено админу")
        
        # ===== ШАГ 2.4: Подтверждаем пользователю =====
        await message.answer(
            t("feedback_sent", lang),  # "✅ Спасибо! Ваше сообщение отправлено..."
            parse_mode="HTML"
        )
        
        # ===== ШАГ 2.5: Возвращаемся в обычный режим =====
        await state.clear()
        
    except Exception as e:
        # ===== ОБРАБОТКА ОШИБОК =====
        logger.error(f"Ошибка отправки сообщения в поддержку: {e}")
        await message.answer(
            t("feedback_error", lang),  # "❌ Ошибка отправки. Попробуйте позже"
            parse_mode="HTML"
        )
        await state.clear()


# ===================================
# ЧАСТЬ 2: Админ отвечает пользователю
# ===================================

async def start_admin_reply(callback: types.CallbackQuery, state: FSMContext):
    """
    ШАГ 3: Админ нажал кнопку "Ответить" под сообщением пользователя
    Теперь ждём текст ответа от админа
    """
    
    # ===== ШАГ 3.1: Извлекаем ID пользователя из callback_data =====
    try:
        user_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
        return
    
    # ===== ШАГ 3.2: Сохраняем ID пользователя в состоянии =====
    await state.update_data(target_user_id=user_id)
    await state.set_state(FeedbackStates.waiting_for_admin_reply)
    
    # ===== ШАГ 3.3: Создаём кнопку "Отмена" для админа =====
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_admin_reply"
            )
        ]
    ])
    
    # ===== ШАГ 3.4: Просим админа написать ответ =====
    await callback.message.answer(
        f"📝 <b>Напишите ответ пользователю {user_id}</b>\n\n"
        f"Ваш ответ будет отправлен ему автоматически.",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )
    
    await callback.answer()
    logger.info(f"Админ начал отвечать пользователю {user_id}")


async def cancel_admin_reply(callback: types.CallbackQuery, state: FSMContext):
    """
    ШАГ 3.1: Отмена ответа (если админ передумал отвечать)
    """
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Ответ отменён",
        parse_mode="HTML"
    )
    await callback.answer()
    
    logger.info("Админ отменил ответ пользователю")


async def send_admin_reply_to_user(message: types.Message, state: FSMContext, bot: Bot):
    """
    ШАГ 4: Получаем текст ответа от админа и отправляем пользователю
    """
    
    # ===== ШАГ 4.1: Извлекаем ID пользователя из состояния =====
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    
    if not target_user_id:
        await message.answer("❌ Ошибка: ID пользователя не найден")
        await state.clear()
        return
    
    # ===== ШАГ 4.2: Формируем ответ для пользователя =====
    response_message = f"""🤖 <b>ОТВЕТ ОТ СЛУЖБЫ ПОДДЕРЖКИ PULSEBOOK</b>

{message.text}

---
💡 Если у вас остались вопросы, напишите команду /support снова."""
    
    try:
        # ===== ШАГ 4.3: Отправляем ответ пользователю =====
        await bot.send_message(
            chat_id=target_user_id,
            text=response_message,
            parse_mode="HTML"
        )
        
        logger.info(f"Ответ отправлен пользователю {target_user_id}")
        
        # ===== ШАГ 4.4: Подтверждаем админу =====
        await message.answer(
            f"✅ <b>Ответ успешно отправлен пользователю {target_user_id}</b>",
            parse_mode="HTML"
        )
        
        # ===== ШАГ 4.5: Сбрасываем состояние =====
        await state.clear()
        
    except Exception as e:
        # ===== ОБРАБОТКА ОШИБОК =====
        logger.error(f"Ошибка отправки ответа пользователю {target_user_id}: {e}")
        await message.answer(
            f"❌ <b>Ошибка отправки ответа:</b>\n<code>{str(e)}</code>\n\n"
            f"Возможно, пользователь заблокировал бота.",
            parse_mode="HTML"
        )
        await state.clear()