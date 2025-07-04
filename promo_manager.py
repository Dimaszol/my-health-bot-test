# promo_manager.py
"""
🎯 Система промокодов для медицинского бота

Показывает специальное предложение новым пользователям на 30-м сообщении
с большими скидками на подписки через Stripe промокоды.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

class PromoManager:
    """Менеджер промокодов для новых пользователей"""
    
    # 🎫 Конфигурация промокодов (соответствует настройкам в Stripe)
    PROMO_CODES = {
        "basic_special": {
            "stripe_code": "basic_first_30",      # Промокод в Stripe
            "original_price": "$3.99",          # Обычная цена
            "promo_price": "$0.99",             # Цена со скидкой
            "package_id": "basic_sub",          # ID пакета из stripe_config.py
            "description": "Базовый план",
            "features": [
                "5 загруженных документов",
                "100 детальных консультаций", 
                "100 вопросов в день"
            ],
            "emoji": "💎"
        },
        "premium_special": {
            "stripe_code": "premium_first_30",    # Промокод в Stripe
            "original_price": "$9.99",          # Обычная цена
            "promo_price": "$1.99",             # Цена со скидкой
            "package_id": "premium_sub",        # ID пакета из stripe_config.py
            "description": "Премиум план",
            "features": [
                "20 загруженных документов",
                "400 детальных консультаций",
                "100 вопросов в день"
            ],
            "emoji": "🚀"
        }
    }
    
    @staticmethod
    async def check_and_show_promo(user_id: int, current_message_count: int) -> Optional[types.Message]:
        """
        🎯 Основная функция: проверяет, нужно ли показать промокод
        
        Args:
            user_id: ID пользователя в Telegram
            current_message_count: текущий счетчик сообщений пользователя
            
        Returns:
            Message с промокодом или None, если показывать не нужно
        """
        try:
            # 🔍 ОТЛАДОЧНЫЕ ЛОГИ
            print(f"🔍 PROMO DEBUG: User {user_id}, count = {current_message_count}")
            
            # 1️⃣ Проверяем точно 4-е сообщение (было изменено для теста)
            if current_message_count != 11:
                print(f"🔍 PROMO DEBUG: Счетчик {current_message_count} != 4, выходим")
                logger.debug(f"User {user_id}: message {current_message_count}/4 - промокод не показываем")
                return None
                
            print(f"🔍 PROMO DEBUG: Счетчик подходит! Показываем промокод!")
                
            # 2️⃣ Показываем промокод сразу (без проверки БД)!
            logger.info(f"🎉 User {user_id}: показываем промокод на 4-м сообщении!")
            return await PromoManager._send_promo_message(user_id)
            
        except Exception as e:
            print(f"🔍 PROMO DEBUG: ОШИБКА! {e}")
            logger.error(f"Ошибка проверки промокода для user {user_id}: {e}")
            return None
    
    @staticmethod
    async def _send_promo_message(user_id: int) -> Optional[types.Message]:
        """
        📨 Отправляет красивое сообщение с промокодом и кнопками
        """
        try:
            from main import bot
            from db_postgresql import get_user_language
            
            # 1️⃣ Получаем язык пользователя (убираем обновление БД)
            lang = await get_user_language(user_id)
            
            # 3️⃣ Создаем красивое сообщение с промокодом
            basic_info = PromoManager.PROMO_CODES['basic_special']
            premium_info = PromoManager.PROMO_CODES['premium_special']
            
            text = f"""🎉 <b>Специальное предложение только для Вас!</b>

🔥 Вы активный пользователь - самое время получить максимум от медицинского ассистента!

💎 <b>БАЗОВЫЙ ПЛАН</b>
<s>{basic_info['original_price']}</s> ➜ <b>{basic_info['promo_price']}</b> <i>(экономия $3.00!)</i>
{chr(10).join(['• ' + feature for feature in basic_info['features']])}

🚀 <b>ПРЕМИУМ ПЛАН</b> <i>(самый популярный!)</i>
<s>{premium_info['original_price']}</s> ➜ <b>{premium_info['promo_price']}</b> <i>(экономия $8.00!)</i>
{chr(10).join(['• ' + feature for feature in premium_info['features']])}

⚡ <i>Это предложение действует только через кнопки ниже!<\i>

