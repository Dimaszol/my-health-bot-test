# webapp/routes/webhook.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe Webhook для веб-версии
    """
    try:
        import stripe
        import os
        from stripe_manager import StripeManager
        
        # Получаем данные
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # Проверяем подпись
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except Exception as e:
            logger.error(f"❌ Webhook signature verification failed: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid signature"})
        
        logger.info(f"✅ Webhook получен: {event['type']}")
        
        # Обрабатываем событие
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            session_id = session['id']
            payment_type = session.get('metadata', {}).get('type')

            # Разовый разбор без документа
            if payment_type == 'one_time_limits':
                from db_postgresql import execute_query, fetch_one, get_db_connection, release_db_connection
                user_id = int(session.get('metadata', {}).get('user_id'))

                existing = await fetch_one(
                    "SELECT id FROM transactions WHERE stripe_session_id = $1 AND status = 'completed'",
                    (session_id,)
                )
                if not existing:
                    await execute_query("""
                        INSERT INTO transactions
                        (user_id, stripe_session_id, amount_usd, package_type,
                        payment_method, status, documents_granted, completed_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    """, (user_id, session_id, 2.49, 'one_time_limits', 'stripe', 'completed', 1))

                    conn = await get_db_connection()
                    try:
                        await conn.execute(
                            "UPDATE user_limits SET documents_left = documents_left + 1, updated_at = NOW() WHERE user_id = $1",
                            user_id
                        )
                        await conn.execute(
                            "UPDATE user_limits SET gpt4o_queries_left = gpt4o_queries_left + 10 WHERE user_id = $1",
                            user_id
                        )
                    finally:
                        await release_db_connection(conn)

                logger.info(f"✅ one_time_limits обработан")
                return JSONResponse(content={"status": "success"})

            # Разовый анализ документа — уже обрабатывается отдельно
            if payment_type == 'one_time_document':
                return JSONResponse(content={"status": "ignored", "reason": "handled by bot webhook"})

            # Стандартная обработка подписок
            success, message = await StripeManager.handle_successful_payment(session_id)
            
            if success:
                logger.info(f"✅ Платёж обработан: {message}")
                return JSONResponse(content={"status": "success"})
            else:
                logger.error(f"❌ Ошибка обработки: {message}")
                return JSONResponse(content={"status": "error", "message": message})

        elif event['type'] == 'invoice.payment_succeeded':
            # Автопродление подписки
            from subscription_manager import SubscriptionManager
            
            invoice = event['data']['object']
            
            # ✅ ПРАВИЛЬНО: Извлекаем subscription_id из parent.subscription_details
            subscription_id = None
            parent = invoice.get('parent', {})
            if parent.get('type') == 'subscription_details':
                subscription_details = parent.get('subscription_details', {})
                subscription_id = subscription_details.get('subscription')
            
            customer_id = invoice.get('customer')
            
            if subscription_id and customer_id:
                success = await SubscriptionManager.handle_subscription_renewal(
                    customer_id=customer_id,
                    subscription_id=subscription_id
                )
                
                if success:
                    logger.info(f"✅ Подписка продлена для customer {customer_id}")
                    return JSONResponse(content={"status": "success"})
                else:
                    logger.error(f"❌ Ошибка продления подписки")
                    return JSONResponse(content={"status": "error"})
            
            return JSONResponse(content={"status": "ignored", "reason": "No subscription_id"})

        # Игнорируем другие события
        return JSONResponse(content={"status": "ignored"})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})