# webhook_subscription_handler.py - Обработчик webhook для автоматического продления подписок

import json
import logging
from datetime import datetime
from aiohttp import web
from subscription_manager import SubscriptionManager
from db_postgresql import get_user_name, get_user_language, t
from notification_system import NotificationSystem

logger = logging.getLogger(__name__)

class SubscriptionWebhookHandler:
    """Обработчик webhook для событий подписок от Make.com"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_subscription_webhook(self, request):
        """
        ✅ ПРОСТАЯ версия - как раньше через Make.com, но напрямую через Stripe
        """
        try:
            # Получаем данные webhook
            try:
                import stripe
                import os
                
                payload = await request.read()
                sig_header = request.headers.get('stripe-signature')
                webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
                
                if sig_header and webhook_secret and webhook_secret.startswith('whsec_'):
                    # Прямой Stripe webhook
                    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
                    data = event
                    logger.info("✅ Webhook verified with Stripe signature")
                    
                    # Извлекаем данные из Stripe формата
                    event_type = data.get('type')
                    
                    if event_type == 'invoice.payment_succeeded':
                        # Извлекаем данные для подписки
                        invoice_data = data.get('data', {}).get('object', {})
                        
                        # Ищем user_id в metadata line items (как в вашем JSON)
                        stripe_customer_id = None
                        lines = invoice_data.get('lines', {}).get('data', [])
                        if lines:
                            line_metadata = lines[0].get('metadata', {})
                            stripe_customer_id = line_metadata.get('user_id')
                        
                        # Если не нашли в line items - ищем в subscription metadata
                        if not stripe_customer_id:
                            parent = invoice_data.get('parent', {})
                            if parent.get('type') == 'subscription_details':
                                sub_metadata = parent.get('subscription_details', {}).get('metadata', {})
                                stripe_customer_id = sub_metadata.get('user_id')
                        
                        subscription_id = invoice_data.get('subscription')
                        amount = invoice_data.get('amount_paid', 0)
                        
                        logger.info(f"📄 Invoice payment: user_id={stripe_customer_id}, amount={amount}")
                        
                    elif event_type == 'checkout.session.completed':
                        # Извлекаем данные для разовой покупки
                        session_data = data.get('data', {}).get('object', {})
                        session_id = session_data.get('id')
                        stripe_customer_id = None  # Будет извлечен в StripeManager
                        subscription_id = None
                        amount = 0
                        
                        logger.info(f"💳 Checkout completed: session_id={session_id}")
                        
                else:
                    # Fallback для тестирования без подписи
                    data = json.loads(payload.decode('utf-8'))
                    logger.info("⚠️ Webhook processed without signature verification")
                    
                    # Make.com формат (если понадобится)
                    event_type = data.get('event_type')
                    stripe_customer_id = data.get('user_id')
                    subscription_id = data.get('subscription_id')
                    amount = int(data.get('amount', 0))
                    
            except Exception as e:
                data = await request.json()
                logger.warning(f"⚠️ Webhook signature verification failed: {e}")
                
                # Простой JSON формат
                event_type = data.get('event_type') or data.get('type')
                stripe_customer_id = data.get('user_id')
                subscription_id = data.get('subscription_id')
                amount = int(data.get('amount', 0))
            
            logger.info(f"🎯 Processing: {event_type}, user: {stripe_customer_id}, amount: {amount}")
            
            # ✅ ПРОСТАЯ ОБРАБОТКА - только 2 типа событий
            if event_type == 'invoice.payment_succeeded':
                # Подписки
                if not stripe_customer_id:
                    logger.error("❌ User ID not found in invoice webhook")
                    return web.json_response(
                        {"status": "error", "message": "User ID not found"}, 
                        status=400
                    )
                
                result = await self._handle_successful_payment(
                    stripe_customer_id, subscription_id, amount
                )
                
            elif event_type == 'checkout.session.completed':
                # Разовые покупки
                session_id = data.get('session_id') or data.get('data', {}).get('object', {}).get('id')
                
                if session_id:
                    try:
                        from stripe_manager import StripeManager
                        success, message = await StripeManager.handle_successful_payment(session_id)
                        
                        if success:
                            result = {
                                "status": "success",
                                "message": f"One-time payment processed: {message}",
                                "session_id": session_id
                            }
                            
                            # Уведомление пользователю
                            if stripe_customer_id:
                                try:
                                    user_id = int(stripe_customer_id)
                                    lang = await get_user_language(user_id)
                                    localized_message = t("webhook_payment_processed_auto", lang, message=message)
                                    await self.bot.send_message(user_id, localized_message, parse_mode="HTML")
                                except Exception as notify_error:
                                    logger.warning(f"Notification failed: {notify_error}")
                        else:
                            result = {"status": "error", "message": f"Payment processing failed: {message}"}
                    except Exception as e:
                        result = {"status": "error", "message": f"Exception during payment processing: {str(e)}"}
                else:
                    result = {"status": "error", "message": "Missing session_id"}
                    
            else:
                # Игнорируем все остальные события
                logger.info(f"🚫 Ignoring event: {event_type}")
                result = {"status": "ignored", "message": f"Event {event_type} ignored"}
            
            # Возвращаем результат
            logger.info(f"✅ Webhook result: {result}")
            return web.json_response({
                "status": "success",
                "message": "Webhook processed successfully",
                "event_type": event_type,
                "result": result,
                "processed_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Webhook processing error: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return web.json_response(
                {"status": "error", "message": str(e)}, 
                status=500
            )
    
    async def _handle_successful_payment(self, stripe_customer_id, subscription_id, amount):
        """Обрабатывает успешное продление подписки"""
        try:
            # ✅ ИСПРАВЛЕНО: Убираем деление, так как amount уже в центах
            logger.info("Subscription payment processed successfully")
            
            # TODO: Найти user_id по stripe_customer_id
            user_id = int(stripe_customer_id)
            
            if not user_id:
                logger.warning("User not found for webhook")
                return {"status": "error", "message": "User not found"}
            
            # Определяем тип подписки по сумме
            package_id = self._determine_package_by_amount(amount)
            
            # Пополняем лимиты пользователя
            result = await SubscriptionManager.purchase_package(
                user_id=user_id,
                package_id=package_id,
                payment_method='stripe_subscription'
            )
            
            if result['success']:
                from db_postgresql import execute_query
                
                # ✅ ИСПРАВЛЕННЫЙ SQL: Используем None вместо NULL в параметрах
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
                """, (user_id, subscription_id, package_id, 'active', datetime.now(), None))
                
                # ✅ ЛОКАЛИЗОВАННОЕ уведомление пользователю
                await self._send_renewal_notification(user_id, package_id)
                
                logger.info("User limits updated successfully")
                return {
                    "status": "success",
                    "message": "Subscription renewed",
                    "user_id": user_id,
                    "package_id": package_id,
                    "new_limits": {
                        "documents": result.get('new_documents'),
                        "queries": result.get('new_queries')
                    }
                }
            else:
                logger.error("Limits update failed")
                return {"status": "error", "message": result.get('error')}
                
        except Exception as e:
            logger.error("Payment processing error")
            return {"status": "error", "message": str(e)}
    
    async def _handle_failed_payment(self, stripe_customer_id, subscription_id):
        """Обрабатывает неудачное продление подписки"""
        try:
            logger.warning("Subscription payment failed")
            
            user_id = await self._get_user_id_by_stripe_customer(stripe_customer_id)
            
            if user_id:
                # 1️⃣ Отправляем уведомление пользователю
                await self._send_payment_failed_notification(user_id)
                
                # 2️⃣ ✅ НОВОЕ: Обновляем статус подписки в БД
                from db_postgresql import execute_query
                
                await execute_query("""
                    UPDATE user_subscriptions 
                    SET status = 'payment_failed', cancelled_at = $1
                    WHERE user_id = $2 AND stripe_subscription_id = $3
                """, (datetime.now(), user_id, subscription_id))
                
                # 3️⃣ ✅ НОВОЕ: Деактивируем лимиты пользователя
                await execute_query("""
                    UPDATE user_limits 
                    SET subscription_type = 'free',
                        subscription_expires_at = NULL
                    WHERE user_id = $1
                """, (user_id,))
                
                logger.info("Payment failure notification sent")
                logger.info("Subscription deactivated")
                
                return {
                    "status": "success",
                    "message": "Payment failed processed and subscription deactivated",
                    "user_id": user_id
                }
            else:
                return {"status": "error", "message": "User not found"}
                
        except Exception as e:
            logger.error("Failed payment processing error")
            return {"status": "error", "message": str(e)}
    
    async def _handle_invoice_created(self, stripe_customer_id, subscription_id):
        """Обрабатывает создание нового счета"""
        try:
            logger.info("Invoice created")
            
            # Пока просто логируем
            # В будущем можно добавить предварительные уведомления
            
            return {
                "status": "success",
                "message": "Invoice created logged"
            }
            
        except Exception as e:
            logger.error("Invoice processing error")
            return {"status": "error", "message": str(e)}
    
    async def _get_user_id_by_stripe_customer(self, stripe_customer_id):
        """
        Находит user_id по stripe_customer_id
        
        TODO: Реализовать поиск в БД
        Нужна таблица связи stripe_customer_id -> user_id
        """
        # ЗАГЛУШКА: для тестирования возвращаем тестового пользователя
        if stripe_customer_id:
            return int(stripe_customer_id)  # Используем переданный ID
        return None
    
    def _determine_package_by_amount(self, amount_cents):
        """Определяет тип пакета по сумме платежа"""
        
        # ✅ ОБЫЧНЫЕ ЦЕНЫ
        if amount_cents == 399:  # $3.99 - Обычная цена Basic
            return "basic_sub"
        elif amount_cents == 999:  # $9.99 - Обычная цена Premium  
            return "premium_sub"
        elif amount_cents == 199:  # $1.99 - Разовая покупка
            return "extra_pack"
        
        # ✅ ПРОМОКОДЫ (ДОБАВЛЯЕМ ЭТИ СТРОКИ!)
        elif amount_cents == 99:   # $0.99 - Промокод Basic (было $3.99)
            logger.info("Promotional pricing detected")
            return "basic_sub"
        elif amount_cents == 199:  # $1.99 - Промокод Premium (было $9.99) 
            logger.info("Premium subscription processed")
            return "premium_sub"
        
        # ✅ НЕИЗВЕСТНАЯ СУММА
        else:
            logger.warning("Unrecognized payment amount")
            return "basic_sub"  # По умолчанию
    
    async def _send_renewal_notification(self, user_id, package_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление об успешном продлении"""
        try:
            lang = await get_user_language(user_id)
            
            # ✅ ИСПОЛЬЗУЕМ ЛОКАЛИЗОВАННОЕ СООБЩЕНИЕ
            message = t("webhook_subscription_renewed", lang, package_id=package_id)
            
            # Отправляем сообщение через бота
            await self.bot.send_message(user_id, message)
            
        except Exception as e:
            logger.error("Renewal notification failed")
    
    async def _send_payment_failed_notification(self, user_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление о неудачном платеже"""
        try:
            lang = await get_user_language(user_id)
            
            # ✅ ИСПОЛЬЗУЕМ ЛОКАЛИЗОВАННОЕ СООБЩЕНИЕ
            message = t("webhook_payment_failed", lang)
            
            # Отправляем сообщение через бота
            await self.bot.send_message(user_id, message)
            
        except Exception as e:
            logger.error("Payment failure notification failed")

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
    
    logger.info(f"Webhook server started on port {port}")
    
    return runner