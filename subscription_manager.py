# subscription_manager.py - ПОЛНАЯ ЗАМЕНА ФАЙЛА

import stripe
import logging
from datetime import datetime, timedelta
from db_postgresql import fetch_one, execute_query

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Менеджер подписок и лимитов"""
    
    @staticmethod
    async def fix_orphaned_subscription_state(user_id: int):
        """
        ✅ НОВАЯ ФУНКЦИЯ: Исправляет "подвешенное" состояние подписки
        Когда в БД есть запись о подписке, но в Stripe её нет
        """
        try:
            logger.info(f"🔧 Исправляем состояние подписки для пользователя {user_id}")
            
            # Проверяем реальное состояние в Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            
            if not stripe_check["has_active"]:
                # В Stripe нет активной подписки - приводим БД в соответствие
                
                # 1. Обновляем статус подписок в user_subscriptions
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = ?
                    WHERE user_id = ? AND status = 'active'
                """, (datetime.now(), user_id))
                
                # 2. Получаем текущие лимиты
                limits = await fetch_one("""
                    SELECT documents_left, gpt4o_queries_left 
                    FROM user_limits 
                    WHERE user_id = ?
                """, (user_id,))
                
                if limits:
                    docs, queries = limits
                    
                    # 3. Определяем правильный subscription_type
                    if docs > 0 or queries > 0:
                        # Есть лимиты, но нет подписки - значит это разовая покупка
                        new_type = 'one_time'
                    else:
                        # Нет лимитов - значит free
                        new_type = 'free'
                    
                    # 4. Обновляем subscription_type
                    await execute_query("""
                        UPDATE user_limits 
                        SET subscription_type = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (new_type, user_id))
                    
                    logger.info(f"✅ Состояние исправлено: user_id={user_id}, type={new_type}, docs={docs}, queries={queries}")
                    return True
            else:
                logger.info(f"✅ Состояние корректно: у пользователя {user_id} есть активная подписка в Stripe")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка исправления состояния для пользователя {user_id}: {e}")
            return False

    @staticmethod
    async def check_real_stripe_subscription(user_id: int):
        """
        ✅ НОВАЯ ФУНКЦИЯ: Проверяет реальное состояние подписки в Stripe
        
        Returns:
            dict: {"has_active": bool, "subscription_id": str, "status": str}
        """
        try:
            # Получаем записи о подписках из локальной БД
            subscription_data = await fetch_one("""
                SELECT stripe_subscription_id, package_id 
                FROM user_subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            if not subscription_data:
                return {"has_active": False, "subscription_id": None, "status": "none"}
            
            stripe_subscription_id = subscription_data[0]
            
            # Проверяем статус в Stripe
            try:
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                
                if subscription.status in ['active', 'trialing']:
                    return {
                        "has_active": True, 
                        "subscription_id": stripe_subscription_id,
                        "status": subscription.status
                    }
                else:
                    # Подписка неактивна в Stripe - обновляем локальную БД
                    await SubscriptionManager._sync_inactive_subscription(user_id, stripe_subscription_id, subscription.status)
                    return {
                        "has_active": False, 
                        "subscription_id": stripe_subscription_id,
                        "status": subscription.status
                    }
                    
            except stripe.error.InvalidRequestError:
                # Подписка не найдена в Stripe - удаляем из локальной БД
                await SubscriptionManager._sync_deleted_subscription(user_id, stripe_subscription_id)
                return {"has_active": False, "subscription_id": None, "status": "deleted"}
                
        except Exception as e:
            logger.error(f"Ошибка проверки Stripe подписки для пользователя {user_id}: {e}")
            return {"has_active": False, "subscription_id": None, "status": "error"}
    
    @staticmethod
    async def _sync_inactive_subscription(user_id: int, stripe_subscription_id: str, stripe_status: str):
        """Синхронизирует неактивную подписку в локальной БД"""
        try:
            await execute_query("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', cancelled_at = ?
                WHERE user_id = ? AND stripe_subscription_id = ?
            """, (datetime.now(), user_id, stripe_subscription_id))
            
            logger.info(f"✅ Синхронизирована неактивная подписка {stripe_subscription_id} для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации неактивной подписки: {e}")
    
    @staticmethod
    async def _sync_deleted_subscription(user_id: int, stripe_subscription_id: str):
        """Удаляет несуществующую в Stripe подписку из локальной БД"""
        try:
            await execute_query("""
                DELETE FROM user_subscriptions 
                WHERE user_id = ? AND stripe_subscription_id = ?
            """, (user_id, stripe_subscription_id))
            
            logger.info(f"✅ Удалена несуществующая подписка {stripe_subscription_id} для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления несуществующей подписки: {e}")
    
    @staticmethod
    async def purchase_package(user_id: int, package_id: str, payment_method: str = 'stripe'):
        """
        ✅ ИСПРАВЛЕННАЯ версия покупки пакета - ГЛАВНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ!
        """
        try:
            # Получаем данные пакета
            package = await fetch_one("""
                SELECT name, price_usd, documents_included, gpt4o_queries_included, type
                FROM subscription_packages 
                WHERE id = $1 AND is_active = TRUE
            """, (package_id,))
            
            if not package:
                raise ValueError(f"Пакет {package_id} не найден или неактивен")
            
            name, price, docs, queries, pkg_type = package
            
            # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Проверяем реальное состояние подписки
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            has_active_subscription = stripe_check["has_active"]
            
            logger.info(f"Покупка {package_id} для пользователя {user_id}. Активная подписка: {has_active_subscription}")
            
            # Получаем текущие лимиты пользователя
            current = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_type
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not current:
                await execute_query("""
                    INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left)
                    VALUES (?, 0, 0)
                """, (user_id,))
                current_docs, current_queries, current_sub_type = 0, 0, 'free'
            else:
                current_docs, current_queries, current_sub_type = current
            
            # ✅ НОВАЯ ЛОГИКА: Определяем правильный subscription_type
            if pkg_type == 'subscription':
                # Покупка подписки - всегда устанавливаем subscription
                final_subscription_type = 'subscription'
                # Заменяем лимиты (не добавляем)
                new_docs = docs
                new_queries = queries
                logger.info(f"Подписка {package_id}: заменяем лимиты на {docs}/{queries}")
            elif has_active_subscription:
                # ✅ ГЛАВНОЕ ИСПРАВЛЕНИЕ: Есть активная подписка - НЕ МЕНЯЕМ тип
                final_subscription_type = 'subscription'  # Оставляем subscription!
                # Добавляем к текущим лимитам
                new_docs = current_docs + docs
                new_queries = current_queries + queries
                logger.info(f"Extra Pack при подписке: добавляем {docs}/{queries} к {current_docs}/{current_queries}")
            else:
                # Нет активной подписки - можно установить one_time
                final_subscription_type = 'one_time'
                # Добавляем к текущим лимитам
                new_docs = current_docs + docs
                new_queries = current_queries + queries
                logger.info(f"Extra Pack без подписки: устанавливаем one_time, добавляем {docs}/{queries}")
            
            # Устанавливаем дату истечения
            expiry_date = datetime.now() + timedelta(days=30)
            
            # Создаем транзакцию
            transaction_id = await execute_query("""
                INSERT INTO transactions 
                (user_id, package_id, amount_usd, package_type, payment_method, 
                 documents_granted, queries_granted, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
            """, (user_id, package_id, price, name, payment_method, docs, queries))
            
            # ✅ ИСПРАВЛЕННОЕ обновление лимитов
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = ?,
                    gpt4o_queries_left = ?,
                    subscription_type = ?,
                    subscription_expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (new_docs, new_queries, final_subscription_type, expiry_date, user_id))
            
            logger.info(f"✅ Пакет {package_id} куплен пользователем {user_id}. Тип: {final_subscription_type}, Новые лимиты: {new_docs} docs, {new_queries} queries")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "new_documents": new_docs,
                "new_queries": new_queries,
                "subscription_type": final_subscription_type,
                "expires_at": expiry_date
            }
            
        except Exception as e:
            logger.error(f"Ошибка покупки пакета {package_id} для пользователя {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # subscription_manager.py - ЗАМЕНИТЬ функцию cancel_stripe_subscription

    @staticmethod
    async def cancel_stripe_subscription(user_id: int):
        """
        ✅ УЛУЧШЕННАЯ версия отмены подписки
        """
        try:
            # Сначала проверяем реальное состояние в Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            
            if not stripe_check["has_active"]:
                # Подписки нет или она уже отменена
                status = stripe_check["status"]
                
                # ✅ ДОБАВЛЕНО: Исправляем подвешенное состояние
                await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                
                if status == "deleted":
                    return True, "Подписка уже была отменена ранее (данные синхронизированы)"
                elif status in ["canceled", "cancelled"]:
                    return True, "Подписка уже отменена в Stripe (данные синхронизированы)"
                else:
                    return True, "У вас нет активной подписки (данные синхронизированы)"
            
            stripe_subscription_id = stripe_check["subscription_id"]
            
            # Отменяем подписку в Stripe
            try:
                import stripe
                subscription = stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
                
                # Обновляем статус в локальной БД
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = ?
                    WHERE stripe_subscription_id = ?
                """, (datetime.now(), stripe_subscription_id))
                
                # ✅ ДОБАВЛЕНО: Исправляем subscription_type после отмены
                await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                
                logger.info(f"✅ Подписка {stripe_subscription_id} пользователя {user_id} отменена")
                
                return True, "Подписка отменена. Лимиты останутся до конца текущего периода."
                
            except stripe.error.InvalidRequestError as stripe_error:
                # Подписка уже отменена в Stripe
                if "canceled subscription" in str(stripe_error):
                    # Синхронизируем локальную БД
                    await SubscriptionManager._sync_inactive_subscription(user_id, stripe_subscription_id, "cancelled")
                    await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                    return True, "Подписка уже была отменена в Stripe (данные синхронизированы)"
                else:
                    raise stripe_error
                
        except Exception as e:
            logger.error(f"❌ Ошибка отмены подписки для пользователя {user_id}: {e}")
            return False, f"Ошибка отмены подписки: {e}"
    
    @staticmethod
    async def get_user_limits(user_id: int):
        """
        ✅ ИСПРАВЛЕННАЯ версия - БЕЗ автоматического исправления состояния
        """
        try:
            # ✅ УБИРАЕМ ЭТУ СТРОКУ:
            # await SubscriptionManager.fix_orphaned_subscription_state(user_id)
            
            # Проверяем и синхронизируем состояние подписки (оставляем как есть)
            await SubscriptionManager.check_and_reset_expired_limits(user_id)
            
            # Получаем актуальные лимиты
            result = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_type, subscription_expires_at
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not result:
                return {
                    "documents_left": 0,
                    "gpt4o_queries_left": 0,
                    "subscription_type": "free",
                    "expires_at": None
                }
            
            docs, queries, sub_type, expires_at = result
            
            return {
                "documents_left": docs,
                "gpt4o_queries_left": queries, 
                "subscription_type": sub_type,
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения лимитов для пользователя {user_id}: {e}")
            return None
    
    @staticmethod
    async def spend_limits(user_id: int, documents: int = 0, queries: int = 0):
        """
        Тратит лимиты пользователя (без изменений)
        """
        try:
            # Сначала проверяем истекшие лимиты
            await SubscriptionManager.check_and_reset_expired_limits(user_id)
            
            # Получаем текущие лимиты
            current = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left 
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not current:
                return {"success": False, "error": "Пользователь не найден"}
            
            current_docs, current_queries = current
            
            # Проверяем достаточность лимитов
            if documents > current_docs:
                return {"success": False, "error": "Недостаточно лимитов на документы"}
            
            if queries > current_queries:
                return {"success": False, "error": "Недостаточно лимитов на запросы"}
            
            # Списываем лимиты
            new_docs = current_docs - documents
            new_queries = current_queries - queries
            
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = ?,
                    gpt4o_queries_left = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (new_docs, new_queries, user_id))
            
            logger.info(f"Списаны лимиты пользователя {user_id}: -{documents} docs, -{queries} queries")
            
            return {
                "success": True,
                "remaining_documents": new_docs,
                "remaining_queries": new_queries
            }
            
        except Exception as e:
            logger.error(f"Ошибка списания лимитов для пользователя {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def check_and_reset_expired_limits(user_id: int):
        """Проверяет и сбрасывает истекшие лимиты (без изменений)"""
        try:
            user_data = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_expires_at, subscription_type
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not user_data:
                return
            
            documents_left, queries_left, expires_at, sub_type = user_data
            
            if not expires_at:
                return
            
            if isinstance(expires_at, str):
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expiry_date = expires_at
            now = datetime.now()
            
            if now >= expiry_date:
                logger.info(f"Лимиты пользователя {user_id} истекли. Тип: {sub_type}")
                
                if sub_type == 'subscription':
                    await SubscriptionManager._auto_renew_subscription(user_id)
                else:
                    await SubscriptionManager._reset_to_zero(user_id)
                    
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов для пользователя {user_id}: {e}")
    
    @staticmethod
    async def _auto_renew_subscription(user_id: int):
        """Автопродление подписки (без изменений)"""
        try:
            transaction = await fetch_one("""
                SELECT package_id, documents_granted, queries_granted
                FROM transactions 
                WHERE user_id = ? AND status = 'completed' AND package_id LIKE '%_sub'
                ORDER BY completed_at DESC LIMIT 1
            """, (user_id,))
            
            if not transaction:
                logger.warning(f"Не найдена активная подписка для пользователя {user_id}")
                await SubscriptionManager._reset_to_zero(user_id)
                return
            
            package_id, docs, queries = transaction
            new_expiry = datetime.now() + timedelta(days=30)
            
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = ?,
                    gpt4o_queries_left = ?,
                    subscription_expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (docs, queries, new_expiry, user_id))
            
            logger.info(f"Подписка пользователя {user_id} автопродлена до {new_expiry.date()}")
            
        except Exception as e:
            logger.error(f"Ошибка автопродления подписки для пользователя {user_id}: {e}")
            await SubscriptionManager._reset_to_zero(user_id)
    
    @staticmethod
    async def _reset_to_zero(user_id: int):
        """Сбрасывает лимиты до нуля (без изменений)"""
        try:
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = 0,
                    gpt4o_queries_left = 0,
                    subscription_expires_at = NULL,
                    subscription_type = 'free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            
            logger.info(f"Лимиты пользователя {user_id} сброшены до нуля")
            
        except Exception as e:
            logger.error(f"Ошибка сброса лимитов для пользователя {user_id}: {e}")

# Вспомогательные функции для интеграции в существующий код
async def check_document_limit(user_id: int) -> bool:
    """Проверяет, может ли пользователь загрузить документ"""
    limits = await SubscriptionManager.get_user_limits(user_id)
    return limits and limits["documents_left"] > 0

async def check_gpt4o_limit(user_id: int) -> bool:
    """Проверяет, может ли пользователь использовать GPT-4o"""
    limits = await SubscriptionManager.get_user_limits(user_id)
    return limits and limits["gpt4o_queries_left"] > 0

async def spend_document_limit(user_id: int) -> bool:
    """Списывает 1 документ"""
    result = await SubscriptionManager.spend_limits(user_id, documents=1)
    return result["success"]

async def spend_gpt4o_limit(user_id: int, message=None, bot=None) -> bool:
    """
    Списывает 1 GPT-4o запрос и показывает уведомление если лимиты закончились
    
    Args:
        user_id: ID пользователя
        message: Объект сообщения Telegram (опционально для уведомления)
        bot: Объект бота (опционально для уведомления)
        
    Returns:
        bool: True если лимит успешно потрачен
    """
    try:
        # ✅ ДОБАВЛЯЕМ: Получаем текущие лимиты ДО траты (для проверки перехода 1→0)
        should_notify = False
        subscription_type = 'free'
        
        if message and bot:
            current_limits = await SubscriptionManager.get_user_limits(user_id)
            current_gpt4o = current_limits.get('gpt4o_queries_left', 0)
            subscription_type = current_limits.get('subscription_type', 'free')
            print(f"💎 Лимиты до траты: {current_gpt4o}")
            
            # Запоминаем нужно ли показывать уведомление
            should_notify = (current_gpt4o == 1)
        
        # ✅ ОРИГИНАЛЬНАЯ ЛОГИКА: Тратим лимит через существующую систему
        result = await SubscriptionManager.spend_limits(user_id, queries=1)
        
        # ✅ ПРОСТОЕ РЕШЕНИЕ: Показываем уведомление сразу после ответа
        if result["success"] and should_notify:
            print(f"🚨 Лимиты закончились у пользователя {user_id}! Показываем уведомление")
            await _show_limits_exhausted_notification(user_id, message, bot, subscription_type)
        
        return result["success"]
        
    except Exception as e:
        logger.error(f"Ошибка траты лимита для пользователя {user_id}: {e}")
        return False


async def _show_limits_exhausted_notification(user_id: int, message, bot, subscription_type: str):
    """
    Показывает уведомление о том, что закончились детальные ответы
    Разные сообщения для разных типов подписки
    """
    try:
        from db_postgresql import get_user_language
        
        lang = await get_user_language(user_id)
        
        # ✅ РАЗНЫЕ СООБЩЕНИЯ ДЛЯ РАЗНЫХ СТАТУСОВ
        if subscription_type in ['free', 'one_time']:
            # Для бесплатных и разовых покупок - предлагаем подписку
            notification_texts = {
                "ru": "🤖 **Детальные ответы закончились!**\n\n"
                      "🔹 Теперь будет использоваться базовая модель для ответов\n\n"
                      "💎 Оформите подписку для возврата к детальным медицинским консультациям!",
                
                "uk": "🤖 **Детальні відповіді закінчилися!**\n\n"
                      "🔹 Тепер буде використовуватися базова модель для відповідей\n\n"
                      "💎 Оформіть підписку для повернення до детальних медичних консультацій!",
                
                "en": "🤖 **Detailed responses finished!**\n\n"
                      "🔹 Basic model will now be used for responses\n\n"
                      "💎 Get a subscription to return to detailed medical consultations!"
            }
            
            # Кнопки для подписки
            button_texts = {
                "ru": "💎 Получить подписку",
                "uk": "💎 Отримати підписку", 
                "en": "💎 Get subscription"
            }
            
            show_subscription_button = True
            
        else:  # subscription - активная подписка
            # Для пользователей с подпиской - просто информируем
            notification_texts = {
                "ru": "🤖 **Лимит детальных ответов исчерпан**\n\n"
                      "🔹 В этом месяце вы использовали все детальные ответы\n"
                      "🔹 Теперь будет использоваться базовая модель\n\n"
                      "📅 Лимиты обновятся в следующем месяце",
                
                "uk": "🤖 **Ліміт детальних відповідей вичерпано**\n\n"
                      "🔹 Цього місяця ви використали всі детальні відповіді\n"
                      "🔹 Тепер буде використовуватися базова модель\n\n"
                      "📅 Ліміти оновляться наступного місяця",
                
                "en": "🤖 **Detailed response limit exhausted**\n\n"
                      "🔹 You've used all detailed responses this month\n"
                      "🔹 Basic model will now be used\n\n"
                      "📅 Limits will refresh next month"
            }
            
            show_subscription_button = False
        
        text = notification_texts.get(lang, notification_texts["ru"])
        
        # Создаем клавиатуру только для бесплатных пользователей
        keyboard = None
        if show_subscription_button:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            button_text = button_texts.get(lang, button_texts["ru"])
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=button_text,
                    callback_data="subscription_menu"
                )]
            ])
        
        # Отправляем уведомление
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        status_msg = "с кнопкой подписки" if show_subscription_button else "без кнопки"
        print(f"✅ Уведомление об исчерпанных лимитах отправлено пользователю {user_id} ({subscription_type}, {status_msg})")
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")