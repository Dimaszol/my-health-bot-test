# subscription_handlers.py - ОБНОВЛЕННАЯ ВЕРСИЯ с системой апгрейда подписок

import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from subscription_keyboards import subscription_main_menu, purchase_confirmation_keyboard, cancel_subscription_confirmation, payment_processing_keyboard, get_package_description
from subscription_manager import SubscriptionManager
from stripe_manager import StripeManager
from db_postgresql import get_user_language, get_user_name, fetch_one, t
from datetime import datetime
from error_handler import log_error_with_context

logger = logging.getLogger(__name__)

class SubscriptionHandlers:
    """Класс для обработки всех действий с подписками"""
    
    # subscription_handlers.py - ЗАМЕНИТЬ функцию show_subscription_menu

    @staticmethod
    async def show_subscription_menu(message_or_callback, user_id: int = None):
        """✅ ИСПРАВЛЕННАЯ версия с proper error handling"""
        try:
            # Определяем user_id если не передан
            if user_id is None:
                if hasattr(message_or_callback, 'from_user'):
                    user_id = message_or_callback.from_user.id
                else:
                    logger.error("Не удалось определить user_id")
                    return
            
            # Получаем язык пользователя СНАЧАЛА
            lang = await get_user_language(user_id)
            
            # ✅ ДОБАВЛЯЕМ TRY-CATCH для get_user_limits
            try:
                limits = await SubscriptionManager.get_user_limits(user_id)
            except Exception as limits_error:
                logger.error(f"Ошибка получения лимитов для пользователя {user_id}: {limits_error}")
                # ✅ FALLBACK: Создаем дефолтные лимиты
                limits = {
                    "documents_left": 0,
                    "gpt4o_queries_left": 0,
                    "subscription_type": "free",
                    "expires_at": None
                }
            
            # ✅ Проверяем что limits не None
            if not limits:
                limits = {
                    "documents_left": 0,
                    "gpt4o_queries_left": 0,
                    "subscription_type": "free",
                    "expires_at": None
                }
            
            # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Проверяем ЛОКАЛЬНУЮ БД вместо Stripe
            current_subscription = None
            has_active_subscription = False
            
            # Проверяем активные подписки в локальной БД
            try:
                active_subscription = await SubscriptionHandlers._get_active_subscription(user_id)
                
                if active_subscription:
                    # Есть активная подписка в БД
                    has_active_subscription = True
                    package_id = active_subscription['package_id']
                    current_subscription = package_id  # basic_sub, premium_sub
                    logger.info(f"Найдена активная подписка в БД: {package_id}")
            except Exception as sub_error:
                logger.error(f"Ошибка проверки подписки для пользователя {user_id}: {sub_error}")
                has_active_subscription = False
            
            # Получаем текст меню
            try:
                subscription_text = await SubscriptionHandlers._get_subscription_menu_text(
                    user_id, lang, limits, has_active_subscription
                )
            except Exception as text_error:
                logger.error(f"Ошибка генерации текста меню для пользователя {user_id}: {text_error}")
                # ✅ FALLBACK текст
                subscription_text = t("subscription_menu_title", lang) + "\n\n" + t("subscription_menu_error", lang)
            
            # Создаем клавиатуру с правильным current_subscription
            try:
                from subscription_keyboards import subscription_main_menu
                keyboard = subscription_main_menu(lang, current_subscription)
            except Exception as keyboard_error:
                logger.error(f"Ошибка создания клавиатуры для пользователя {user_id}: {keyboard_error}")
                # ✅ FALLBACK: Простая кнопка назад
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t("back_to_settings", lang), callback_data="back_to_settings")]
                ])
            
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
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(user_id)
            except:
                lang = "ru"
            
            # ✅ ПОКАЗЫВАЕМ ПОНЯТНУЮ ОШИБКУ ПОЛЬЗОВАТЕЛЮ
            error_text = t("subscription_menu_error", lang)
            
            # Простая кнопка назад
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("back_to_settings", lang), callback_data="back_to_settings")]
            ])
            
            if isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.message.edit_text(
                    error_text,
                    reply_markup=back_keyboard
                )
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(
                    error_text,
                    reply_markup=back_keyboard
                )
    
    @staticmethod
    async def _get_subscription_menu_text(user_id: int, lang: str, limits: dict, has_real_subscription: bool) -> str:
        """✅ ЛОКАЛИЗОВАННАЯ версия - использует t() вместо словарей"""
        
        # ✅ ИМПОРТИРУЕМ функцию локализации
        from db_postgresql import t
        
        # ✅ УБИРАЕМ весь словарь texts - теперь получаем переводы через t()
        
        # Начинаем с заголовка
        text_parts = [t("subscription_menu_title", lang)]
        
        # Добавляем информацию о текущих лимитах
        if limits:
            text_parts.append(t("subscription_current_limits", lang))
            text_parts.append(f"• {t('subscription_documents', lang)}: <b>{limits['documents_left']}</b>")
            text_parts.append(f"• {t('subscription_queries', lang)}: <b>{limits['gpt4o_queries_left']}</b>\n")
            text_parts.append(f"• {t('limits_usage_info', lang)}")
            
            # ✅ ИСПРАВЛЕНИЕ: Информация о подписке на основе РЕАЛЬНОГО состояния
            if has_real_subscription:
                text_parts.append(f"• {t('subscription_type', lang)}: <b>{t('subscription_active', lang)}</b>")
                if limits.get('expires_at'):
                    try:
                        from datetime import datetime
                        expires_at_value = limits['expires_at']
                        if isinstance(expires_at_value, str):
                            expiry_date = datetime.fromisoformat(expires_at_value.replace('Z', '+00:00'))
                        else:
                            expiry_date = expires_at_value
                        formatted_date = expiry_date.strftime("%d.%m.%Y")
                        text_parts.append(f"• {t('subscription_expires', lang)}: <b>{formatted_date}</b>")
                    except:
                        pass
            else:
                text_parts.append(f"• {t('subscription_type', lang)}: <b>{t('subscription_free', lang)}</b>")
        
        # Добавляем призыв к действию
        text_parts.append(t("subscription_choose", lang))
        
        # Добавляем уведомление о синхронизации
        text_parts.append(t("subscription_sync_note", lang))
        
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
            await callback.message.edit_text(
                t("purchase_confirmation_title", lang, package_description=package_description),
                reply_markup=purchase_confirmation_keyboard(package_id, lang),
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"
            
            await callback.answer(t("purchase_request_error", lang), show_alert=True)
    
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
        """✅ ИСПРАВЛЕННАЯ ФУНКЦИЯ: Показывает предупреждение об апгрейде подписки"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            current_package = active_subscription['package_id']
            
            # ✅ ИСПРАВЛЕНО: Используем функции локализации вместо прямого поля
            from stripe_config import StripeConfig
            
            # Получаем локализованные названия пакетов
            current_name = StripeConfig.get_localized_package_name(current_package, lang)
            new_name = StripeConfig.get_localized_package_name(new_package_id, lang)
            
            # Получаем информацию о ценах
            current_info = StripeConfig.get_package_info(current_package)
            new_info = StripeConfig.get_package_info(new_package_id)
            
            if not current_info or not new_info:
                logger.error(f"Не найдена информация о пакетах: {current_package}, {new_package_id}")
                await callback.answer(t("upgrade_warning_error", lang), show_alert=True)
                return
            
            # ✅ ИСПРАВЛЕНО: Используем локализованные названия
            warning_text = t("subscription_upgrade_warning", lang,
                current_name=current_name,
                current_price=current_info['price_display'],
                new_name=new_name,
                new_price=new_info['price_display'])
            
            # Создаем клавиатуру подтверждения апгрейда
            upgrade_keyboard = SubscriptionHandlers._create_upgrade_confirmation_keyboard(
                new_package_id, current_package, lang
            )
            
            await callback.message.edit_text(
                warning_text,
                reply_markup=upgrade_keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка показа предупреждения об апгрейде: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"  # Fallback на русский
            
            await callback.answer(t("upgrade_warning_error", lang), show_alert=True)
    
    @staticmethod
    def _create_upgrade_confirmation_keyboard(new_package_id: str, current_package_id: str, lang: str) -> InlineKeyboardMarkup:
        """✅ Создает клавиатуру подтверждения апгрейда"""
        
        # ✅ ПРАВИЛЬНО: Получаем переводы через t()
        confirm_text = t("upgrade_confirm", lang)
        cancel_text = t("upgrade_cancel", lang)
        
        # ✅ ПРАВИЛЬНО: Используем полученные переводы
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=confirm_text,  # ✅ Используем переменную confirm_text
                callback_data=f"upgrade_to_{new_package_id}"
            )],
            [InlineKeyboardButton(
                text=cancel_text,   # ✅ Используем переменную cancel_text
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
            await callback.message.edit_text(
                t("processing_subscription_upgrade", lang),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
            
            # 1. Отменяем старую подписку в Stripe
            cancel_success = await SubscriptionHandlers._cancel_old_subscription(user_id)
            
            if not cancel_success:
                await callback.message.edit_text(
                    t("upgrade_cancel_old_error", lang),
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
                await callback.message.edit_text(
                    t("upgrade_success", lang, payment_url=payment_url_or_error),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            else:
                await callback.message.edit_text(
                    t("upgrade_partial_error", lang, error=payment_url_or_error),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML"
                )
            
        except Exception as e:
            logger.error(f"Ошибка апгрейда подписки для пользователя {callback.from_user.id}: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"

            await callback.message.edit_text(
                t("upgrade_general_error", lang),
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
            from db_postgresql import execute_query
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
            await callback.message.edit_text(
                t("creating_payment_link", lang),
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
                await callback.message.edit_text(
                    t("payment_link_created", lang, payment_url=payment_url_or_error),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                
            else:
                # Ошибка создания ссылки
                await callback.message.edit_text(
                    t("payment_link_error", lang, error=payment_url_or_error),
                    reply_markup=payment_processing_keyboard(lang),
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Ошибка подтверждения покупки {package_id} для пользователя {callback.from_user.id}: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"
            
            await callback.message.edit_text(
                t("payment_link_general_error", lang),
                reply_markup=payment_processing_keyboard(lang)
            )
            await callback.answer()
    
    @staticmethod
    async def handle_cancel_subscription_request(callback: types.CallbackQuery):
        """Обрабатывает запрос на отмену подписки (без изменений)"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            # Проверяем есть ли активная подписка
            limits = await SubscriptionManager.get_user_limits(user_id)
            
            if not limits or limits['subscription_type'] != 'subscription':
                await callback.answer(t("no_subscription_to_cancel", lang), show_alert=True)
                return
            
            # Показываем предупреждение об отмене
            await callback.message.edit_text(
                t("cancel_subscription_warning", lang),
                reply_markup=cancel_subscription_confirmation(lang),
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка запроса отмены подписки для пользователя {callback.from_user.id}: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"
            
            await callback.answer(t("request_processing_error", lang), show_alert=True)
    
    @staticmethod
    async def handle_cancel_subscription_confirmation(callback: types.CallbackQuery):
        """Обрабатывает подтверждение отмены подписки"""
        try:
            user_id = callback.from_user.id
            lang = await get_user_language(user_id)
            
            # Отменяем подписку
            success, message = await StripeManager.cancel_user_subscription(user_id)
            
            if success:
                success_text = t("subscription_cancelled_success", lang, message=message)
            else:
                success_text = t("subscription_cancel_error", lang, message=message)
            
            # Создаем кнопку возврата в меню
            back_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=t("back_to_subscriptions", lang),
                    callback_data="subscription_menu"
                )]
            ])
            
            # ✅ ИСПРАВЛЕНО: Убрали .get() у строки
            await callback.message.edit_text(
                success_text,  # ✅ ПРАВИЛЬНО: это строка, не словарь
                reply_markup=back_button,
                parse_mode="HTML"
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения отмены подписки для пользователя {callback.from_user.id}: {e}")
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЯЗЫКА
            try:
                lang = await get_user_language(callback.from_user.id)
            except:
                lang = "ru"  # Fallback на русский
            
            await callback.answer(t("subscription_cancel_error_short", lang), show_alert=True)
    
    @staticmethod
    async def show_subscription_upsell(message, user_id: int, reason: str = "limits_exceeded"):
        """✅ ИСПРАВЛЕННАЯ версия - использует только locales.py"""
        try:
            from db_postgresql import t  # ✅ Используем общую систему переводов
            from subscription_keyboards import subscription_upsell_keyboard
            
            lang = await get_user_language(user_id)
            
            # ✅ ЕДИНСТВЕННЫЙ ИСТОЧНИК ПРАВДЫ - locales.py
            text = t(reason, lang)  # Получаем текст из locales.py
            
            await message.answer(
                text,
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
# В файл subscription_handlers.py ЗАМЕНИТЬ весь класс UpsellTracker:

class UpsellTracker:
    """Отслеживает показ upsell сообщений пользователям"""
    
    def __init__(self):
        self.user_message_counts = {}  # user_id: count
        self.user_last_upsell = {}     # user_id: timestamp
        self.user_summary_counts = {}  # user_id: count обновлений сводки
    
    def should_show_upsell(self, user_id: int) -> bool:
        """Определяет, нужно ли показать upsell сообщение"""
        current_count = self.user_message_counts.get(user_id, 0)
        
        # ✅ ИЗМЕНЯЕМ: показываем каждые 7 сообщений (вместо 5)
        if current_count >= 7:
            self.user_message_counts[user_id] = 0  # Сбрасываем счетчик
            self.user_last_upsell[user_id] = datetime.now().timestamp()
            return True
        
        return False
    
    def should_show_upsell_on_summary(self, user_id: int) -> bool:
        """
        ✅ НОВОЕ: Определяет, нужно ли показать upsell при обновлении сводки
        """
        current_count = self.user_summary_counts.get(user_id, 0)
        
        # Показываем каждое 3-е обновление сводки
        if current_count >= 3:
            self.user_summary_counts[user_id] = 0  # Сбрасываем счетчик
            return True
        
        return False
    
    def increment_message_count(self, user_id: int):
        """Увеличивает счетчик сообщений пользователя"""
        self.user_message_counts[user_id] = self.user_message_counts.get(user_id, 0) + 1
    
    def increment_summary_count(self, user_id: int):
        """
        ✅ НОВОЕ: Увеличивает счетчик обновлений сводки
        """
        self.user_summary_counts[user_id] = self.user_summary_counts.get(user_id, 0) + 1
    
    def reset_count(self, user_id: int):
        """Сбрасывает счетчики для пользователя (например, после покупки подписки)"""
        self.user_message_counts[user_id] = 0
        self.user_summary_counts[user_id] = 0
        if user_id in self.user_last_upsell:
            del self.user_last_upsell[user_id]

# Глобальный экземпляр трекера
upsell_tracker = UpsellTracker()