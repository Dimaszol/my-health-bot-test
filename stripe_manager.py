# stripe_manager.py - Менеджер платежей через Stripe

import stripe
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from stripe_config import StripeConfig
from subscription_manager import SubscriptionManager
from db_postgresql import execute_query, fetch_one

logger = logging.getLogger(__name__)

class StripeManager:
    """Менеджер для работы с платежами Stripe"""
    
    @staticmethod
    async def create_checkout_session(user_id: int, package_id: str, user_name: str = "User"):
        """Создает сессию оплаты с правильным типом"""
        try:
            package_info = StripeConfig.get_package_info(package_id)
            if not package_info:
                return False, f"Пакет {package_id} не найден"
            
            # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Определяем тип оплаты
            if package_info['type'] == 'subscription':
                # ✅ ПОДПИСКА - автосписание каждый месяц
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': package_info['stripe_price_id'],  # Готовый Price ID
                        'quantity': 1,
                    }],
                    mode='subscription',  # ✅ ПОДПИСКА
                    success_url=StripeConfig.SUCCESS_URL + f"?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=StripeConfig.CANCEL_URL,
                    allow_promotion_codes=True,
                    subscription_data={
                        'metadata': {
                            'user_id': str(user_id),
                            'package_id': package_id,
                        }
                    },
                    metadata={
                        'user_id': str(user_id),
                        'package_id': package_id,
                        'user_name': user_name,
                        'subscription_type': 'recurring'
                    }
                )
            else:
                # ✅ РАЗОВАЯ ПОКУПКА (только Extra Pack)
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': package_info['price_cents'],
                            'product_data': {
                                'name': package_info['name'],
                                'description': f"{package_info['documents']} documents + {package_info['gpt4o_queries']} GPT-4o queries",
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='payment',  # ✅ РАЗОВАЯ ОПЛАТА
                    success_url=StripeConfig.SUCCESS_URL + f"?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=StripeConfig.CANCEL_URL,
                    metadata={
                        'user_id': str(user_id),
                        'package_id': package_id,
                        'user_name': user_name,
                        'subscription_type': 'one_time'
                    }
                )
            
            # Сохраняем сессию в БД
            await StripeManager._save_payment_session(
                user_id=user_id,
                session_id=session.id,
                package_id=package_id,
                amount_cents=package_info['price_cents']
            )
            
            logger.info(f"✅ Создана {'подписка' if package_info['type'] == 'subscription' else 'разовая оплата'} для пользователя {user_id}: {session.id}")
            return True, session.url
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания сессии: {e}")
            return False, str(e)
    
    @staticmethod
    async def _save_payment_session(user_id: int, session_id: str, package_id: str, amount_cents: int):
        """Сохраняет информацию о сессии оплаты в БД"""
        try:
            await execute_query("""
                INSERT INTO transactions 
                (user_id, stripe_session_id, package_id, amount_usd, package_type, status, payment_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id, 
                package_id,
                amount_cents / 100,  # Конвертируем центы в доллары
                StripeConfig.get_package_info(package_id)['name'],
                'pending',
                'stripe',
                datetime.now()
            ))
            
            logger.info(f"💾 Сохранена информация о сессии {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сессии в БД: {e}")
    
    @staticmethod
    async def handle_successful_payment(session_id: str):
        """Обрабатывает успешную оплату (подписка или разовая)"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Для подписок проверяем статус подписки, не платежа
            if session.mode == 'subscription':
                subscription = stripe.Subscription.retrieve(session.subscription)
                if subscription.status not in ['active', 'trialing']:
                    return False, f"Подписка не активна: {subscription.status}"
            else:
                # Для разовых платежей проверяем статус оплаты
                if session.payment_status != 'paid':
                    return False, "Платеж не завершен"
            
            # Извлекаем метаданные
            user_id = int(session.metadata.get('user_id'))
            package_id = session.metadata.get('package_id')
            
            # Проверяем дубликаты
            existing_transaction = await fetch_one("""
                SELECT id FROM transactions 
                WHERE stripe_session_id = ? AND status = 'completed'
            """, (session_id,))
            
            if existing_transaction:
                return True, "Платеж уже обработан"
            
            # Получаем информацию о пакете
            package_info = StripeConfig.get_package_info(package_id)
            if not package_info:
                return False, f"Пакет {package_id} не найден"
            
            # ✅ НОВАЯ ЛОГИКА: Обрабатываем подписки по-разному
            if package_info['type'] == 'subscription':
                # Для подписок сохраняем Stripe subscription ID
                subscription_id = session.subscription
                
                # Сохраняем информацию о подписке
                await execute_query("""
                    INSERT OR REPLACE INTO user_subscriptions 
                    (user_id, stripe_subscription_id, package_id, status, created_at)
                    VALUES (?, ?, ?, 'active', ?)
                """, (user_id, subscription_id, package_id, datetime.now()))
                
                # Выдаем лимиты
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_subscription'
                )
                
                message = f"Подписка '{package_info['name']}' активирована! Автопродление каждый месяц."
                
            else:
                # Для разовых покупок - как раньше
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_payment'
                )
                
                message = f"'{package_info['name']}' успешно приобретен!"
            
            if not result['success']:
                return False, f"Ошибка выдачи лимитов: {result['error']}"
            
            # Обновляем статус транзакции
            await execute_query("""
                UPDATE transactions SET 
                    status = 'completed',
                    completed_at = ?,
                    documents_granted = ?,
                    queries_granted = ?
                WHERE stripe_session_id = ?
            """, (
                datetime.now(),
                package_info['documents'],
                package_info['gpt4o_queries'], 
                session_id
            ))
            
            logger.info(f"✅ Успешно обработан {'подписка' if package_info['type'] == 'subscription' else 'платеж'} {session_id} для пользователя {user_id}")
            
            return True, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки платежа {session_id}: {e}")
            return False, f"Ошибка активации: {e}"
    
    @staticmethod
    async def handle_failed_payment(session_id: str, reason: str = "Unknown") -> bool:
        """
        Обрабатывает неуспешный платеж
        
        Args:
            session_id: ID сессии Stripe
            reason: Причина неудачи
            
        Returns:
            bool: Успех обработки
        """
        try:
            # Обновляем статус в БД
            await execute_query("""
                UPDATE transactions SET 
                    status = 'failed'
                WHERE stripe_session_id = ?
            """, (session_id,))
            
            logger.warning(f"⚠️ Неуспешный платеж {session_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки неуспешного платежа {session_id}: {e}")
            return False
    
    @staticmethod
    async def cancel_user_subscription(user_id: int) -> Tuple[bool, str]:
        """Отменяет активную подписку пользователя"""
        return await SubscriptionManager.cancel_stripe_subscription(user_id)
    
    @staticmethod
    async def get_user_payment_history(user_id: int, limit: int = 10) -> list:
        """Получает историю платежей пользователя"""
        try:
            from db_postgresql import fetch_all
            
            transactions = await fetch_all("""
                SELECT package_type, amount_usd, status, created_at, completed_at
                FROM transactions 
                WHERE user_id = ? AND status != 'pending'
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            return [
                {
                    "package": row[0],
                    "amount": row[1],
                    "status": row[2], 
                    "created": row[3],
                    "completed": row[4]
                }
                for row in transactions
            ]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории платежей для пользователя {user_id}: {e}")
            return []

# Функция для webhook (обработка событий от Stripe)
async def handle_stripe_webhook(payload: str, sig_header: str) -> Tuple[bool, str]:
    """
    Обрабатывает webhook события от Stripe
    
    Args:
        payload: Тело запроса от Stripe
        sig_header: Заголовок подписи Stripe
        
    Returns:
        (успех, сообщение)
    """
    try:
        # Проверяем подпись webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, StripeConfig.WEBHOOK_SECRET
        )
        
        # Обрабатываем различные типы событий
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            success, message = await StripeManager.handle_successful_payment(session['id'])
            return success, message
            
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            await StripeManager.handle_failed_payment(session['id'], "Session expired")
            return True, "Session expired processed"
            
        else:
            logger.info(f"🔄 Необработанное Stripe событие: {event['type']}")
            return True, f"Event {event['type']} ignored"
            
    except ValueError as e:
        logger.error(f"❌ Неверный payload от Stripe: {e}")
        return False, "Invalid payload"
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Неверная подпись Stripe webhook: {e}")
        return False, "Invalid signature"
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки Stripe webhook: {e}")
        return False, f"Webhook error: {e}"
    
class StripeGDPRManager:
    """Управление GDPR-совместимым удалением данных из Stripe"""
    
    @staticmethod
    async def delete_user_stripe_data_gdpr(user_id: int) -> bool:
        """
        GDPR-совместимое удаление всех данных пользователя из Stripe
        Включает отмену активных подписок и удаление customer
        """
        try:
            print(f"💳 Начинаем GDPR удаление Stripe данных для пользователя {user_id}")
            
            # 1. Находим все Stripe подписки пользователя
            stripe_subscriptions = await StripeGDPRManager._find_user_subscriptions(user_id)
            
            # 2. Отменяем все активные подписки
            for subscription_id in stripe_subscriptions:
                await StripeGDPRManager._cancel_stripe_subscription(subscription_id)
            
            # 3. Находим Stripe customer_id
            customer_id = await StripeGDPRManager._find_stripe_customer(user_id)
            
            # 4. Удаляем customer из Stripe (если есть)
            if customer_id:
                await StripeGDPRManager._delete_stripe_customer(customer_id)
            
            # 5. Очищаем Stripe ссылки из нашей базы
            await StripeGDPRManager._clean_stripe_references(user_id)
            
            print(f"✅ GDPR удаление Stripe данных завершено для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка GDPR удаления Stripe данных для пользователя {user_id}: {e}")
            print(f"⚠️ Ошибка удаления Stripe данных: {e}")
            return False
    
    @staticmethod
    async def _find_user_subscriptions(user_id: int) -> list:
        """Находит все Stripe подписки пользователя"""
        try:
            from db_postgresql import fetch_all
            
            result = await fetch_all("""
                SELECT stripe_subscription_id 
                FROM user_subscriptions 
                WHERE user_id = $1 AND stripe_subscription_id IS NOT NULL
            """, (user_id,))
            
            subscriptions = [row['stripe_subscription_id'] for row in result if row['stripe_subscription_id']]
            print(f"🔍 Найдено {len(subscriptions)} Stripe подписок для пользователя {user_id}")
            return subscriptions
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска подписок для пользователя {user_id}: {e}")
            return []
    
    @staticmethod
    async def _cancel_stripe_subscription(subscription_id: str):
        """Отменяет подписку в Stripe"""
        try:
            # Немедленная отмена подписки
            stripe.Subscription.delete(subscription_id)
            print(f"✅ Отменена Stripe подписка: {subscription_id}")
            
        except stripe.error.InvalidRequestError as e:
            if "No such subscription" in str(e):
                print(f"⚠️ Подписка {subscription_id} уже не существует в Stripe")
            else:
                logger.error(f"❌ Ошибка отмены подписки {subscription_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка отмены подписки {subscription_id}: {e}")
    
    @staticmethod
    async def _find_stripe_customer(user_id: int) -> str:
        """Находит Stripe customer_id по user_id (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
        try:
            from db_postgresql import fetch_one
            
            # Пока что возвращаем None, так как поле отсутствует
            # В будущем, когда добавите поле stripe_customer_id, раскомментируйте:
            
            # result = await fetch_one("""
            #     SELECT stripe_customer_id 
            #     FROM transactions 
            #     WHERE user_id = $1 AND stripe_customer_id IS NOT NULL
            #     ORDER BY created_at DESC
            #     LIMIT 1
            # """, (user_id,))
            
            # if result and result['stripe_customer_id']:
            #     customer_id = result['stripe_customer_id']
            #     print(f"🔍 Найден Stripe customer: {customer_id} для пользователя {user_id}")
            #     return customer_id
            
            print(f"⚠️ Поиск Stripe customer пропущен (поле отсутствует) для пользователя {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска Stripe customer для пользователя {user_id}: {e}")
            return None
    
    @staticmethod
    async def _delete_stripe_customer(customer_id: str):
        """Удаляет customer из Stripe"""
        try:
            stripe.Customer.delete(customer_id)
            print(f"✅ Удален Stripe customer: {customer_id}")
            
        except stripe.error.InvalidRequestError as e:
            if "No such customer" in str(e):
                print(f"⚠️ Customer {customer_id} уже не существует в Stripe")
            else:
                logger.error(f"❌ Ошибка удаления customer {customer_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления customer {customer_id}: {e}")
    
    @staticmethod
    async def _clean_stripe_references(user_id: int):
        """Очищает все ссылки на Stripe из нашей базы данных (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            conn = await get_db_connection()
            try:
                # Удаляем записи подписок с Stripe ID
                result = await conn.execute("""
                    DELETE FROM user_subscriptions 
                    WHERE user_id = $1 AND stripe_subscription_id IS NOT NULL
                """, user_id)  # ✅ ИСПРАВЛЕНО: передаем user_id напрямую, а не кортеж
                
                print(f"✅ Stripe ссылки очищены из базы для пользователя {user_id}")
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки Stripe ссылок для пользователя {user_id}: {e}")