🎯 Выберите свой план:"""

            # 4️⃣ Создаем кнопки с промокодами
            keyboard = InlineKeyboardBuilder()
            
            # Кнопка для Basic плана
            keyboard.button(
                text=f"{basic_info['emoji']} Базовый за {basic_info['promo_price']}",
                callback_data=f"promo_buy:basic_special"
            )
            
            # Кнопка для Premium плана  
            keyboard.button(
                text=f"{premium_info['emoji']} Премиум за {premium_info['promo_price']}", 
                callback_data=f"promo_buy:premium_special"
            )
            
            # Кнопка "Не сейчас"
            keyboard.button(
                text="⏰ Может быть позже",
                callback_data="promo_dismiss"
            )
            
            keyboard.adjust(1)  # Все кнопки в столбец
            
            # 5️⃣ Отправляем сообщение
            message = await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            
            logger.info(f"✅ User {user_id}: промокод успешно отправлен")
            return message
            
        except Exception as e:
            logger.error(f"Ошибка отправки промокода user {user_id}: {e}")
            return None
    
    @staticmethod
    async def handle_promo_purchase(callback_query: types.CallbackQuery):
        """
        💳 Обрабатывает нажатие на кнопку покупки по промокоду
        """
        try:
            # 1️⃣ Извлекаем тип промокода из callback_data
            callback_data = callback_query.data
            if ":" not in callback_data:
                await callback_query.answer("❌ Неверный формат промокода")
                return
                
            promo_type = callback_data.split(":")[1]
            promo_info = PromoManager.PROMO_CODES.get(promo_type)
            
            if not promo_info:
                await callback_query.answer("❌ Промокод не найден")
                logger.warning(f"Неизвестный промокод: {promo_type}")
                return
                
            user_id = callback_query.from_user.id
            user_name = callback_query.from_user.first_name or "Пользователь"
            
            logger.info(f"User {user_id} выбрал промокод {promo_type}")
            
            # 2️⃣ Создаем ссылку на оплату с промокодом через Stripe
            from stripe_manager import StripeManager
            
            success, result = await StripeManager.create_promo_payment_session(
                user_id=user_id,
                package_id=promo_info["package_id"],
                promo_code=promo_info["stripe_code"],
                user_name=user_name
            )
            
            # 3️⃣ Обрабатываем результат создания ссылки
            if success:
                # Успешно создали ссылку на оплату
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="💳 Перейти к оплате", url=result)
                
                # Обновляем сообщение с кнопкой оплаты
                savings = float(promo_info['original_price'][1:]) - float(promo_info['promo_price'][1:])
                
                await callback_query.message.edit_text(
                    f"🎯 <b>Отличный выбор!</b>\n\n"
                    f"📦 <b>{promo_info['description']}</b>: {promo_info['promo_price']}\n"
                    f"💰 <b>Ваша экономия:</b> ${savings:.2f}\n\n"
                    
                    f"👇 Нажмите кнопку для оплаты со скидкой:",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="HTML"
                )
                
                await callback_query.answer("✅ Ссылка на оплату готова!")
                logger.info(f"✅ User {user_id}: создана ссылка на оплату с промокодом {promo_type}")
                
            else:
                # Ошибка создания ссылки
                await callback_query.answer(f"❌ {result}")
                logger.error(f"Ошибка создания ссылки для user {user_id}: {result}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки промокода: {e}")
            await callback_query.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    @staticmethod
    async def handle_promo_dismiss(callback_query: types.CallbackQuery):
        """
        ⏰ Обрабатывает нажатие "Может быть позже"
        """
        try:
            await callback_query.message.edit_text(
                f"💡 <b>Не проблема!</b>\n\n"
                f"🔖 Это сообщение останется в переписке - сможете воспользоваться промокодом в любое время.\n\n"
                f"🎯 Просто вернитесь сюда, когда будете готовы получить максимум от медицинского ассистента!",
                parse_mode="HTML"
            )
            
            await callback_query.answer("✅ Промокод сохранен в переписке")
            logger.info(f"User {callback_query.from_user.id}: отложил промокод")
            
        except Exception as e:
            logger.error(f"Ошибка обработки dismiss промокода: {e}")
            await callback_query.answer("✅ Окей!")

# 🔧 Функция для интеграции с существующим кодом
async def check_promo_on_message(user_id: int, message_count: int) -> Optional[types.Message]:
    """
    🎯 ГЛАВНАЯ ФУНКЦИЯ для интеграции в обработчик сообщений
    
    Эту функцию нужно вызывать в main.py при каждом сообщении пользователя
    """
    return await PromoManager.check_and_show_promo(user_id, message_count)