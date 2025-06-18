# subscription_handlers.py - ОБНОВЛЕННАЯ ВЕРСИЯ с системой апгрейда подписок

import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from subscription_keyboards import (
    subscription_main_menu, purchase_confirmation_keyboard,
    subscription_upsell_keyboard, cancel_subscription_confirmation,
    payment_processing_keyboard, get_package_description
)
from subscription_manager import SubscriptionManager
from stripe_manager import StripeManager
from db_postgresql import get_user_language, get_user_name, fetch_one
from datetime import datetime
from error_handler import log_error_with_context

logger = logging.getLogger(__name__)

class SubscriptionHandlers:
    """Класс для обработки всех действий с подписками"""
    
    # subscription_handlers.py - ЗАМЕНИТЬ функцию show_subscription_menu

    @staticmethod
    async def show_subscription_menu(message_or_callback, user_id: int = None):
        """✅ ИСПРАВЛЕННАЯ версия с правильными параметрами"""
        try:
            # Определяем user_id если не передан
            if user_id is None:
                if hasattr(message_or_callback, 'from_user'):
                    user_id = message_or_callback.from_user.id
                else:
                    logger.error("Не удалось определить user_id")
                    return
            
            # Получаем язык и лимиты пользователя
            lang = await get_user_language(user_id)
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Проверяем РЕАЛЬНОЕ состояние в Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            has_real_subscription = stripe_check["has_active"]
            
            # ✅ НОВАЯ ЛОГИКА: Определяем текущую подписку на основе Stripe, а не БД
            current_subscription = None
            if has_real_subscription:
                # Есть РЕАЛЬНАЯ активная подписка в Stripe
                if limits and limits['documents_left'] >= 20:  # Premium
                    current_subscription = "premium_sub"
                elif limits and limits['documents_left'] >= 5:   # Basic
                    current_subscription = "basic_sub"
            # Если нет активной подписки в Stripe - current_subscription остается None
            
            logger.info(f"Меню подписок для {user_id}: Stripe={has_real_subscription}, current_sub={current_subscription}")
            
            # ✅ ИСПРАВЛЕНИЕ: Передаем правильное количество параметров
            subscription_text = await SubscriptionHandlers._get_subscription_menu_text(
                user_id, lang, limits, has_real_subscription
            )
            
            # Создаем клавиатуру с правильным current_subscription
            keyboard = subscription_main_menu(lang, current_subscription)
            
            # Отправляем или редактируем сообщение
            if isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.message.edit_text(
                    subscription_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(
                    subscription_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка показа меню подписок для пользователя {user_id}: {e}")
            
            # ✅ ДОБАВЛЕНО: Показываем ошибку пользователю для отладки
            error_text = f"❌ Ошибка меню подписок: {str(e)[:200]}"
            
            if isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.message.answer(error_text)
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(error_text)
    
    @staticmethod
    async def _get_subscription_menu_text(user_id: int, lang: str, limits: dict, has_real_subscription: bool) -> str:
        """✅ ОБНОВЛЕННАЯ версия - учитывает реальное состояние Stripe"""
        
        texts = {
            "ru": {
                "title": "💎 <b>Подписки и лимиты</b>",
                "current_limits": "\n📊 <b>Ваши текущие лимиты:</b>",
                "documents": "📄 Документы",
                "queries": "🤖 GPT-4o запросы", 
                "subscription": "💳 Подписка",
                "expires": "⏰ Истекает",
                "free": "Бесплатная",
                "choose": "\n🛒 <b>Выберите подписку:</b>",
                "sync_note": "\n🔄 <i>Данные синхронизированы с платежной системой</i>"
            },
            "uk": {
                "title": "💎 <b>Підписки та ліміти</b>",
                "current_limits": "\n📊 <b>Ваші поточні ліміти:</b>",
                "documents": "📄 Документи",
                "queries": "🤖 GPT-4o запити",
                "subscription": "💳 Підписка", 
                "expires": "⏰ Закінчується",
                "free": "Безкоштовна",
                "choose": "\n🛒 <b>Оберіть підписку:</b>",
                "sync_note": "\n🔄 <i>Дані синхронізовані з платіжною системою</i>"
            },
            "en": {
                "title": "💎 <b>Subscriptions and limits</b>",
                "current_limits": "\n📊 <b>Your current limits:</b>",
                "documents": "📄 Documents", 
                "queries": "🤖 GPT-4o queries",
                "subscription": "💳 Subscription",
                "expires": "⏰ Expires",
                "free": "Free",
                "choose": "\n🛒 <b>Choose subscription:</b>",
                "sync_note": "\n🔄 <i>Data synchronized with payment system</i>"
            }
        }
        
        t = texts.get(lang, texts["ru"])
        
        # Начинаем с заголовка
        text_parts = [t["title"]]
        
        # Добавляем информацию о текущих лимитах
        if limits:
            text_parts.append(t["current_limits"])
            text_parts.append(f"• {t['documents']}: <b>{limits['documents_left']}</b>")
            text_parts.append(f"• {t['queries']}: <b>{limits['gpt4o_queries_left']}</b>")
            
            # ✅ ИСПРАВЛЕНИЕ: Информация о подписке на основе РЕАЛЬНОГО состояния
            if has_real_subscription:
                text_parts.append(f"• {t['subscription']}: <b>✅ Активная</b>")
                if limits.get('expires_at'):
                    try:
                        from datetime import datetime
                        expires_at_value = limits['expires_at']
                        if isinstance(expires_at_value, str):
                            expiry_date = datetime.fromisoformat(expires_at_value.replace('Z', '+00:00'))
                        else:
                            expiry_date = expires_at_value
                        formatted_date = expiry_date.strftime("%d.%m.%Y")
                        text_parts.append(f"• {t['expires']}: <b>{formatted_date}</b>")
                    except:
                        pass
            else:
                text_parts.append(f"• {t['subscription']}: <b>{t['free']}</b>")
        
        # Добавляем призыв к действию
        text_parts.append(t["choose"])
        
        # Добавляем уведомление о синхронизации
        text_parts.append(t["sync_note"])
        
        return "\n".join(text_parts)
    
    @staticmethod
    async def handle_purchase_request(callback: types.CallbackQuery, package_id: str):
        """✅ ИСПРАВЛЕНО: Обрабатывает запрос на покупку с правильной проверкой активных подписок"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            user_name = await get_user_name(user_id) or callback.from_user.first_name or "User"
            
            # ✅ ИСПРАВЛЕНО: Проверяем РЕАЛЬНЫЕ активные подписки в БД
            active_subscription = await SubscriptionHandlers._get_active_subscription(user_id)
            
            # ✅ ВАЖНО: Показываем апгрейд только если:
            # 1. Есть активная подписка в БД
            # 2. И покупается другая подписка (не Extra Pack)
            if (active_subscription and 
                package_id in ['basic_sub', 'premium_sub'] and 
                active_subscription['package_id'] != package_id):
                
                # У пользователя есть ДРУГАЯ активная подписка
                await SubscriptionHandlers._show_upgrade_warning(
                    callback, package_id, active_subscription
                )
                return
            
            # ✅ Если нет активной подписки ИЛИ покупается та же самая ИЛИ это Extra Pack
            # - продолжаем как обычную покупку
            package_description = get_package_description(package_id, lang)
            
            # Показываем подтверждение покупки
            confirmation_text = {
                "ru": f"🛒 <b>Подтверждение покупки</b>\n\n{package_description}\n\n💳 Нажмите 'Оплатить' для перехода к безопасной оплате через Stripe.",
                "uk": f"🛒 <b>Підтвердження покупки</b>\n\n{package_description}\n\n💳 Натисніть 'Сплатити' для переходу до безпечної оплати через Stripe.",
                "en": f"🛒 <b>Purchase confirmation</b>\n\n{package_description}\n\n💳 Click 'Pay' to proceed to secure payment via Stripe."
            }
            
            await callback.message.edit_text(
                confirmation_text.get(lang, confirmation_text["en"]),
                reply_markup=purchase_confirmation_keyboard(package_id, lang),
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            # ✅ ИСПРАВЛЕНО: Используем существующую систему логирования
            logger.error(f"Ошибка: {e}")
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    
    @staticmethod
    async def _get_active_subscription(user_id: int) -> dict:
        """✅ НОВАЯ ФУНКЦИЯ: Получает информацию об активной подписке пользователя"""
        try:
            subscription_data = await fetch_one("""
                SELECT stripe_subscription_id, package_id, created_at 
                FROM user_subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            if subscription_data:
                return {
                    "stripe_subscription_id": subscription_data[0],
                    "package_id": subscription_data[1],
                    "created_at": subscription_data[2]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения активной подписки для пользователя {user_id}: {e}")
            return None
    
    @staticmethod
    async def _show_upgrade_warning(callback: types.CallbackQuery, new_package_id: str, active_subscription: dict):
        """✅ НОВАЯ ФУНКЦИЯ: Показывает предупреждение об апгрейде подписки"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            current_package = active_subscription['package_id']
            
            # Получаем информацию о пакетах для красивого отображения
            from stripe_config import StripeConfig
            current_info = StripeConfig.get_package_info(current_package)
            new_info = StripeConfig.get_package_info(new_package_id)
            
            # Формируем текст предупреждения
            warning_texts = {
                "ru": f"⚠️ <b>Замена подписки</b>\n\n📋 <b>Текущая подписка:</b>\n{current_info['user_friendly_name']} ({current_info['price_display']}/месяц)\n\n🔄 <b>Новая подписка:</b>\n{new_info['user_friendly_name']} ({new_info['price_display']}/месяц)\n\n💡 <b>Что произойдет:</b>\n• Текущая подписка будет отменена немедленно\n• Новая подписка активируется сразу\n• Следующее списание по новой цене\n\n❓ Продолжить замену?",
                "uk": f"⚠️ <b>Заміна підписки</b>\n\n📋 <b>Поточна підписка:</b>\n{current_info['user_friendly_name']} ({current_info['price_display']}/місяць)\n\n🔄 <b>Нова підписка:</b>\n{new_info['user_friendly_name']} ({new_info['price_display']}/місяць)\n\n💡 <b>Що станеться:</b>\n• Поточну підписку буде скасовано негайно\n• Нова підписка активується зараз\n• Наступне списання за новою ціною\n\n❓ Продовжити заміну?",
                "en": f"⚠️ <b>Subscription upgrade</b>\n\n📋 <b>Current subscription:</b>\n{current_info['user_friendly_name']} ({current_info['price_display']}/month)\n\n🔄 <b>New subscription:</b>\n{new_info['user_friendly_name']} ({new_info['price_display']}/month)\n\n💡 <b>What will happen:</b>\n• Current subscription will be cancelled immediately\n• New subscription will activate right away\n• Next billing at new price\n\n❓ Continue with upgrade?"
            }
            
            # Создаем клавиатуру подтверждения апгрейда
            upgrade_keyboard = SubscriptionHandlers._create_upgrade_confirmation_keyboard(
                new_package_id, current_package, lang
            )
            
            await callback.message.edit_text(
                warning_texts.get(lang, warning_texts["en"]),
                reply_markup=upgrade_keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка показа предупреждения об апгрейде: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)
    
    @staticmethod
    def _create_upgrade_confirmation_keyboard(new_package_id: str, current_package_id: str, lang: str) -> InlineKeyboardMarkup:
        """✅ УПРОЩЕНО: Передаем только новый пакет"""
        
        texts = {
            "ru": {
                "confirm": "✅ Да, заменить подписку",
                "cancel": "❌ Отмена"
            },
            "uk": {
                "confirm": "✅ Так, замінити підписку",
                "cancel": "❌ Скасувати"
            },
            "en": {
                "confirm": "✅ Yes, upgrade subscription",
                "cancel": "❌ Cancel"
            }
        }
        
        t = texts.get(lang, texts["en"])
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t["confirm"], 
                callback_data=f"upgrade_to_{new_package_id}"  # ✅ ПРОСТО: только новый пакет
            )],
            [InlineKeyboardButton(
                text=t["cancel"], 
                callback_data="subscription_menu"
            )]
        ])
        
    @staticmethod
    async def handle_subscription_upgrade(callback: types.CallbackQuery, current_package_id: str, new_package_id: str):
        """✅ НОВАЯ ФУНКЦИЯ: Обрабатывает подтвержденный апгрейд подписки"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            # Показываем сообщение о процессе
            processing_texts = {
                "ru": "🔄 Отменяем старую подписку и создаем новую...",
                "uk": "🔄 Скасовуємо стару підписку та створюємо нову...",
                "en": "🔄 Cancelling old subscription and creating new one..."
            }
            
            await callback.message.edit_text(
                processing_texts.get(lang, processing_texts["en"]),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
            
            # 1. Отменяем старую подписку в Stripe
            cancel_success = await SubscriptionHandlers._cancel_old_subscription(user_id)
            
            if not cancel_success:
                error_texts = {
                    "ru": "❌ Ошибка отмены старой подписки. Попробуйте позже.",
                    "uk": "❌ Помилка скасування старої підписки. Спробуйте пізніше.",
                    "en": "❌ Error cancelling old subscription. Please try later."
                }
                
                await callback.message.edit_text(
                    error_texts.get(lang, error_texts["en"]),
                    reply_markup=payment_processing_keyboard(lang)
                )
                return
            
            # 2. Создаем новую подписку
            user_name = await get_user_name(user_id) or callback.from_user.first_name or "User"
            success, payment_url_or_error = await StripeManager.create_checkout_session(
                user_id=user_id,
                package_id=new_package_id,
                user_name=user_name
            )
            
            if success:
                success_texts = {
                    "ru": f"✅ <b>Старая подписка отменена!</b>\n\n💳 <b>Ссылка для новой подписки:</b>\n🔗 <a href='{payment_url_or_error}'>Нажмите для оплаты</a>\n\n⚠️ Ссылка действительна 30 минут",
                    "uk": f"✅ <b>Стару підписку скасовано!</b>\n\n💳 <b>Посилання для нової підписки:</b>\n🔗 <a href='{payment_url_or_error}'>Натисніть для оплати</a>\n\n⚠️ Посилання дійсне 30 хвилин",
                    "en": f"✅ <b>Old subscription cancelled!</b>\n\n💳 <b>New subscription link:</b>\n🔗 <a href='{payment_url_or_error}'>Click to pay</a>\n\n⚠️ Link expires in 30 minutes"
                }
                
                await callback.message.edit_text(
                    success_texts.get(lang, success_texts["en"]),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            else:
                error_texts = {
                    "ru": f"❌ <b>Старая подписка отменена, но ошибка создания новой:</b>\n\n{payment_url_or_error}\n\nВы можете создать новую подписку через меню.",
                    "uk": f"❌ <b>Стару підписку скасовано, але помилка створення нової:</b>\n\n{payment_url_or_error}\n\nВи можете створити нову підписку через меню.",
                    "en": f"❌ <b>Old subscription cancelled, but error creating new one:</b>\n\n{payment_url_or_error}\n\nYou can create a new subscription via menu."
                }
                
                await callback.message.edit_text(
                    error_texts.get(lang, error_texts["en"]),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML"
                )
            
        except Exception as e:
            logger.error(f"Ошибка апгрейда подписки для пользователя {callback.from_user.id}: {e}")
            
            error_texts = {
                "ru": "❌ Произошла ошибка при смене подписки",
                "uk": "❌ Сталася помилка при зміні підписки",
                "en": "❌ An error occurred while changing subscription"
            }
            
            lang = await get_user_language(callback.from_user.id)
            await callback.message.edit_text(
                error_texts.get(lang, error_texts["en"]),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
    
    @staticmethod
    async def _cancel_old_subscription(user_id: int) -> bool:
        """✅ НОВАЯ ФУНКЦИЯ: Отменяет старую подписку пользователя"""
        try:
            # Получаем активную подписку
            active_subscription = await SubscriptionHandlers._get_active_subscription(user_id)
            
            if not active_subscription:
                logger.warning(f"Нет активной подписки для отмены у пользователя {user_id}")
                return True  # Если нет подписки - считаем успехом
            
            stripe_subscription_id = active_subscription['stripe_subscription_id']
            
            # Отменяем в Stripe немедленно
            import stripe
            stripe.Subscription.delete(stripe_subscription_id)
            
            # Обновляем статус в нашей БД
            from db_pool import execute_query
            await execute_query("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', cancelled_at = ?
                WHERE stripe_subscription_id = ? AND user_id = ?
            """, (datetime.now(), stripe_subscription_id, user_id))
            
            logger.info(f"✅ Подписка {stripe_subscription_id} пользователя {user_id} отменена для апгрейда")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены старой подписки для пользователя {user_id}: {e}")
            return False
    
    @staticmethod
    async def handle_purchase_confirmation(callback: types.CallbackQuery, package_id: str):
        """Обрабатывает подтверждение покупки (без изменений для обычных покупок)"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            user_name = await get_user_name(user_id) or callback.from_user.first_name or "User"
            
            # Показываем сообщение о создании ссылки
            processing_text = {
                "ru": "⏳ Создание ссылки для оплаты...",
                "uk": "⏳ Створення посилання для оплати...",
                "en": "⏳ Creating payment link..."
            }
            
            await callback.message.edit_text(
                processing_text.get(lang, processing_text["en"]),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
            
            # Создаем сессию оплаты Stripe
            success, payment_url_or_error = await StripeManager.create_checkout_session(
                user_id=user_id,
                package_id=package_id,
                user_name=user_name
            )
            
            if success:
                # Успешно создана ссылка
                success_text = {
                    "ru": f"💳 <b>Ссылка для оплаты создана!</b>\n\n🔗 <a href='{payment_url_or_error}'>Нажмите для оплаты</a>\n\n⚠️ Ссылка действительна 30 минут\n💡 После оплаты лимиты будут автоматически зачислены",
                    "uk": f"💳 <b>Посилання для оплати створено!</b>\n\n🔗 <a href='{payment_url_or_error}'>Натисніть для оплати</a>\n\n⚠️ Посилання дійсне 30 хвилин\n💡 Після оплати ліміти будуть автоматично зараховані",
                    "en": f"💳 <b>Payment link created!</b>\n\n🔗 <a href='{payment_url_or_error}'>Click to pay</a>\n\n⚠️ Link expires in 30 minutes\n💡 Limits will be automatically credited after payment"
                }
                
                await callback.message.edit_text(
                    success_text.get(lang, success_text["en"]),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                
            else:
                # Ошибка создания ссылки
                error_text = {
                    "ru": f"❌ <b>Ошибка создания ссылки для оплаты</b>\n\n{payment_url_or_error}\n\nПопробуйте еще раз или обратитесь в поддержку.",
                    "uk": f"❌ <b>Помилка створення посилання для оплати</b>\n\n{payment_url_or_error}\n\nСпробуйте ще раз або зверніться до підтримки.",
                    "en": f"❌ <b>Error creating payment link</b>\n\n{payment_url_or_error}\n\nPlease try again or contact support."
                }
                
                await callback.message.edit_text(
                    error_text.get(lang, error_text["en"]),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка подтверждения покупки {package_id} для пользователя {callback.from_user.id}: {e}")
            
            error_text = {
                "ru": "❌ Произошла ошибка при создании ссылки для оплаты",
                "uk": "❌ Сталася помилка при створенні посилання для оплати",
                "en": "❌ An error occurred while creating payment link"
            }
            
            lang = await get_user_language(callback.from_user.id)
            await callback.message.edit_text(
                error_text.get(lang, error_text["en"]),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
    
    # Остальные методы остаются без изменений...
    @staticmethod
    async def show_user_limits(callback: types.CallbackQuery):
        """Показывает подробную информацию о лимитах пользователя (без изменений)"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            if not limits:
                error_text = {
                    "ru": "❌ Не удалось загрузить информацию о лимитах",
                    "uk": "❌ Не вдалося завантажити інформацію про ліміти",
                    "en": "❌ Failed to load limits information"
                }
                await callback.answer(error_text.get(lang, error_text["en"]), show_alert=True)
                return
            
            # Формируем подробный текст о лимитах
            limits_text = await SubscriptionHandlers._get_detailed_limits_text(limits, lang)
            
            # Создаем кнопку "Назад"
            back_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⬅️ Назад" if lang == "ru" else "⬅️ Назад" if lang == "uk" else "⬅️ Back",
                    callback_data="subscription_menu"
                )]
            ])
            
            await callback.message.edit_text(
                limits_text,
                reply_markup=back_button,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка показа лимитов для пользователя {callback.from_user.id}: {e}")
            await callback.answer("❌ Ошибка загрузки лимитов", show_alert=True)
    
    @staticmethod
    async def _get_detailed_limits_text(limits: dict, lang: str) -> str:
        """Формирует подробный текст о лимитах пользователя (без изменений)"""
        
        texts = {
            "ru": {
                "title": "📊 <b>Подробная информация о лимитах</b>",
                "documents": "📄 Документы и снимки",
                "queries": "🤖 GPT-4o запросы",
                "subscription": "💳 Тип подписки",
                "expires": "⏰ Дата окончания",
                "unlimited": "♾️ Без ограничений",
                "free": "🆓 Бесплатная",
                "subscription_active": "✅ Активная подписка",
                "one_time": "📦 Разовая покупка",
                "expired": "❌ Истекла",
                "usage_info": "\n💡 <b>Как используются лимиты:</b>\n• Загрузка документов и снимков: -1 документ\n• Подробные ответы с GPT-4o: -1 запрос\n• Обычные ответы используют GPT-4o-mini (бесплатно)"
            },
            "uk": {
                "title": "📊 <b>Детальна інформація про ліміти</b>",
                "documents": "📄 Документи та знімки",
                "queries": "🤖 GPT-4o запити",
                "subscription": "💳 Тип підписки",
                "expires": "⏰ Дата закінчення",
                "unlimited": "♾️ Без обмежень",
                "free": "🆓 Безкоштовна",
                "subscription_active": "✅ Активна підписка",
                "one_time": "📦 Разова покупка",
                "expired": "❌ Закінчилася",
                "usage_info": "\n💡 <b>Як використовуються ліміти:</b>\n• Завантаження документів та знімків: -1 документ\n• Детальні відповіді з GPT-4o: -1 запит\n• Звичайні відповіді використовують GPT-4o-mini (безкоштовно)"
            },
            "en": {
                "title": "📊 <b>Detailed limits information</b>",
                "documents": "📄 Documents and scans",
                "queries": "🤖 GPT-4o queries",
                "subscription": "💳 Subscription type",
                "expires": "⏰ Expiration date",
                "unlimited": "♾️ Unlimited",
                "free": "🆓 Free",
                "subscription_active": "✅ Active subscription",
                "one_time": "📦 One-time purchase",
                "expired": "❌ Expired",
                "usage_info": "\n💡 <b>How limits are used:</b>\n• Document and scan uploads: -1 document\n• Detailed answers with GPT-4o: -1 query\n• Regular answers use GPT-4o-mini (free)"
            }
        }
        
        t = texts.get(lang, texts["ru"])
        
        # Формируем текст
        text_parts = [t["title"], ""]
        
        # Лимиты документов
        docs_left = limits.get('documents_left', 0)
        if docs_left > 999:
            docs_display = t["unlimited"]
        else:
            docs_display = f"<b>{docs_left}</b>"
        text_parts.append(f"{t['documents']}: {docs_display}")
        
        # Лимиты запросов
        queries_left = limits.get('gpt4o_queries_left', 0)
        if queries_left > 999:
            queries_display = t["unlimited"]
        else:
            queries_display = f"<b>{queries_left}</b>"
        text_parts.append(f"{t['queries']}: {queries_display}")
        
        text_parts.append("")  # Пустая строка
        
        # Тип подписки
        sub_type = limits.get('subscription_type', 'free')
        if sub_type == 'subscription':
            sub_display = t["subscription_active"]
        elif sub_type == 'one_time':
            sub_display = t["one_time"]
        else:
            sub_display = t["free"]
        
        text_parts.append(f"{t['subscription']}: {sub_display}")
        
        # Дата истечения
        expires_at = limits.get('expires_at')
        if expires_at:
            try:
                if isinstance(expires_at, str):
                    expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    expiry_date = expires_at
                if expiry_date > datetime.now():
                    formatted_date = expiry_date.strftime("%d.%m.%Y")
                    text_parts.append(f"{t['expires']}: <b>{formatted_date}</b>")
                else:
                    text_parts.append(f"{t['expires']}: {t['expired']}")
            except:
                pass
        
        # Информация об использовании
        text_parts.append(t["usage_info"])
        
        return "\n".join(text_parts)
    
    @staticmethod
    async def handle_cancel_subscription_request(callback: types.CallbackQuery):
        """Обрабатывает запрос на отмену подписки (без изменений)"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            # Проверяем есть ли активная подписка
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            if not limits or limits['subscription_type'] != 'subscription':
                no_subscription_text = {
                    "ru": "❌ У вас нет активной подписки для отмены",
                    "uk": "❌ У вас немає активної підписки для скасування",
                    "en": "❌ You don't have an active subscription to cancel"
                }
                await callback.answer(no_subscription_text.get(lang, no_subscription_text["en"]), show_alert=True)
                return
            
            # Показываем предупреждение об отмене
            cancel_warning_text = {
                "ru": "⚠️ <b>Отмена подписки</b>\n\nВы уверены, что хотите отменить подписку?\n\n📝 <b>Что произойдет:</b>\n• Автопродление будет отключено\n• Текущие лимиты останутся до конца периода\n• После окончания периода лимиты сбросятся до бесплатных\n\n💡 Вы сможете оформить подписку заново в любое время.",
                "uk": "⚠️ <b>Скасування підписки</b>\n\nВи впевнені, що хочете скасувати підписку?\n\n📝 <b>Що станеться:</b>\n• Автопродовження буде вимкнено\n• Поточні ліміти залишаться до кінця періоду\n• Після закінчення періоду ліміти скинуться до безкоштовних\n\n💡 Ви зможете оформити підписку знову в будь-який час.",
                "en": "⚠️ <b>Cancel subscription</b>\n\nAre you sure you want to cancel your subscription?\n\n📝 <b>What will happen:</b>\n• Auto-renewal will be disabled\n• Current limits will remain until the end of the period\n• After the period ends, limits will reset to free\n\n💡 You can subscribe again at any time."
            }
            
            await callback.message.edit_text(
                cancel_warning_text.get(lang, cancel_warning_text["en"]),
                reply_markup=cancel_subscription_confirmation(lang),
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка запроса отмены подписки для пользователя {callback.from_user.id}: {e}")
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
    
    @staticmethod
    async def handle_cancel_subscription_confirmation(callback: types.CallbackQuery):
        """Обрабатывает подтверждение отмены подписки (без изменений)"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            # Отменяем подписку
            success, message = await StripeManager.cancel_user_subscription(user_id)
            
            if success:
                success_text = {
                    "ru": f"✅ <b>Подписка отменена</b>\n\n{message}\n\n📊 Ваши текущие лимиты останутся активными до окончания оплаченного периода.",
                    "uk": f"✅ <b>Підписку скасовано</b>\n\n{message}\n\n📊 Ваші поточні ліміти залишаться активними до закінчення сплаченого періоду.",
                    "en": f"✅ <b>Subscription cancelled</b>\n\n{message}\n\n📊 Your current limits will remain active until the end of the paid period."
                }
            else:
                success_text = {
                    "ru": f"❌ <b>Ошибка отмены подписки</b>\n\n{message}",
                    "uk": f"❌ <b>Помилка скасування підписки</b>\n\n{message}",
                    "en": f"❌ <b>Subscription cancellation error</b>\n\n{message}"
                }
            
            # Создаем кнопку возврата в меню
            back_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⬅️ Назад к подпискам" if lang == "ru" else "⬅️ Назад до підписок" if lang == "uk" else "⬅️ Back to subscriptions",
                    callback_data="subscription_menu"
                )]
            ])
            
            await callback.message.edit_text(
                success_text.get(lang, success_text["en"]),
                reply_markup=back_button,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения отмены подписки для пользователя {callback.from_user.id}: {e}")
            await callback.answer("❌ Ошибка отмены подписки", show_alert=True)
    
    @staticmethod
    async def show_subscription_upsell(message, user_id: int, reason: str = "limits_exceeded"):
        """Обновленные upsell сообщения (без изменений)"""
        try:
            lang = await get_user_language(user_id)
            
            upsell_texts = {
                "limits_exceeded": {
                    "ru": "📄 **Лимиты исчерпаны**\n\n🔹 У вас закончились лимиты на загрузку документов или получение глубоких медицинских ответов\n\n💎 Оформите подписку для расширенных возможностей ИИ-анализа!",
                    "uk": "📄 **Ліміти вичерпано**\n\n🔹 У вас закінчилися ліміти на завантаження документів або отримання глибоких медичних відповідей\n\n💎 Оформіть підписку для розширених можливостей ШІ-аналізу!",
                    "en": "📄 **Limits exceeded**\n\n🔹 You've run out of limits for document uploads or deep medical responses\n\n💎 Get a subscription for advanced AI analysis capabilities!"
                },
                "better_response": {
                    "ru": "🤖 **Хотите более подробный ответ?**\n\n🔹 Наш продвинутый ИИ может дать более детальный и точный медицинский анализ\n\n💎 Оформите подписку для доступа к глубоким медицинским ответам!",
                    "uk": "🤖 **Хочете більш детальну відповідь?**\n\n🔹 Наш прогресивний ШІ може дати більш детальний та точний медичний аналіз\n\n💎 Оформіть підписку для доступу до глибоких медичних відповідей!",
                    "en": "🤖 **Want a more detailed response?**\n\n🔹 Our advanced AI can provide more detailed and accurate medical analysis\n\n💎 Get a subscription for access to deep medical responses!"
                }
            }
            
            text = upsell_texts.get(reason, upsell_texts["limits_exceeded"])
            
            await message.answer(
                text.get(lang, text["en"]),
                reply_markup=subscription_upsell_keyboard(lang),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа upsell сообщения для пользователя {user_id}: {e}")
    
    @staticmethod
    async def dismiss_upsell(callback: types.CallbackQuery):
        """Закрывает upsell сообщение (без изменений)"""
        try:
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка закрытия upsell сообщения: {e}")
            await callback.answer()

# Система отслеживания upsell сообщений (без изменений)
class UpsellTracker:
    """Отслеживает показ upsell сообщений пользователям"""
    
    def __init__(self):
        self.user_message_counts = {}  # user_id: count
        self.user_last_upsell = {}     # user_id: timestamp
    
    def should_show_upsell(self, user_id: int) -> bool:
        """Определяет, нужно ли показать upsell сообщение"""
        current_count = self.user_message_counts.get(user_id, 0)
        
        # Показываем каждые 5 сообщений
        if current_count >= 5:
            self.user_message_counts[user_id] = 0  # Сбрасываем счетчик
            self.user_last_upsell[user_id] = datetime.now().timestamp()
            return True
        
        return False
    
    def increment_message_count(self, user_id: int):
        """Увеличивает счетчик сообщений пользователя"""
        self.user_message_counts[user_id] = self.user_message_counts.get(user_id, 0) + 1
    
    def reset_count(self, user_id: int):
        """Сбрасывает счетчик для пользователя (например, после покупки подписки)"""
        self.user_message_counts[user_id] = 0
        if user_id in self.user_last_upsell:
            del self.user_last_upsell[user_id]

# Глобальный экземпляр трекера
upsell_tracker = UpsellTracker()