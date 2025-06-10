# subscription_logic.py - Логика работы с лимитами и подписками

from datetime import datetime, timedelta
from db_pool import fetch_one, execute_query
import logging

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Менеджер подписок и лимитов"""
    
    @staticmethod
    async def check_and_reset_expired_limits(user_id: int):
        """
        Проверяет и сбрасывает истекшие лимиты
        Вызывается при каждом действии пользователя
        """
        try:
            # Получаем данные пользователя
            user_data = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left, subscription_expires_at, subscription_type
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not user_data:
                logger.warning(f"Пользователь {user_id} не найден в user_limits")
                return
            
            documents_left, queries_left, expires_at, sub_type = user_data
            
            # Если нет даты истечения - лимиты вечные
            if not expires_at:
                return
            
            # Проверяем истечение
            expiry_date = datetime.fromisoformat(expires_at)
            now = datetime.now()
            
            if now >= expiry_date:
                logger.info(f"Лимиты пользователя {user_id} истекли. Тип: {sub_type}")
                
                if sub_type == 'subscription':
                    # Подписка - пытаемся автопродлить
                    await SubscriptionManager._auto_renew_subscription(user_id)
                else:
                    # Разовая покупка - сбрасываем до 0
                    await SubscriptionManager._reset_to_zero(user_id)
                    
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов для пользователя {user_id}: {e}")
    
    @staticmethod
    async def _auto_renew_subscription(user_id: int):
        """Автопродление подписки"""
        try:
            # Получаем последнюю активную подписку
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
            
            # TODO: Здесь будет логика списания денег с карты
            # Пока просто продлеваем (в реальности нужна интеграция с платежной системой)
            
            # Обновляем лимиты и дату
            new_expiry = datetime.now() + timedelta(days=30)
            
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = ?,
                    gpt4o_queries_left = ?,
                    subscription_expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (docs, queries, new_expiry.isoformat(), user_id))
            
            logger.info(f"Подписка пользователя {user_id} автопродлена до {new_expiry.date()}")
            
        except Exception as e:
            logger.error(f"Ошибка автопродления подписки для пользователя {user_id}: {e}")
            await SubscriptionManager._reset_to_zero(user_id)
    
    @staticmethod
    async def _reset_to_zero(user_id: int):
        """Сбрасывает лимиты до нуля"""
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
    
    @staticmethod
    async def purchase_package(user_id: int, package_id: str, payment_method: str = 'stripe'):
        """
        Покупка пакета
        
        Args:
            user_id: ID пользователя
            package_id: ID пакета из subscription_packages
            payment_method: Способ оплаты
        """
        try:
            # Получаем данные пакета
            package = await fetch_one("""
                SELECT name, price_usd, documents_included, gpt4o_queries_included, type
                FROM subscription_packages 
                WHERE id = ? AND is_active = 1
            """, (package_id,))
            
            if not package:
                raise ValueError(f"Пакет {package_id} не найден или неактивен")
            
            name, price, docs, queries, pkg_type = package
            
            # Получаем текущие лимиты пользователя
            current = await fetch_one("""
                SELECT documents_left, gpt4o_queries_left 
                FROM user_limits 
                WHERE user_id = ?
            """, (user_id,))
            
            if not current:
                # Создаем запись если её нет
                await execute_query("""
                    INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left)
                    VALUES (?, 0, 0)
                """, (user_id,))
                current_docs, current_queries = 0, 0
            else:
                current_docs, current_queries = current
            
            # Рассчитываем новые лимиты
            if pkg_type == 'subscription':
                # Подписка - заменяем лимиты
                new_docs = docs
                new_queries = queries
            else:
                # Разовая покупка - добавляем к текущим
                new_docs = current_docs + docs
                new_queries = current_queries + queries
            
            # Устанавливаем дату истечения
            expiry_date = datetime.now() + timedelta(days=30)
            
            # Создаем транзакцию
            transaction_id = await execute_query("""
                INSERT INTO transactions 
                (user_id, package_id, amount_usd, package_type, payment_method, 
                 documents_granted, queries_granted, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)
            """, (user_id, package_id, price, name, payment_method, docs, queries))
            
            # Обновляем лимиты пользователя
            await execute_query("""
                UPDATE user_limits SET 
                    documents_left = ?,
                    gpt4o_queries_left = ?,
                    subscription_type = ?,
                    subscription_expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (new_docs, new_queries, pkg_type, expiry_date.isoformat(), user_id))
            
            logger.info(f"Пакет {package_id} куплен пользователем {user_id}. Новые лимиты: {new_docs} docs, {new_queries} queries")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "new_documents": new_docs,
                "new_queries": new_queries,
                "expires_at": expiry_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка покупки пакета {package_id} для пользователя {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def spend_limits(user_id: int, documents: int = 0, queries: int = 0):
        """
        Тратит лимиты пользователя
        
        Args:
            user_id: ID пользователя
            documents: Количество документов для списания
            queries: Количество запросов для списания
            
        Returns:
            dict: Результат операции
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
    async def get_user_limits(user_id: int):
        """Получает текущие лимиты пользователя"""
        try:
            # Проверяем истекшие лимиты
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
    async def cancel_stripe_subscription(user_id: int):
        """Отменяет активную Stripe подписку"""
        try:
            # Находим активную подписку пользователя
            subscription_data = await fetch_one("""
                SELECT stripe_subscription_id, package_id FROM user_subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            if not subscription_data:
                return False, "Активная подписка не найдена"
            
            stripe_subscription_id, package_id = subscription_data
            
            # Отменяем подписку в Stripe
            import stripe
            subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Обновляем статус в БД
            await execute_query("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', cancelled_at = ?
                WHERE stripe_subscription_id = ?
            """, (datetime.now().isoformat(), stripe_subscription_id))
            
            # Обновляем тип подписки пользователя
            await execute_query("""
                UPDATE user_limits SET 
                    subscription_type = 'free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            
            logger.info(f"✅ Подписка {stripe_subscription_id} пользователя {user_id} отменена")
            
            return True, "Подписка отменена. Лимиты останутся до конца текущего периода."
            
        except Exception as e:
            logger.error(f"❌ Ошибка отмены подписки для пользователя {user_id}: {e}")
            return False, f"Ошибка отмены подписки: {e}"
    
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

async def spend_gpt4o_limit(user_id: int) -> bool:
    """Списывает 1 GPT-4o запрос"""
    result = await SubscriptionManager.spend_limits(user_id, queries=1)
    return result["success"]