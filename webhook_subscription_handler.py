# webhook_subscription_handler.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import json
import logging
from datetime import datetime
from aiohttp import web
from subscription_manager import SubscriptionManager
from db_postgresql import get_user_language, t, get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

class SubscriptionWebhookHandler:
    """Обработчик webhook для событий подписок от Stripe"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_subscription_webhook(self, request):
        """
        ✅ ИСПРАВЛЕННАЯ версия - правильное извлечение данных и прямой PostgreSQL
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
                        
                        # Способ 3: Прямо из invoice (если есть)
                        if not subscription_id:
                            subscription_id = invoice_data.get('subscription')
                        
                        amount = invoice_data.get('amount_paid', 0)
                        
                        logger.info(f"📄 Invoice payment extracted:")
                        logger.info(f"   user_id: {stripe_customer_id}")
                        logger.info(f"   subscription_id: {subscription_id}")
                        logger.info(f"   amount: {amount}")
                        
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
            
            logger.info(f"🎯 Processing: {event_type}, user: {stripe_customer_id}, subscription: {subscription_id}, amount: {amount}")
            
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
        """Обрабатывает успешное продление подписки - ПРЯМОЙ PostgreSQL"""
        try:
            logger.info(f"🔍 НАЧАЛО ОБРАБОТКИ: user_id={stripe_customer_id}, sub_id={subscription_id}, amount={amount}")
            
            # 1. Проверяем и преобразуем user_id
            if not stripe_customer_id:
                logger.error("❌ stripe_customer_id пустой")
                return {"status": "error", "message": "stripe_customer_id is required"}
            
            try:
                user_id = int(stripe_customer_id)
                logger.info(f"✅ user_id преобразован: {user_id}")
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Не удалось преобразовать user_id: {stripe_customer_id}, ошибка: {e}")
                return {"status": "error", "message": f"Invalid user_id: {stripe_customer_id}"}
            
            # 2. Определяем пакет
            package_id = self._determine_package_by_amount(amount)
            logger.info(f"📦 Определен пакет: {package_id} для суммы {amount}")
            
            # 3. Получаем соединение с БД напрямую
            conn = await get_db_connection()
            try:
                # 4. Проверяем существование пользователя
                user_exists = await conn.fetchrow("""
                    SELECT user_id FROM users WHERE user_id = $1
                """, user_id)
                
                if not user_exists:
                    logger.warning(f"⚠️ Пользователь {user_id} не найден в БД, создаем...")
                    await conn.execute("""
                        INSERT INTO users (user_id, name, created_at) 
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                    """, user_id, f"User {user_id}", datetime.now())
                
                # 5. Обновляем лимиты через SubscriptionManager
                logger.info(f"💳 Вызываем SubscriptionManager.purchase_package...")
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_subscription'
                )
                
                logger.info(f"💳 Результат SubscriptionManager: {result}")
                
                if not result.get('success'):
                    logger.error(f"❌ SubscriptionManager вернул ошибку: {result}")
                    return {"status": "error", "message": f"SubscriptionManager failed: {result.get('error')}"}
                
                # 6. Сохраняем/обновляем подписку в БД НАПРЯМУЮ через PostgreSQL
                logger.info(f"💾 Сохраняем подписку в user_subscriptions...")
                
                # Проверяем, есть ли уже подписка для этого пользователя
                existing_subscription = await conn.fetchrow("""
                    SELECT id, stripe_subscription_id FROM user_subscriptions 
                    WHERE user_id = $1
                """, user_id)
                
                logger.info(f"🔍 Существующая подписка: {dict(existing_subscription) if existing_subscription else None}")
                
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
                    logger.info(f"✅ Обновлена существующая подписка для user_id={user_id}")
                else:
                    # Создаем новую
                    await conn.execute("""
                        INSERT INTO user_subscriptions 
                        (user_id, stripe_subscription_id, package_id, status, created_at, cancelled_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, user_id, subscription_id, package_id, 'active', datetime.now(), None)
                    logger.info(f"✅ Создана новая подписка для user_id={user_id}")
                
                # 7. Проверяем, что запись действительно сохранилась
                saved_subscription = await conn.fetchrow("""
                    SELECT user_id, stripe_subscription_id, package_id, status, created_at 
                    FROM user_subscriptions 
                    WHERE user_id = $1
                """, user_id)
                
                logger.info(f"🔍 ПРОВЕРКА: Сохраненная подписка: {dict(saved_subscription) if saved_subscription else None}")
                
                # 8. Отправляем уведомление
                await self._send_renewal_notification(user_id, package_id)
                
                logger.info(f"✅ УСПЕШНО ЗАВЕРШЕНО для user_id={user_id}")
                
                return {
                    "status": "success",
                    "message": "Subscription renewed",
                    "user_id": user_id,
                    "package_id": package_id,
                    "stripe_subscription_id": subscription_id,
                    "new_limits": {
                        "documents": result.get('new_documents'),
                        "queries": result.get('new_queries')
                    },
                    "database_record": dict(saved_subscription) if saved_subscription else None
                }
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ ОШИБКА В _handle_successful_payment: {e}")
            import traceback
            logger.error(f"❌ Полный traceback: {traceback.format_exc()}")
            return {"status": "error", "message": f"Exception: {str(e)}"}
    
    def _determine_package_by_amount(self, amount_cents):
        """Определяет тип пакета по сумме платежа с подробным логированием"""
        
        logger.info(f"🔍 Определяем пакет для суммы: {amount_cents} центов")
        
        # ✅ ОБЫЧНЫЕ ЦЕНЫ
        if amount_cents == 399:  # $3.99 - Basic
            logger.info("📦 Определен пакет: basic_sub (обычная цена)")
            return "basic_sub"
        elif amount_cents == 999:  # $9.99 - Premium  
            logger.info("📦 Определен пакет: premium_sub (обычная цена)")
            return "premium_sub"
        elif amount_cents == 199:  # $1.99 - Extra pack
            logger.info("📦 Определен пакет: extra_pack")
            return "extra_pack"
        
        # ✅ ПРОМОКОДЫ
        elif amount_cents == 99:   # $0.99 - Промокод Basic
            logger.info("📦 Определен пакет: basic_sub (промокод)")
            return "basic_sub"
        elif amount_cents == 299:  # $2.99 - Промокод Premium (если есть)
            logger.info("📦 Определен пакет: premium_sub (промокод)")
            return "premium_sub"
        
        # ✅ НЕИЗВЕСТНАЯ СУММА
        else:
            logger.warning(f"⚠️ Неизвестная сумма {amount_cents}, используем premium_sub по умолчанию")
            return "premium_sub"  # Для $9.99 по умолчанию premium
    
    async def _send_renewal_notification(self, user_id, package_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление об успешном продлении"""
        try:
            lang = await get_user_language(user_id)
            
            # ✅ ИСПОЛЬЗУЕМ ЛОКАЛИЗОВАННОЕ СООБЩЕНИЕ
            message = t("webhook_subscription_renewed", lang, package_id=package_id)
            
            # Отправляем сообщение через бота
            await self.bot.send_message(user_id, message)
            
        except Exception as e:
            logger.error(f"Renewal notification failed: {e}")
    
    async def _send_payment_failed_notification(self, user_id):
        """✅ ЛОКАЛИЗОВАННАЯ версия - Отправляет уведомление о неудачном платеже"""
        try:
            lang = await get_user_language(user_id)
            
            # ✅ ИСПОЛЬЗУЕМ ЛОКАЛИЗОВАННОЕ СООБЩЕНИЕ
            message = t("webhook_payment_failed", lang)
            
            # Отправляем сообщение через бота
            await self.bot.send_message(user_id, message)
            
        except Exception as e:
            logger.error(f"Payment failure notification failed: {e}")

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