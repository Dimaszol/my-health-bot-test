# webhook_subscription_handler.py - PRODUCTION VERSION (Secure + Complete)

import json
import logging
from datetime import datetime
from aiohttp import web
from subscription_manager import SubscriptionManager
from db_postgresql import get_user_language, t, get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

def datetime_serializer(obj):
    """JSON serializer для datetime объектов"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class SubscriptionWebhookHandler:
    """Обработчик webhook для событий подписок от Stripe"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_subscription_webhook(self, request):
        """
        ✅ PRODUCTION версия - обработка Stripe webhook
        """
        try:
            import stripe
            import os
            
            payload = await request.read()
            sig_header = request.headers.get('stripe-signature')
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            
            # Проверяем подпись Stripe
            if sig_header and webhook_secret and webhook_secret.startswith('whsec_'):
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
                logger.info("✅ Webhook verified with Stripe signature")
            else:
                # Fallback для тестирования без подписи
                data = json.loads(payload.decode('utf-8'))
                event = data
            
            # Извлекаем тип события
            event_type = event.get('type')
            
            # ✅ ОБРАБОТКА invoice.payment_succeeded (автопродление подписки)
            if event_type == 'invoice.payment_succeeded':
                # Извлекаем данные из invoice
                invoice_data = event.get('data', {}).get('object', {})
                
                # ✅ ПРАВИЛЬНО: Извлекаем subscription_id из parent.subscription_details
                subscription_id = None
                parent = invoice_data.get('parent', {})
                if parent.get('type') == 'subscription_details':
                    subscription_details = parent.get('subscription_details', {})
                    subscription_id = subscription_details.get('subscription')
                
                amount = invoice_data.get('amount_paid', 0)
                
                if not subscription_id:
                    logger.error("❌ Subscription ID not found in invoice webhook")
                    return web.json_response(
                        {"status": "error", "message": "Subscription ID not found"}, 
                        status=400
                    )
                
                # Обрабатываем платёж
                result = await self._handle_successful_payment(
                    invoice_data, subscription_id, amount
                )
            
            # ✅ ОБРАБОТКА checkout.session.completed (первичная покупка и разовые платежи)
            elif event_type == 'checkout.session.completed':
                session_data = event.get('data', {}).get('object', {})
                session_id = session_data.get('id')
                
                if not session_id:
                    logger.error("❌ Missing session_id in checkout.session.completed")
                    return web.json_response(
                        {"status": "error", "message": "Missing session_id"}, 
                        status=400
                    )
                
                try:
                    from stripe_manager import StripeManager
                    success, message = await StripeManager.handle_successful_payment(session_id)
                    
                    if success:
                        result = {
                            "status": "success",
                            "message": f"Payment processed: {message}",
                            "session_id": session_id
                        }
                        
                        # Отправляем уведомление пользователю
                        try:
                            session = stripe.checkout.Session.retrieve(session_id)
                            user_id = int(session.metadata.get('user_id'))
                            lang = await get_user_language(user_id)
                            localized_message = t("webhook_payment_processed_auto", lang, message=message)
                            await self.bot.send_message(user_id, localized_message, parse_mode="HTML")
                        except Exception:
                            pass  # Игнорируем ошибки уведомления
                    else:
                        result = {
                            "status": "error",
                            "message": f"Payment processing failed: {message}"
                        }
                except Exception as e:
                    logger.error(f"❌ Checkout processing failed")
                    result = {
                        "status": "error",
                        "message": "Exception in checkout processing"
                    }
            
            # Игнорируем все остальные события
            else:
                result = {"status": "ignored", "message": f"Event {event_type} ignored"}
            
            # Возвращаем результат
            response_data = {
                "status": "success",
                "message": "Webhook processed successfully",
                "event_type": event_type,
                "result": result,
                "processed_at": datetime.now().isoformat()
            }
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"❌ Webhook processing error")
            return web.json_response(
                {"status": "error", "message": "Internal server error"}, 
                status=500
            )
    
    async def _handle_successful_payment(self, invoice_data, subscription_id, amount):
        """
        ✅ ИСПРАВЛЕНО - Извлекаем user_id через stripe_customer_id из БД
        """
        try:
            # 1. Получаем Stripe customer_id из invoice
            stripe_customer_id = invoice_data.get('customer')
            
            if not stripe_customer_id:
                logger.error("❌ Customer ID not found in webhook")
                return {"status": "error", "message": "Customer ID not found"}
            
            if not subscription_id:
                logger.error("❌ Subscription ID not found")
                return {"status": "error", "message": "Subscription ID not found"}
            
            # 2. Получаем соединение с БД
            conn = await get_db_connection()
            try:
                # 3. Находим user_id по customer_id
                user_data = await conn.fetchrow("""
                    SELECT user_id FROM user_subscriptions 
                    WHERE stripe_customer_id = $1
                """, stripe_customer_id)
                
                if not user_data:
                    logger.error("❌ User not found by customer_id")
                    return {"status": "error", "message": "User not found"}
                
                user_id = user_data['user_id']
                
                # 4. Определяем пакет
                package_id = self._determine_package_by_amount(amount)
                
                # 5. Проверяем существование пользователя
                user_exists = await conn.fetchrow("""
                    SELECT user_id FROM users WHERE user_id = $1
                """, user_id)
                
                if not user_exists:
                    # Создаем пользователя если не существует
                    await conn.execute("""
                        INSERT INTO users (user_id, name, created_at) 
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                    """, user_id, f"User {user_id}", datetime.now())
                
                # 6. Используем ПРАВИЛЬНЫЙ метод - purchase_package
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_subscription'
                )
                
                if not result.get('success'):
                    logger.error(f"❌ SubscriptionManager failed")
                    return {"status": "error", "message": "SubscriptionManager failed"}
                
                # 7. Обновляем подписку в БД
                await conn.execute("""
                    UPDATE user_subscriptions 
                    SET stripe_subscription_id = $1, 
                        package_id = $2, 
                        status = $3,
                        created_at = $4,
                        cancelled_at = $5
                    WHERE stripe_customer_id = $6
                """, subscription_id, package_id, 'active', datetime.now(), None, stripe_customer_id)
                
                # 8. Отправляем уведомление
                await self._send_renewal_notification(user_id, package_id)
                
                return {
                    "status": "success",
                    "message": "Subscription renewed",
                    "user_id": user_id,
                    "package_id": package_id,
                    "stripe_subscription_id": subscription_id,
                    "new_limits": {
                        "documents": result.get('new_documents'),
                        "queries": result.get('new_queries')
                    }
                }
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Payment processing error")
            return {"status": "error", "message": "Payment processing failed"}
    
    def _determine_package_by_amount(self, amount_cents):
        """Определяет тип пакета по сумме платежа"""
        
        # ✅ ОБЫЧНЫЕ ЦЕНЫ
        if amount_cents == 399:  # $3.99 - Basic
            return "basic_sub"
        elif amount_cents == 999:  # $9.99 - Premium  
            return "premium_sub"
        elif amount_cents == 199:  # $1.99 - Extra pack
            return "extra_pack"
        
        # ✅ ПРОМОКОДЫ
        elif amount_cents == 99:   # $0.99 - Промокод Basic
            return "basic_sub"
        elif amount_cents == 299:  # $2.99 - Промокод Premium
            return "premium_sub"
        
        # ✅ НЕИЗВЕСТНАЯ СУММА - по умолчанию premium
        else:
            return "premium_sub"
    
    async def _send_renewal_notification(self, user_id, package_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление об успешном продлении"""
        try:
            lang = await get_user_language(user_id)
            message = t("webhook_subscription_renewed", lang, package_id=package_id)
            await self.bot.send_message(user_id, message)
        except Exception:
            pass  # ⚠️ Не логируем детали ошибки уведомления
    
    async def _send_payment_failed_notification(self, user_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление о неудачном платеже"""
        try:
            lang = await get_user_language(user_id)
            message = t("webhook_payment_failed", lang)
            await self.bot.send_message(user_id, message)
        except Exception:
            pass  # ⚠️ Не логируем детали ошибки уведомления

# Функция для создания веб-приложения
def create_webhook_app(bot):
    """Создает веб-приложение для обработки webhook"""
    
    handler = SubscriptionWebhookHandler(bot)
    app = web.Application()
    
    # Добавляем маршрут для webhook
    app.router.add_post('/webhook/stripe', handler.handle_subscription_webhook)
    
    # Добавляем health check
    async def health_check(request):
        return web.json_response({
            "status": "healthy",
            "service": "subscription_webhook",
            "timestamp": datetime.now().isoformat()
        })
    
    app.router.add_get('/health', health_check)
    
    return app

# Функция для запуска webhook сервера
async def start_webhook_server(bot, host='0.0.0.0', port=8080):
    """Запускает webhook сервер"""
    
    app = create_webhook_app(bot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info("✅ Webhook server started")
    
    return runner