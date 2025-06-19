# webhook_handler.py - Простой обработчик webhook для подписок

import stripe
import asyncio
from datetime import datetime
from stripe_config import StripeConfig
from subscription_manager import SubscriptionManager
from db_postgresql import execute_query, fetch_one

async def handle_stripe_webhook(payload: str, sig_header: str):
    """Обрабатывает webhook события для подписок"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, StripeConfig.WEBHOOK_SECRET
        )
        
        if event['type'] == 'invoice.payment_succeeded':
            # ✅ Успешное продление подписки
            invoice = event['data']['object']
            subscription_id = invoice['subscription']
            
            # Находим пользователя
            subscription_data = await fetch_one("""
                SELECT user_id, package_id FROM user_subscriptions 
                WHERE stripe_subscription_id = ? AND status = 'active'
            """, (subscription_id,))
            
            if subscription_data:
                user_id, package_id = subscription_data
                
                # Обновляем лимиты на новый период
                await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_renewal'
                )
                
                print(f"✅ Подписка {subscription_id} пользователя {user_id} продлена")
        
        elif event['type'] == 'customer.subscription.deleted':
            # 🗑️ Подписка отменена
            subscription = event['data']['object']
            subscription_id = subscription['id']
            
            # Помечаем подписку как отмененную
            await execute_query("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', cancelled_at = ?
                WHERE stripe_subscription_id = ?
            """, (datetime.now(), subscription_id))
            
            print(f"🗑️ Подписка {subscription_id} отменена")
        
        return True, "Webhook processed"
        
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        return False, str(e)