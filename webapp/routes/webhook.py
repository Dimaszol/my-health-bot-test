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
            
            # Используем существующую функцию из StripeManager
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