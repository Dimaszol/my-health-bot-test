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
        Обрабатывает webhook от Make.com с событиями Stripe
        
        Ожидаемые данные:
        Подписки: {
            "event_type": "invoice.payment_succeeded",
            "user_id": "cus_...",
            "subscription_id": "sub_...", 
            "amount": "399"
        }
        
        Разовые платежи: {
            "event_type": "checkout.session.completed",
            "session_id": "cs_...",
            "user_id": "123456",
            "amount": "199"
        }
        """
        try:
            # Получаем данные от Make.com
            data = await request.json()
            
            # Логируем полученные данные
            logger.info("Webhook received from payment provider")
            
            # Извлекаем информацию
            event_type = data.get('event_type')
            stripe_customer_id = data.get('user_id')
            subscription_id = data.get('subscription_id')
            
            # ✅ ИСПРАВЛЕНИЕ 1: Конвертируем amount в число (Make.com передает строку)
            amount_raw = data.get('amount', 0)
            try:
                amount = int(amount_raw) if amount_raw else 0
            except (ValueError, TypeError):
                amount = 0
            
            if not event_type:
                return web.json_response(
                    {"status": "error", "message": "Missing event_type"}, 
                    status=400
                )
            
            # Обрабатываем разные типы событий
            if event_type == 'invoice.payment_succeeded':
                result = await self._handle_successful_payment(
                    stripe_customer_id, subscription_id, amount
                )
            elif event_type == 'invoice.payment_failed':
                result = await self._handle_failed_payment(
                    stripe_customer_id, subscription_id
                )
            elif event_type == 'invoice.created':
                result = await self._handle_invoice_created(
                    stripe_customer_id, subscription_id
                )
            elif event_type == 'checkout.session.completed':
                # ✅ ИСПРАВЛЕНИЕ 2: Добавляем обработку разовых платежей
                session_id = data.get('session_id')
                user_id_from_metadata = data.get('user_id')
                
                if session_id:
                    # Автоматически обрабатываем через существующую логику
                    try:
                        from stripe_manager import StripeManager
                        success, message = await StripeManager.handle_successful_payment(session_id)
                        
                        if success:
                            result = {
                                "status": "success",
                                "message": f"One-time payment processed: {message}",
                                "session_id": session_id
                            }
                            
                            # ✅ ЛОКАЛИЗОВАННОЕ уведомление пользователю
                            if user_id_from_metadata:
                                try:
                                    user_id = int(user_id_from_metadata)
                                    lang = await get_user_language(user_id)
                                    
                                    # ✅ ИСПОЛЬЗУЕМ ЛОКАЛИЗОВАННОЕ СООБЩЕНИЕ
                                    localized_message = t("webhook_payment_processed_auto", lang, message=message)
                                    
                                    await self.bot.send_message(
                                        user_id,
                                        localized_message,
                                        parse_mode="HTML"
                                    )
                                except Exception as notify_error:
                                    pass
                        else:
                            result = {
                                "status": "error", 
                                "message": f"Payment processing failed: {message}"
                            }
                    except Exception as e:
                        result = {
                            "status": "error",
                            "message": f"Exception during payment processing: {str(e)}"
                        }
                else:
                    result = {"status": "error", "message": "Missing session_id"}
            else:
                logger.warning("Unknown webhook event type received")
                result = {"status": "ignored", "message": f"Event {event_type} ignored"}
            
            # Возвращаем результат
            return web.json_response({
                "status": "success",
                "message": "Webhook processed successfully",
                "event_type": event_type,
                "result": result,
                "processed_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error("Webhook processing error")
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