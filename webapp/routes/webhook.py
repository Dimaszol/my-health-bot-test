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
        
        # Игнорируем другие события
        return JSONResponse(content={"status": "ignored"})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})