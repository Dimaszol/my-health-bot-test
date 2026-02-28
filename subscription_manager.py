# subscription_manager.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ ФАЙЛ с PostgreSQL синтаксисом

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
        ✅ Исправляет "подвешенное" состояние подписки
        Когда в БД есть запись о подписке, но в Stripe её нет
        """
        try:
            logger.info("🔧 Исправляем состояние подписки")
            
            # Проверяем реальное состояние в Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            
            if not stripe_check["has_active"]:
                # В Stripe нет активной подписки - приводим БД в соответствие
                
                # 1. Обновляем статус подписок в user_subscriptions
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = $1
                    WHERE user_id = $2 AND status = 'active'
                """, (datetime.now(), user_id))
                
                # 2. Получаем текущие лимиты
                limits = await fetch_one("""
                    SELECT documents_left, gpt4o_queries_left 
                    FROM user_limits 
                    WHERE user_id = $1
                """, (user_id,))
                
                if limits:
                    docs, queries = limits
                    
                    # 3. Определяем правильный subscription_type
                    if docs > 0 or queries > 0:
                        new_type = 'one_time'
                    else:
                        new_type = 'free'
                    
                    # 4. Обновляем subscription_type
                    await execute_query("""
                        UPDATE user_limits 
                        SET subscription_type = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $2
                    """, (new_type, user_id))
                    
                    logger.info("✅ Состояние исправлено")
                    return True
            else:
                logger.info("✅ Состояние корректно: активная подписка в Stripe")
                return True
                
        except Exception as e:
            logger.error("❌ Ошибка исправления состояния подписки")
            return False

    @staticmethod
    async def check_real_stripe_subscription(user_id: int):
        """✅ НАТИВНЫЙ PostgreSQL синтаксис"""
        try:
            # ✅ ИСПРАВЛЕНИЕ: Сначала ищем подписку с stripe_subscription_id
            subscription_data = await fetch_one("""
                SELECT stripe_subscription_id, package_id, status 
                FROM user_subscriptions 
                WHERE user_id = $1 AND stripe_subscription_id IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            # Если нет подписки с stripe_subscription_id, ищем любую
            if not subscription_data:
                subscription_data = await fetch_one("""
                    SELECT stripe_subscription_id, package_id, status 
                    FROM user_subscriptions 
                    WHERE user_id = $1
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
            
            logger.info(f"🔍 Поиск подписки в БД: найдено {len(subscription_data) if subscription_data else 0} записей")
            
            if not subscription_data:
                logger.info("❌ Подписка не найдена в БД")
                return {"has_active": False, "subscription_id": None, "status": "none"}
            
            stripe_subscription_id = subscription_data[0]
            
            # Если нет stripe_subscription_id - подписка только в локальной БД
            if not stripe_subscription_id:
                logger.info("⚠️ Подписка найдена в БД, но без stripe_subscription_id")
                # Проверяем статус в локальной БД
                local_status = subscription_data[2]  # status из БД
                if local_status == 'active':
                    return {
                        "has_active": True,
                        "subscription_id": None,
                        "status": "local_active"
                    }
                else:
                    return {
                        "has_active": False,
                        "subscription_id": None,
                        "status": "local_inactive"
                    }
            
            logger.info(f"🔍 Найдена подписка в БД: {stripe_subscription_id}")
            
            # ✅ ВАЖНО: Проверяем реальный статус в Stripe, игнорируя локальный статус
            
            # Проверяем статус в Stripe
            try:
                import stripe
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                logger.info(f"✅ Получена подписка из Stripe: status={subscription.status}")
                
                # Проверяем отмену в конце периода
                is_cancelled_at_period_end = getattr(subscription, 'cancel_at_period_end', False)
                logger.info(f"🔍 cancel_at_period_end: {is_cancelled_at_period_end}")
                
                if subscription.status in ['active', 'trialing'] and not is_cancelled_at_period_end:
                    logger.info("✅ Подписка активна в Stripe")
                    return {
                        "has_active": True, 
                        "subscription_id": stripe_subscription_id,
                        "status": subscription.status
                    }
                elif subscription.status in ['active', 'trialing'] and is_cancelled_at_period_end:
                    logger.info("⚠️ Подписка активна, но отменена в конце периода")
                    return {
                        "has_active": False, 
                        "subscription_id": stripe_subscription_id,
                        "status": "cancelled_at_period_end"
                    }
                else:
                    logger.info(f"❌ Подписка неактивна в Stripe: {subscription.status}")
                    return {
                        "has_active": False, 
                        "subscription_id": stripe_subscription_id,
                        "status": subscription.status
                    }
                    
            except stripe.error.InvalidRequestError as e:
                logger.warning(f"⚠️ Подписка не найдена в Stripe: {e}")
                return {"has_active": False, "subscription_id": None, "status": "deleted"}
            except Exception as stripe_error:
                logger.error(f"❌ Ошибка запроса к Stripe: {stripe_error}")
                return {"has_active": False, "subscription_id": None, "status": "error"}
                
        except Exception as e:
            logger.error("❌ Ошибка проверки Stripe подписки")
            return {"has_active": False, "subscription_id": None, "status": "error"}
    
    @staticmethod
    async def _sync_inactive_subscription(user_id: int, stripe_subscription_id: str, stripe_status: str):
        """Синхронизирует неактивную подписку в локальной БД"""
        try:
            await execute_query("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', cancelled_at = $1
                WHERE user_id = $2 AND stripe_subscription_id = $3
            """, (datetime.now(), user_id, stripe_subscription_id))
            
            logger.info("✅ Синхронизирована неактивная подписка")
            
        except Exception as e:
            logger.error("Ошибка синхронизации неактивной подписки")
    
    @staticmethod
    async def _sync_deleted_subscription(user_id: int, stripe_subscription_id: str):
        """Удаляет несуществующую в Stripe подписку из локальной БД"""
        try:
            await execute_query("""
                DELETE FROM user_subscriptions 
                WHERE user_id = $1 AND stripe_subscription_id = $2
            """, (user_id, stripe_subscription_id))
            
            logger.info("✅ Удалена несуществующая подписка")
            
        except Exception as e:
            logger.error("Ошибка удаления несуществующей подписки")
    
    @staticmethod
    async def purchase_package(user_id: int, package_id: str, payment_method: str = 'stripe'):
        """✅ ИСПРАВЛЕННАЯ версия покупки пакета с PostgreSQL синтаксисом"""
        try:
            from db_postgresql import get_user_language, t
            
            # Получаем данные пакета
            package = await fetch_one("""
                SELECT name, price_usd, documents_included, gpt4o_queries_included, type
                FROM subscription_packages 
                WHERE id = $1 AND is_active = TRUE
            """, (package_id,))
            
            if not package:
                lang = await get_user_language(user_id)
                raise ValueError(t("package_not_found", lang, package_id=package_id))
            
            name, price, docs, queries, pkg_type = package
            
            # Проверяем реальное состояние подписки
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            has_active_subscription = stripe_check["has_active"]
            
            logger.info("Покупка пакета: проверка активной подписки")
            
            # Получаем текущие лимиты пользователя
            current = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_type
                FROM user_limits 
                WHERE user_id = $1
            """, (user_id,))
            
            if not current:
                await execute_query("""
                    INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left)
                    VALUES ($1, 0, 0)
                """, (user_id,))
                current_docs, current_queries, current_sub_type = 0, 0, 'free'
            else:
                current_docs, current_queries, current_sub_type = current
            
            # Определяем правильный subscription_type
            if pkg_type == 'subscription':
                final_subscription_type = 'subscription'
                new_docs = docs
                new_queries = queries
                logger.info("Подписка: заменяем лимиты")
            elif has_active_subscription:
                final_subscription_type = 'subscription'  # Оставляем subscription!
                new_docs = current_docs + docs
                new_queries = current_queries + queries
            else:
                final_subscription_type = 'one_time'
                new_docs = current_docs + docs
                new_queries = current_queries + queries
                logger.info("Extra Pack без подписки: устанавливаем one_time")
            
            # Устанавливаем дату истечения
            expiry_date = datetime.now() + timedelta(days=30)
            
            # Создаем транзакцию
            transaction_id = await execute_query("""
                INSERT INTO transactions 
                (user_id, package_id, amount_usd, package_type, payment_method, 
                 documents_granted, queries_granted, status, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'completed', CURRENT_TIMESTAMP)
            """, (user_id, package_id, price, name, payment_method, docs, queries))
            
            # Обновление лимитов
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = $1,
                    gpt4o_queries_left = $2,
                    subscription_type = $3,
                    subscription_expires_at = $4,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $5
            """, (new_docs, new_queries, final_subscription_type, expiry_date, user_id))

            return {
                "success": True,
                "transaction_id": transaction_id,
                "new_documents": new_docs,
                "new_queries": new_queries,
                "subscription_type": final_subscription_type,
                "expires_at": expiry_date
            }
            
        except Exception as e:
            logger.error("Ошибка покупки пакета")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def cancel_stripe_subscription(user_id: int):
        """✅ ИСПРАВЛЕННАЯ версия отмены подписки с PostgreSQL синтаксисом"""
        try:
            from db_postgresql import get_user_language, t
            lang = await get_user_language(user_id)
            
            # Сначала проверяем реальное состояние в Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            
            if not stripe_check["has_active"]:
                # Подписки нет или она уже отменена
                status = stripe_check["status"]
                
                # Исправляем подвешенное состояние
                await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                
                if status == "deleted":
                    return True, t("subscription_already_cancelled_synced", lang)
                elif status in ["canceled", "cancelled", "cancelled_at_period_end"]:
                    return True, t("subscription_already_cancelled_stripe", lang)
                else:
                    return True, t("subscription_no_active", lang)
            
            stripe_subscription_id = stripe_check["subscription_id"]
            
            # Отменяем подписку в Stripe
            try:
                import stripe
                subscription = stripe.Subscription.modify(
                    stripe_subscription_id,
                    cancel_at_period_end=True
                )
                
                # Сразу обновляем статус в БД как "отменена"
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = $1
                    WHERE stripe_subscription_id = $2
                """, (datetime.now(), stripe_subscription_id))
                
                # Сразу меняем subscription_type на free
                await execute_query("""
                    UPDATE user_limits 
                    SET subscription_type = 'free'
                    WHERE user_id = $1
                """, (user_id,))
                
                logger.info("✅ Подписка отменена")
                
                return True, ""
                
            except stripe.error.InvalidRequestError as stripe_error:
                # Подписка уже отменена в Stripe
                if "canceled subscription" in str(stripe_error):
                    # Синхронизируем локальную БД
                    await SubscriptionManager._sync_inactive_subscription(user_id, stripe_subscription_id, "cancelled")
                    await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                    return True, t("subscription_already_cancelled_stripe", lang)
                else:
                    raise stripe_error
                
        except Exception as e:
            logger.error("❌ Ошибка отмены подписки")
            try:
                from db_postgresql import get_user_language, t
                lang = await get_user_language(user_id)
                return False, t("subscription_cancel_error", lang, error=str(e))
            except:
                return False, f"Ошибка отмены подписки: {e}"
    
    @staticmethod
    async def get_user_limits(user_id: int):
        """✅ ИСПРАВЛЕННАЯ версия с PostgreSQL синтаксисом"""
        try:
            # Проверяем и синхронизируем состояние подписки
            await SubscriptionManager.check_and_reset_expired_limits(user_id)
            
            # Получаем актуальные лимиты
            result = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_type, subscription_expires_at
                FROM user_limits 
                WHERE user_id = $1
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
            logger.error("Ошибка получения лимитов")
            return None
    
    @staticmethod
    async def spend_limits(user_id: int, documents: int = 0, queries: int = 0):
        """✅ PostgreSQL синтаксис"""
        try:
            from db_postgresql import get_user_language, t
            
            # Сначала проверяем истекшие лимиты
            await SubscriptionManager.check_and_reset_expired_limits(user_id)
            
            # Получаем текущие лимиты
            current = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left 
                FROM user_limits 
                WHERE user_id = $1
            """, (user_id,))
            
            if not current:
                lang = await get_user_language(user_id)
                return {"success": False, "error": t("user_not_found", lang)}
            
            current_docs, current_queries = current
            lang = await get_user_language(user_id)
            
            # Проверяем достаточность лимитов
            if documents > current_docs:
                return {"success": False, "error": t("insufficient_document_limits", lang)}
            
            if queries > current_queries:
                return {"success": False, "error": t("insufficient_query_limits", lang)}
            
            # Списываем лимиты
            new_docs = current_docs - documents
            new_queries = current_queries - queries
            
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = $1,
                    gpt4o_queries_left = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $3
            """, (new_docs, new_queries, user_id))
          
            return {
                "success": True,
                "remaining_documents": new_docs,
                "remaining_queries": new_queries
            }
            
        except Exception as e:
            logger.error("Ошибка списания лимитов")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    async def check_and_reset_expired_limits(user_id: int):
        """
        ✅ МАКСИМАЛЬНО ПРОСТАЯ ЛОГИКА:
        - Если нет даты истечения - ничего не делаем (новый пользователь)
        - Если дата истечения + 1 день прошли - обнуляем лимиты
        - Не важно какой тип подписки, не вызываем Stripe API
        """
        try:
            user_data = await fetch_one("""
                SELECT subscription_expires_at
                FROM user_limits 
                WHERE user_id = $1
            """, (user_id,))
            
            if not user_data or not user_data[0]:
                # Новый пользователь без даты истечения - ничего не делаем
                return
            
            expires_at = user_data[0]
            
            # Парсим дату
            if isinstance(expires_at, str):
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expiry_date = expires_at
                
            now = datetime.now()
            
            # ✅ ДАЕМ +1 ДЕНЬ НА АВТОПРОДЛЕНИЕ ПОДПИСКИ
            grace_period = expiry_date + timedelta(days=7)
            
            if now >= grace_period:
                logger.info("🕒 Лимиты истекли, прошло более 7 дней")
                
                # Обнуляем лимиты для ВСЕХ типов покупок
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = $1
                    WHERE user_id = $2 AND status = 'active'
                """, (datetime.now(), user_id))
                await execute_query("""
                    UPDATE user_limits SET 
                        documents_left = 0,
                        gpt4o_queries_left = 0,
                        subscription_expires_at = NULL,
                        subscription_type = 'free',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                """, (user_id,))
                
                logger.info("✅ Лимиты обнулены")
            else:
                logger.debug("⏰ Лимиты еще действуют")
                        
        except Exception as e:
            logger.error("❌ Ошибка проверки лимитов")
    
    @staticmethod
    async def _auto_renew_subscription(user_id: int):
        """✅ ИСПРАВЛЕННАЯ версия - ищет в user_subscriptions и обновляет subscription_type"""
        try:
            # Ищем активную подписку в user_subscriptions
            subscription_data = await fetch_one("""
                SELECT package_id, stripe_subscription_id
                FROM user_subscriptions 
                WHERE user_id = $1 AND status = 'active' AND stripe_subscription_id IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            if not subscription_data:
                logger.warning("Не найдена активная подписка")
                await SubscriptionManager._reset_to_zero(user_id)
                return
            
            package_id, stripe_sub_id = subscription_data
            
            # Получаем параметры пакета из subscription_packages
            package = await fetch_one("""
                SELECT documents_included, gpt4o_queries_included
                FROM subscription_packages 
                WHERE id = $1 AND is_active = TRUE
            """, (package_id,))
            
            if not package:
                logger.error(f"Пакет {package_id} не найден или неактивен")
                await SubscriptionManager._reset_to_zero(user_id)
                return
            
            docs, queries = package
            new_expiry = datetime.now() + timedelta(days=30)
            
            # ✅ ВАЖНО: Обновляем subscription_type на 'subscription'
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = $1,
                    gpt4o_queries_left = $2,
                    subscription_expires_at = $3,
                    subscription_type = 'subscription',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
            """, (docs, queries, new_expiry, user_id))
            
            logger.info(f"✅ Подписка автопродлена до {new_expiry.date()}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автопродления подписки: {e}")
            await SubscriptionManager._reset_to_zero(user_id)
    
    @staticmethod
    async def handle_subscription_renewal(customer_id: str, subscription_id: str) -> bool:
        """
        Обрабатывает webhook от Stripe при автопродлении подписки
        ✅ С защитой от дублирования первого invoice
        """
        try:
            # ✅ ИСПРАВЛЕНО: Находим user_id через subscription_id ИЛИ customer_id
            result = await fetch_one("""
                SELECT user_id, created_at FROM user_subscriptions 
                WHERE stripe_subscription_id = $1 OR stripe_customer_id = $2
                ORDER BY created_at DESC LIMIT 1
            """, (subscription_id, customer_id))

            if not result:
                logger.error(f"❌ User not found for subscription {subscription_id} or customer {customer_id}")
                return False
            
            user_id, created_at = result
            
            # ✅ ЗАЩИТА ОТ ДУБЛИРОВАНИЯ: Игнорируем первый invoice
            from datetime import datetime, timedelta
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            # Если подписка создана менее 5 минут назад - это первый invoice, игнорируем
            time_since_creation = datetime.now() - created_at
            if time_since_creation < timedelta(minutes=5):
                logger.info(f"⏭️ Ignoring first invoice for new subscription (created {time_since_creation.seconds}s ago)")
                return True  # Возвращаем success, но не продлеваем
            
            # Вызываем существующую логику автопродления
            await SubscriptionManager._auto_renew_subscription(user_id)
            
            logger.info(f"✅ Subscription auto-renewed for user {user_id}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Subscription renewal error: {e}")
            return False

    @staticmethod
    async def _reset_to_zero(user_id: int):
        """✅ PostgreSQL синтаксис"""
        try:
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = 0,
                    gpt4o_queries_left = 0,
                    subscription_expires_at = NULL,
                    subscription_type = 'free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, (user_id,))
            
            logger.info("Лимиты сброшены до нуля")
            
        except Exception as e:
            logger.error("Ошибка сброса лимитов")

    @staticmethod
    async def force_sync_with_stripe(user_id: int) -> dict:
        """✅ НАТИВНЫЙ PostgreSQL синтаксис для синхронизации"""
        try:
            logger.info("🔄 Принудительная синхронизация запущена")
            
            # 1. Получаем реальное состояние из Stripe
            stripe_check = await SubscriptionManager.check_real_stripe_subscription(user_id)
            logger.info(f"Stripe check result: {stripe_check}")
            
            # 2. Получаем текущее состояние в БД
            all_subscriptions = await fetch_one("""
                SELECT status, package_id, stripe_subscription_id 
                FROM user_subscriptions 
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            active_subscription = await fetch_one("""
                SELECT status, package_id, stripe_subscription_id 
                FROM user_subscriptions 
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            db_limits = await fetch_one("""
                SELECT subscription_type, documents_left, gpt4o_queries_left
                FROM user_limits WHERE user_id = $1
            """, (user_id,))
            
            logger.info(f"DB state - all_subs: {all_subscriptions}, active: {active_subscription}, limits: {db_limits}")
            
            # 3. Сравниваем и исправляем расхождения
            stripe_active = stripe_check.get("has_active", False)
            db_active = active_subscription is not None
            
            logger.info(f"Comparison - Stripe active: {stripe_active}, DB active: {db_active}")
            
            sync_actions = []
            
            if stripe_active and not db_active:
                logger.info("Case: Stripe active, DB inactive - activating in DB")
                
                if all_subscriptions and stripe_check.get("subscription_id") == all_subscriptions[2]:
                    # Активируем существующую подписку
                    await execute_query("""
                        UPDATE user_subscriptions 
                        SET status = 'active', cancelled_at = NULL
                        WHERE user_id = $1 AND stripe_subscription_id = $2
                    """, (user_id, stripe_check["subscription_id"]))
                    sync_actions.append("✅ Активирован статус подписки")
                    
                else:
                    # Создаём новую запись подписки
                    package_id = await SubscriptionManager._detect_package_from_stripe(
                        stripe_check["subscription_id"]
                    )
                    
                    await execute_query("""
                        INSERT INTO user_subscriptions 
                        (user_id, stripe_subscription_id, package_id, status, created_at, cancelled_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET 
                            stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                            package_id = EXCLUDED.package_id,
                            status = EXCLUDED.status,
                            created_at = EXCLUDED.created_at,
                            cancelled_at = EXCLUDED.cancelled_at
                    """, (user_id, stripe_check["subscription_id"], package_id, 'active', datetime.now(), None))
                    sync_actions.append("✅ Создана запись активной подписки")
                
            elif not stripe_active and db_active:
                logger.info("Case: Stripe inactive, DB active - deactivating in DB")
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = $1
                    WHERE user_id = $2 AND status = 'active'
                """, (datetime.now(), user_id))
                sync_actions.append("❌ Деактивирован статус подписки")
                
            elif stripe_active and db_active:
                logger.info("Case: Both active - checking details")
                stripe_sub_id = stripe_check["subscription_id"]
                db_sub_id = active_subscription[2]
                
                if stripe_sub_id != db_sub_id:
                    await execute_query("""
                        UPDATE user_subscriptions 
                        SET stripe_subscription_id = $1
                        WHERE user_id = $2 AND status = 'active'
                    """, (stripe_sub_id, user_id))
                    sync_actions.append("🔄 Обновлён Stripe subscription ID")
            
            # 4. Синхронизируем только subscription_type
            if db_limits:
                current_type = db_limits[0]
                expected_type = 'subscription' if stripe_active else 'free'
                
                logger.info(f"Subscription type - current: {current_type}, expected: {expected_type}")
                
                if current_type != expected_type:
                    await execute_query("""
                        UPDATE user_limits 
                        SET subscription_type = $1
                        WHERE user_id = $2
                    """, (expected_type, user_id))
                    sync_actions.append(f"🔄 Исправлен subscription_type на {expected_type}")
            
            if sync_actions:
                logger.info(f"Sync completed: {len(sync_actions)} actions performed")
                for action in sync_actions:
                    logger.info(f"  - {action}")
            else:
                logger.info("No sync actions needed")
            
            return {
                "synced": True,
                "stripe_active": stripe_active,
                "db_active": db_active,
                "actions": sync_actions
            }
            
        except Exception as e:
            logger.error(f"❌ Subscription sync failed: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {"synced": False, "error": f"Sync failed: {e}", "actions": []}

    @staticmethod
    async def _detect_package_from_stripe(stripe_subscription_id: str) -> str:
        """Определяет package_id по Stripe подписке"""
        try:
            import stripe
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Получаем сумму из Stripe
            amount_cents = subscription.plan.amount
            
            # Определяем пакет по сумме (учитываем промокоды)
            if amount_cents in [399, 99]:  # $3.99 или $0.99 (промокод)
                return "basic_sub"
            elif amount_cents in [999, 199]:  # $9.99 или $1.99 (промокод)
                return "premium_sub"
            else:
                logger.warning(f"⚠️ Неизвестная сумма в Stripe: ${amount_cents/100}")
                return "basic_sub"  # По умолчанию
                
        except Exception as e:
            logger.error("❌ Ошибка определения пакета из Stripe")
            return "basic_sub"

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
    """
    try:
        # Получаем текущие лимиты ДО траты (для проверки перехода 1→0)
        should_notify = False
        subscription_type = 'free'
        
        if message and bot:
            current_limits = await SubscriptionManager.get_user_limits(user_id)
            current_gpt4o = current_limits.get('gpt4o_queries_left', 0)
            subscription_type = current_limits.get('subscription_type', 'free')
            
            # Запоминаем нужно ли показывать уведомление
            should_notify = (current_gpt4o == 1)
        
        # Тратим лимит через существующую систему
        result = await SubscriptionManager.spend_limits(user_id, queries=1)
        
        # Показываем уведомление сразу после ответа
        if result["success"] and should_notify:
            await _show_limits_exhausted_notification(user_id, message, bot, subscription_type)
        
        return result["success"]
        
    except Exception as e:
        logger.error("Ошибка траты лимита")
        return False


async def _show_limits_exhausted_notification(user_id: int, message, bot, subscription_type: str):
    """
    Показывает уведомление о том, что закончились детальные ответы
    Разные сообщения для разных типов подписки
    """
    try:
        from db_postgresql import get_user_language, t
        
        lang = await get_user_language(user_id)
        
        # Разные сообщения для разных статусов
        if subscription_type in ['free', 'one_time']:
            # Для бесплатных и разовых покупок - предлагаем подписку
            text = t("limits_exhausted_free_message", lang)
            
            # Кнопка для подписки
            button_text = t("limits_exhausted_subscription_button", lang)
            show_subscription_button = True
            
        else:  # subscription - активная подписка
            # Для пользователей с подпиской - просто информируем
            text = t("limits_exhausted_subscription_message", lang)
            show_subscription_button = False
        
        # Создаем клавиатуру только для бесплатных пользователей
        keyboard = None
        if show_subscription_button:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
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
        
        logger.info("Limit notification sent to user")
        
    except Exception as e:
        logger.error("Ошибка отправки уведомления пользователю")