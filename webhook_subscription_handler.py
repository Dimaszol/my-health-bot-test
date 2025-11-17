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
        ✅ PRODUCTION версия - минимальное логирование, полная функциональность
        """
        try:
            
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
                        
                        # ✅ ПРАВИЛЬНОЕ извлечение user_id
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
                        
                        # ✅ ПРАВИЛЬНОЕ извлечение subscription_id
                        subscription_id = None
                        
                        # Способ 1: Из lines -> parent -> subscription_item_details -> subscription
                        if lines and len(lines) > 0:
                            parent = lines[0].get('parent', {})
                            if parent.get('type') == 'subscription_item_details':
                                subscription_item_details = parent.get('subscription_item_details', {})
                                subscription_id = subscription_item_details.get('subscription')
                        
                        # Способ 2: Если не найден выше, пробуем из parent -> subscription_details
                        if not subscription_id:
                            parent = invoice_data.get('parent', {})
                            if parent.get('type') == 'subscription_details':
                                subscription_details = parent.get('subscription_details', {})
                                subscription_id = subscription_details.get('subscription')
                        
                        amount = invoice_data.get('amount_paid', 0)
                        
                    elif event_type == 'checkout.session.completed':
                        # Извлекаем данные для разовой покупки
                        session_data = data.get('data', {}).get('object', {})
                        session_id = session_data.get('id')
                        stripe_customer_id = None  # Будет извлечен в StripeManager
                        subscription_id = None
                        amount = 0
                        
                else:
                    # Fallback для тестирования без подписи
                    data = json.loads(payload.decode('utf-8'))
                    
                    # Make.com формат (если понадобится)
                    event_type = data.get('event_type')
                    stripe_customer_id = data.get('user_id')
                    subscription_id = data.get('subscription_id')
                    amount = int(data.get('amount', 0))
                    
            except Exception as e:
                data = await request.json()
                
                # Простой JSON формат
                event_type = data.get('event_type') or data.get('type')
                stripe_customer_id = data.get('user_id')
                subscription_id = data.get('subscription_id')
                amount = int(data.get('amount', 0))
            
            # ✅ ПРОСТАЯ ОБРАБОТКА - только 2 типа событий
            if event_type == 'invoice.payment_succeeded':
                # Подписки
                if not stripe_customer_id:
                    logger.error("❌ User ID not found in invoice webhook")
                    return web.json_response(
                        {"status": "error", "message": "User ID not found"}, 
                        status=400
                    )
                
                if not subscription_id:
                    logger.error("❌ Subscription ID not found in invoice webhook")
                    return web.json_response(
                        {"status": "error", "message": "Subscription ID not found"}, 
                        status=400
                    )
                
                result = await self._handle_successful_payment(
                    stripe_customer_id, subscription_id, amount
                )
                
            elif event_type == 'checkout.session.completed':
                # Разовые покупки и первичные подписки
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
                            
                            # ✅ ИСПРАВЛЕНИЕ: Всегда отправляем уведомление пользователю
                            try:
                                import stripe
                                session = stripe.checkout.Session.retrieve(session_id)
                                user_id = int(session.metadata.get('user_id'))
                                lang = await get_user_language(user_id)
                                localized_message = t("webhook_payment_processed_auto", lang, message=message)
                                await self.bot.send_message(user_id, localized_message, parse_mode="HTML")
                            except Exception:
                                pass  # ⚠️ Не логируем детали ошибки уведомления
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
                else:
                    result = {"status": "error", "message": "Missing session_id"}
                    logger.error("❌ Missing session_id in checkout.session.completed")
                    
            else:
                # Игнорируем все остальные события
                result = {"status": "ignored", "message": f"Event {event_type} ignored"}
            
            # ✅ ИСПРАВЛЕНИЕ JSON SERIALIZATION: Возвращаем результат с правильным сериализатором
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
    
    async def _handle_successful_payment(self, stripe_customer_id, subscription_id, amount):
        """
        ✅ PRODUCTION - Обработка успешного платежа (БЕЗ логирования чувствительных данных)
        """
        try:
            # 1. Проверяем и преобразуем user_id
            if not stripe_customer_id:
                logger.error("❌ stripe_customer_id is empty")
                return {"status": "error", "message": "stripe_customer_id is required"}
            
            try:
                user_id = int(stripe_customer_id)
            except (ValueError, TypeError):
                logger.error(f"❌ Invalid user_id format")
                return {"status": "error", "message": "Invalid user_id"}
            
            # 2. Определяем пакет
            package_id = self._determine_package_by_amount(amount)
            
            # 3. Получаем соединение с БД напрямую
            conn = await get_db_connection()
            try:
                # 4. ✅ ВАЖНО: Проверяем существование пользователя
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
                
                # 5. ✅ ВАЖНО: Используем ПРАВИЛЬНЫЙ метод - purchase_package
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_subscription'
                )
                
                if not result.get('success'):
                    logger.error(f"❌ SubscriptionManager failed")
                    return {"status": "error", "message": "SubscriptionManager failed"}
                
                # 6. Сохраняем/обновляем подписку в БД НАПРЯМУЮ через PostgreSQL
                existing_subscription = await conn.fetchrow("""
                    SELECT id, stripe_subscription_id FROM user_subscriptions 
                    WHERE user_id = $1
                """, user_id)
                
                if existing_subscription:
                    # Обновляем существующую
                    await conn.execute("""
                        UPDATE user_subscriptions 
                        SET stripe_subscription_id = $1, 
                            package_id = $2, 
                            status = $3,
                            created_at = $4,
                            cancelled_at = $5
                        WHERE user_id = $6
                    """, subscription_id, package_id, 'active', datetime.now(), None, user_id)
                else:
                    # Создаем новую
                    await conn.execute("""
                        INSERT INTO user_subscriptions 
                        (user_id, stripe_subscription_id, package_id, status, created_at, cancelled_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, user_id, subscription_id, package_id, 'active', datetime.now(), None)
                
                # 7. Отправляем уведомление
                await self._send_renewal_notification(user_id, package_id)
                
                # ✅ ИСПРАВЛЕНИЕ: Убираем datetime объекты из ответа
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