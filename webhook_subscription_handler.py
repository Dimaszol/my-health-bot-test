# webhook_subscription_handler.py - PRODUCTION VERSION (Secure + Complete)

import json
import logging
from datetime import datetime
from aiohttp import web
from subscription_manager import SubscriptionManager
from db_postgresql import get_user_language, t, get_db_connection, release_db_connection
import asyncio

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
                    # ✅ ИСПРАВЛЕНО: Используем session из webhook payload, НЕ делаем retrieve
                    payment_type = session_data.get('metadata', {}).get('type')
                    
                    # ✅ ОБРАБОТКА ONE-TIME DOCUMENT
                    if payment_type == 'one_time_document':
                        result = await self._handle_one_time_document_payment(session_data)
                        # Сразу возвращаем результат, не идём дальше
                        return web.json_response({
                            "status": "success",
                            "message": "Webhook processed successfully",
                            "event_type": event_type,
                            "result": result,
                            "processed_at": datetime.now().isoformat()
                        })
                    
                    # Стандартная обработка подписок и пакетов
                    from stripe_manager import StripeManager
                    success, message = await StripeManager.handle_successful_payment(session_id)
                    
                    if success:
                        result = {
                            "status": "success",
                            "message": f"Payment processed: {message}",
                            "session_id": session_id
                        }
                        # ✅ УБРАЛИ отправку Telegram-сообщений
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
            
            # ✅ ОБРАБОТКА invoice.payment_failed
            elif event_type == 'invoice.payment_failed':
                invoice_data = event.get('data', {}).get('object', {})
                stripe_customer_id = invoice_data.get('customer')
                result = await self._handle_payment_failed(stripe_customer_id)

            # ✅ ОБРАБОТКА customer.subscription.deleted
            elif event_type == 'customer.subscription.deleted':
                subscription_data = event.get('data', {}).get('object', {})
                stripe_customer_id = subscription_data.get('customer')
                result = await self._handle_subscription_deleted(stripe_customer_id)

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

    async def _handle_payment_failed(self, stripe_customer_id: str):
        """Обрабатывает неудачный платёж - только логируем"""
        try:
            if not stripe_customer_id:
                return {"status": "error", "message": "No customer_id"}
            
            conn = await get_db_connection()
            try:
                user_data = await conn.fetchrow("""
                    SELECT user_id FROM user_subscriptions 
                    WHERE stripe_customer_id = $1
                """, stripe_customer_id)
                
                if not user_data:
                    return {"status": "error", "message": "User not found"}
                
                logger.info("⚠️ Payment failed event received")
                return {"status": "success", "message": "Payment failed logged"}
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error("❌ Error handling payment_failed")
            return {"status": "error", "message": "Handler failed"}

    async def _handle_subscription_deleted(self, stripe_customer_id: str):
        """Обрабатывает удаление подписки - деактивирует в БД"""
        try:
            if not stripe_customer_id:
                return {"status": "error", "message": "No customer_id"}
            
            conn = await get_db_connection()
            try:
                user_data = await conn.fetchrow("""
                    SELECT user_id FROM user_subscriptions 
                    WHERE stripe_customer_id = $1
                """, stripe_customer_id)
                
                if not user_data:
                    return {"status": "error", "message": "User not found"}
                
                user_id = user_data['user_id']
                
                # Деактивируем подписку в БД
                await conn.execute("""
                    UPDATE user_subscriptions 
                    SET status = 'cancelled', cancelled_at = $1
                    WHERE stripe_customer_id = $2
                """, datetime.now(), stripe_customer_id)
                
                # Сбрасываем на free через существующий метод
                await SubscriptionManager.fix_orphaned_subscription_state(user_id)
                
                logger.info("✅ Subscription deactivated")
                return {"status": "success", "message": "Subscription deactivated"}
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error("❌ Error handling subscription_deleted")
            return {"status": "error", "message": "Handler failed"}

    async def _handle_one_time_document_payment(self, session_data):
        """
        Обрабатывает оплату разового анализа документа
        ✅ БЕЗ тяжёлой логики - только идемпотентная запись
        ✅ Использует session из webhook payload
        ✅ НЕ отправляет Telegram-сообщения
        """
        try:
            from db_postgresql import execute_query, fetch_one
            
            # Извлекаем данные из session payload
            session_id = session_data.get('id')
            metadata = session_data.get('metadata', {})
            user_id = int(metadata.get('user_id'))
            document_id = int(metadata.get('document_id'))
            
            logger.info(f"💳 One-time document payment: user={user_id}, doc={document_id}")
            
            # 1. Проверка идемпотентности
            existing = await fetch_one("""
                SELECT id FROM transactions 
                WHERE stripe_session_id = $1 AND status = 'completed'
            """, (session_id,))
            
            if existing:
                logger.info(f"⚠️ Payment already processed: {session_id}")
                return {
                    "status": "success",
                    "message": "Payment already processed",
                    "document_id": document_id
                }
            
            # 2. Сохраняем транзакцию
            await execute_query("""
                INSERT INTO transactions 
                (user_id, stripe_session_id, amount_usd, package_type, 
                 payment_method, status, documents_granted, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """, (
                user_id,
                session_id,
                2.49,
                'one_time_document',
                'stripe',
                'completed',
                1
            ))
            
            # 3. Добавляем 1 document credit + 5 детальных консультаций
            conn = await get_db_connection()
            try:
                await conn.execute("""
                    UPDATE user_limits 
                    SET documents_left = documents_left + 1,
                        updated_at = NOW()
                    WHERE user_id = $1
                """, user_id)
                await conn.execute("""
                    UPDATE user_limits 
                    SET gpt4o_queries_left = gpt4o_queries_left + 5 
                    WHERE user_id = $1
                """, user_id)
                # ✅ Оплата подтверждена — помечаем документ
                await conn.execute("""
                    UPDATE documents SET payment_confirmed = true WHERE id = $1
                """, document_id)
            finally:
                await release_db_connection(conn)
            
            logger.info(f"✅ Added +1 document credit to user {user_id}")
            
            # 4. Запускаем обработку в фоне
            asyncio.create_task(self._process_document_background(document_id, user_id))
            logger.info(f"📋 Started background processing for document {document_id}")
            
            return {
                "status": "success",
                "message": "One-time document payment processed",
                "document_id": document_id,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing one-time document payment: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    async def _process_document_background(self, document_id: int, user_id: int):
        """
        Фоновая обработка документа после one-time оплаты
        ✅ Не блокирует webhook
        ✅ Использует существующий process_document
        ✅ Автоматически списывает лимиты
        """
        try:
            from document_processor import process_document
            from subscription_manager import spend_document_limit
            
            logger.info(f"🔄 Starting background processing for document {document_id}")
            
            # Получаем данные документа
            conn = await get_db_connection()
            try:
                doc = await conn.fetchrow("""
                    SELECT file_path, additional_context, file_type 
                    FROM documents 
                    WHERE id = $1 AND user_id = $2
                """, document_id, user_id)
                
                if not doc:
                    logger.error(f"❌ Document {document_id} not found for processing")
                    return
                
                file_path = doc['file_path']
                additional_context = doc['additional_context'] or ''
                
                # Получаем язык пользователя
                from db_postgresql import get_user_language
                lang = await get_user_language(user_id)
                
            finally:
                await release_db_connection(conn)
            
            # Если файл в Supabase - скачиваем локально
            import tempfile
            import os

            if file_path.startswith("users/"):
                # Скачиваем из Supabase Storage
                from supabase_storage import get_storage_manager
                storage = get_storage_manager()
                
                # Создаём временный файл
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1])
                local_file_path = temp_file.name
                temp_file.close()
                
                # Скачиваем
                success = await storage.download_file(
                    storage_path=file_path,
                    local_path=local_file_path
                )
                
                if not success:
                    logger.error(f"❌ Failed to download file from Supabase: {file_path}")
                    return
            else:
                # Локальный файл - используем как есть
                local_file_path = file_path

            try:
                # Обрабатываем документ (существующая функция)
                result = await process_document(
                    file_path=local_file_path,
                    user_id=user_id,
                    lang=lang,
                    additional_context=additional_context
                )
                                
            finally:
                # Удаляем временный файл если был скачан из Supabase
                if file_path.startswith("users/") and os.path.exists(local_file_path):
                    try:
                        os.remove(local_file_path)
                    except:
                        pass
            
            if not result.get('success'):
                error_message = result.get('message', 'Processing failed')
                logger.error(f"❌ Document {document_id} processing failed: {error_message}")
                
                # Сохраняем ошибку в БД чтобы polling увидел
                conn = await get_db_connection()
                try:
                    await conn.execute("""
                        UPDATE documents 
                        SET title = $1,
                            confirmed = false
                        WHERE id = $2
                    """, error_message[:200], document_id)  # Ограничиваем длину сообщения
                finally:
                    await release_db_connection(conn)
                
                return
            
            # Сохраняем результаты в БД
            conn = await get_db_connection()
            try:                                
                # Добавляем в векторную базу
                try:
                    from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
                    summary = result.get('summary', '')
                    if summary:
                        chunks = await split_into_chunks(summary, document_id, user_id)
                        await add_chunks_to_vector_db(document_id, user_id, chunks)
                except Exception as e:
                    logger.warning(f"⚠️ Vector DB error (non-critical): {e}")
                
                # ✅ НОВОЕ: Извлекаем медицинские события в timeline
                try:
                    from medical_timeline import update_medical_timeline_on_document_upload
                    await update_medical_timeline_on_document_upload(
                        user_id=user_id,
                        document_id=document_id,
                        document_text=result.get('raw_text', ''),
                        use_gemini=False
                    )
                    logger.info(f"✅ Medical timeline updated for document {document_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Medical timeline error (non-critical): {e}")

                # Первое сообщение для обсудить
                try:
                    from document_questions import generate_and_save_first_message
                    from medical_timeline import get_document_importance
                    
                    importance = await get_document_importance(document_id, user_id)
                    
                    await generate_and_save_first_message(
                        document_id=document_id,
                        user_id=user_id,
                        full_analysis=result.get('full_analysis'),
                        importance=importance,
                        lang=lang
                    )
                    logger.info(f"✅ First message generated for document {document_id}")
                except Exception as e:
                    logger.warning(f"⚠️ First message generation error (non-critical): {e}")

                # Списываем лимит документов
                await spend_document_limit(user_id)
                
                # Обновляем документ
                from datetime import datetime as dt
                document_date_str = result.get('document_date')
                document_date_obj = None
                if document_date_str:
                    try:
                        document_date_obj = dt.strptime(document_date_str, '%Y-%m-%d').date()
                    except:
                        pass

                await conn.execute("""
                    UPDATE documents 
                    SET full_analysis = $1,
                        title = $2,
                        confirmed = true,
                        raw_text = $3,
                        summary = $4,
                        document_type = $5,
                        subtype = $6,
                        first_analysis = $7,
                        document_date = $8
                    WHERE id = $9
                """, 
                    result.get('full_analysis'),
                    result.get('title', 'Document'),
                    result.get('raw_text', ''),
                    result.get('summary', ''),
                    result.get('document_type'),
                    result.get('subtype'),
                    result.get('first_analysis'),
                    document_date_obj,  # <-- ТЕПЕРЬ date объект
                    document_id
                )

                logger.info(f"✅ Document {document_id} processed and saved successfully")
                
            finally:
                await release_db_connection(conn)
            
        except Exception as e:
            logger.error(f"❌ Critical error in background processing for document {document_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())

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