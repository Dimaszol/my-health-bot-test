# stripe_manager.py - Менеджер платежей через Stripe

import stripe
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from stripe_config import StripeConfig
from subscription_manager import SubscriptionManager
from db_pool import execute_query, fetch_one

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
                datetime.now().isoformat()
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
                """, (user_id, subscription_id, package_id, datetime.now().isoformat()))
                
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
                datetime.now().isoformat(),
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
            from db_pool import fetch_all
            
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