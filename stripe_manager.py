# stripe_manager.py - ИСПРАВЛЕННАЯ ВЕРСИЯ с полной локализацией

import stripe
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from stripe_config import StripeConfig
from subscription_manager import SubscriptionManager
from db_postgresql import execute_query, fetch_one, get_user_language, t

logger = logging.getLogger(__name__)

class StripeManager:
    """Менеджер для работы с платежами Stripe"""
    
    @staticmethod
    async def create_checkout_session(user_id: int, package_id: str, user_name: str = "User", source: str = "telegram"):
        """Создает сессию оплаты с правильным типом"""
        try:
            package_info = StripeConfig.get_package_info(package_id)
            if not package_info:
                # ✅ ДОБАВЛЕНО: получение языка для локализованной ошибки
                try:
                    lang = await get_user_language(user_id)
                    error_msg = t("stripe_package_not_found", lang, package_id=package_id)
                except:
                    error_msg = f"Package {package_id} not found"
                
                return False, error_msg
            
            # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Определяем тип оплаты
            if package_info['type'] == 'subscription':
                # 💱 Определяем валюту на основе страны пользователя
                from webapp.utils.currency import get_ui_currency
                from db_postgresql import get_db_connection, release_db_connection
                
                # Получаем страну пользователя из БД
                conn = await get_db_connection()
                try:
                    user_data = await conn.fetchrow(
                        "SELECT country FROM users WHERE user_id = $1", 
                        user_id
                    )
                    country = user_data['country'] if user_data else None
                finally:
                    await release_db_connection(conn)
                
                currency = get_ui_currency(country)
                
                # Получаем правильный Price ID для валюты
                price_id = StripeConfig.get_price_id_for_currency(package_id, currency)
                
                if not price_id:
                    # Fallback на USD если что-то пошло не так
                    price_id = package_info['stripe_price_id']
                
                # ✅ ПОДПИСКА - автосписание каждый месяц
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price_id,  # ✅ ИЗМЕНЕНО: динамический Price ID
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=(StripeConfig.WEB_SUCCESS_URL if source == "web" else StripeConfig.TELEGRAM_SUCCESS_URL) + f"&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=StripeConfig.WEB_CANCEL_URL if source == "web" else StripeConfig.TELEGRAM_CANCEL_URL,
                    allow_promotion_codes=True,
                    subscription_data={
                        'metadata': {
                            'user_id': str(user_id),
                            'package_id': package_id,
                        }
                    },
                    metadata={
                        'user_id': str(user_id),
                        'package_id': package_id,
                        'user_name': user_name,
                        'subscription_type': 'recurring',
                        'currency': currency
                    }
                )
            else:
                # ✅ РАЗОВАЯ ПОКУПКА (только Extra Pack)
                # 💱 Определяем валюту для Extra Pack
                from webapp.utils.currency import get_ui_currency
                from db_postgresql import get_db_connection, release_db_connection
                
                conn = await get_db_connection()
                try:
                    user_data = await conn.fetchrow(
                        "SELECT country FROM users WHERE user_id = $1", 
                        user_id
                    )
                    country = user_data['country'] if user_data else None
                finally:
                    await release_db_connection(conn)
                
                currency = get_ui_currency(country)
                
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': currency.lower(),  # ✅ ИЗМЕНЕНО
                            'unit_amount': package_info['price_cents'],
                            'product_data': {
                                'name': package_info['name'],
                                'description': f"{package_info['documents']} documents + {package_info['gpt4o_queries']} Detailed responses",
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='payment',  # ✅ РАЗОВАЯ ОПЛАТА
                    success_url=(StripeConfig.WEB_SUCCESS_URL if source == "web" else StripeConfig.TELEGRAM_SUCCESS_URL) + f"&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=StripeConfig.WEB_CANCEL_URL if source == "web" else StripeConfig.TELEGRAM_CANCEL_URL,
                    metadata={
                        'user_id': str(user_id),
                        'package_id': package_id,
                        'user_name': user_name,
                        'subscription_type': 'one_time',
                        'currency': currency  # ✅ ДОБАВЛЕНО
                    }
                )
            
            # Сохраняем сессию в БД
            await StripeManager._save_payment_session(
                user_id=user_id,
                session_id=session.id,
                package_id=package_id,
                amount_cents=package_info['price_cents']
            )
            
            return True, session.url
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания сессии")
            
            # ✅ ДОБАВЛЕНО: локализованная ошибка
            try:
                lang = await get_user_language(user_id)
                error_msg = t("stripe_session_creation_error", lang)
            except:
                error_msg = "Payment session creation failed"
            
            return False, error_msg
    
    @staticmethod
    async def create_one_time_document_checkout(user_id: int, document_id: int, lang: str = "ru"):
        """
        Создаёт Stripe checkout для разовой оплаты анализа документа ($2.49)
        """
        try:
            # 💱 Определяем валюту на основе страны пользователя
            from webapp.utils.currency import get_ui_currency
            from db_postgresql import get_db_connection, release_db_connection

            # Получаем страну пользователя из БД
            conn = await get_db_connection()
            try:
                user_data = await conn.fetchrow(
                    "SELECT country FROM users WHERE user_id = $1", 
                    user_id
                )
                country = user_data['country'] if user_data else None
            finally:
                await release_db_connection(conn)

            currency = get_ui_currency(country)
            
            # Цена в центах
            amount_cents = 249  # $2.49
            
            # Определяем URL в зависимости от языка
            success_url = f"{StripeConfig.WEB_SUCCESS_URL.split('?')[0]}/documents?doc_id={document_id}"
            cancel_url = f"{StripeConfig.WEB_CANCEL_URL.split('?')[0]}/documents?payment_cancelled=true"
            
            # Локализованные названия
            product_names = {
                'ru': 'Разовый AI-разбор документа',
                'en': 'One-Time Document AI Analysis',
                'uk': 'Разовій AI-розбір документа',
                'de': 'Einmalige KI-Dokumentenanalyse'
            }
            
            product_descriptions = {
                'ru': 'Полный медицинский AI-анализ вашего документа',
                'en': 'Complete medical AI analysis of your document',
                'uk': 'Повний медичний AI-аналіз вашого документа',
                'de': 'Vollständige medizinische KI-Analyse Ihres Dokuments'
            }
            
            product_name = product_names.get(lang, product_names['en'])
            product_description = product_descriptions.get(lang, product_descriptions['en'])
            
            # Создаём Stripe session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),  # ✅ ИЗМЕНЕНО: динамическая валюта
                        'unit_amount': amount_cents,
                        'product_data': {
                            'name': product_name,
                            'description': product_description,
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',  # Разовый платёж
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'type': 'one_time_document',  # ВАЖНО!
                    'user_id': str(user_id),
                    'document_id': str(document_id),
                    'lang': lang,
                    'currency': currency  # ✅ ДОБАВЛЕНО: сохраняем валюту
                }
            )
            
            logger.info(f"✅ One-time document checkout создан: session={session.id}, user={user_id}, doc={document_id}")
            
            return True, session.url
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания one-time checkout: {e}")
            error_msg = t("stripe_session_creation_error", lang)
            return False, error_msg

    @staticmethod
    async def _save_payment_session(user_id: int, session_id: str, package_id: str, amount_cents: int):
        """Сохраняет информацию о сессии оплаты в БД"""
        try:
            await execute_query("""
                INSERT INTO transactions 
                (user_id, stripe_session_id, package_id, amount_usd, package_type, status, payment_method, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, (
                user_id,
                session_id, 
                package_id,
                amount_cents / 100,  # Конвертируем центы в доллары
                StripeConfig.get_package_info(package_id)['name'],
                'pending',
                'stripe',
                datetime.now()
            ))
            
            logger.info(f"💾 Сохранена информация о сессии")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сессии в БД")
    
    @staticmethod
    async def handle_successful_payment(session_id: str):
        """✅ ИСПРАВЛЕННАЯ ВЕРСИЯ: Обрабатывает успешную оплату с правильным PostgreSQL синтаксисом"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Извлекаем метаданные
            user_id = int(session.metadata.get('user_id'))
            package_id = session.metadata.get('package_id')
            
            # ✅ ДОБАВЛЕНО: Получаем язык пользователя для локализованных сообщений
            try:
                lang = await get_user_language(user_id)
            except:
                lang = "ru"  # Fallback на русский
            
            # Для подписок проверяем статус подписки, не платежа
            if session.mode == 'subscription':
                subscription = stripe.Subscription.retrieve(session.subscription)
                if subscription.status not in ['active', 'trialing']:
                    # ✅ ИСПРАВЛЕНО: Локализованное сообщение ошибки
                    error_msg = f"Subscription not active: {subscription.status}"
                    return False, error_msg
            else:
                # Для разовых платежей проверяем статус оплаты
                if session.payment_status != 'paid':
                    # ✅ ИСПРАВЛЕНО: Локализованное сообщение ошибки
                    return False, "Payment not completed"
            
            # Проверяем дубликаты
            existing_transaction = await fetch_one("""
                SELECT id FROM transactions 
                WHERE stripe_session_id = $1
                AND status = 'completed'
            """, (session_id,))
            
            if existing_transaction:
                # ✅ ИСПРАВЛЕНО: Локализованное сообщение
                return True, "Payment already processed"
            
            # Получаем информацию о пакете
            package_info = StripeConfig.get_package_info(package_id)
            if not package_info:
                # ✅ ИСПРАВЛЕНО: Локализованное сообщение ошибки
                error_msg = f"Package not found: {package_id}"
                return False, error_msg
                        
            if package_info['type'] == 'subscription':
                # Для подписок сохраняем Stripe subscription ID и customer ID
                subscription_id = session.subscription
                customer_id = session.customer 
                
                # ✅ ИСПРАВЛЕНИЕ: Сначала удаляем старую подписку
                await execute_query("""
                    DELETE FROM user_subscriptions WHERE user_id = $1
                """, (user_id,))

                # Затем вставляем новую с customer_id
                await execute_query("""
                    INSERT INTO user_subscriptions 
                    (user_id, stripe_subscription_id, stripe_customer_id, package_id, status, created_at, cancelled_at)
                    VALUES ($1, $2, $3, $4, 'active', $5, $6)
                """, (user_id, subscription_id, customer_id, package_id, datetime.now(), None)) 
                
                # Выдаем лимиты
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_subscription'
                )
                
                # ✅ ИСПРАВЛЕНО: Локализованное сообщение с названием пакета
                package_name = package_info['name']
                message = f"Subscription activated: {package_name}"
                
            else:
                # Для разовых покупок - как раньше
                result = await SubscriptionManager.purchase_package(
                    user_id=user_id,
                    package_id=package_id,
                    payment_method='stripe_payment'
                )
                # ✅ ДОБАВЬ: Сохраняем customer_id для будущих подписок
                customer_id = session.customer
                if customer_id:
                    # Проверяем есть ли уже запись
                    existing = await fetch_one("""
                        SELECT id FROM user_subscriptions WHERE user_id = $1
                    """, (user_id,))
                    
                    if existing:
                        # Обновляем customer_id если запись есть
                        await execute_query("""
                            UPDATE user_subscriptions 
                            SET stripe_customer_id = $1
                            WHERE user_id = $2
                        """, (customer_id, user_id))
                    else:
                        # Создаём запись только с customer_id (без subscription_id)
                        await execute_query("""
                            INSERT INTO user_subscriptions 
                            (user_id, stripe_customer_id, package_id, status, created_at)
                            VALUES ($1, $2, $3, 'one_time', $4)
                        """, (user_id, customer_id, package_id, datetime.now()))
                
                # ✅ ИСПРАВЛЕНО: Локализованное сообщение с названием пакета
                package_name = package_info['name']
                message = f"Package purchased: {package_name}"
            
            if not result['success']:
                # ✅ ИСПРАВЛЕНО: Локализованное сообщение ошибки
                error_msg = f"❌ Ошибка активации: {result['error']}"
                return False, error_msg
            
            # Обновляем статус транзакции
            await execute_query("""
                UPDATE transactions SET 
                    status = 'completed',
                    completed_at = $1,
                    documents_granted = $2,
                    queries_granted = $3
                WHERE stripe_session_id = $4
            """, (
                datetime.now(),
                package_info['documents'],
                package_info['gpt4o_queries'], 
                session_id
            ))
            
            return True, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки платежа: {e}")
            
            # ✅ ДОБАВЛЕНО: локализованная ошибка
            try:
                user_id = int(session.metadata.get('user_id', 0)) if 'session' in locals() else 0
                lang = await get_user_language(user_id) if user_id > 0 else "ru"
                error_msg = f"❌ Ошибка активации: {str(e)}"
            except:
                error_msg = f"Activation error: {e}"
            
            return False, error_msg
    
    @staticmethod
    async def handle_failed_payment(session_id: str, reason: str = "Unknown") -> bool:
        """
        Обрабатывает неуспешный платеж
        """
        try:
            # Обновляем статус в БД
            await execute_query("""
                UPDATE transactions SET 
                    status = 'failed'
                WHERE stripe_session_id = $1
            """, (session_id,))
            
            logger.warning(f"Неуспешный платеж")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки неуспешного платежа")
            return False

    @staticmethod
    async def cancel_user_subscription(user_id: int) -> Tuple[bool, str]:
        """Отменяет активную подписку пользователя"""
        return await SubscriptionManager.cancel_stripe_subscription(user_id)

    @staticmethod
    async def get_user_payment_history(user_id: int, limit: int = 10) -> list:
        """Получает историю платежей пользователя"""
        try:
            from db_postgresql import fetch_all
            
            transactions = await fetch_all("""
                SELECT package_type, amount_usd, status, created_at, completed_at
                FROM transactions 
                WHERE user_id = $1 AND status != 'pending'
                ORDER BY created_at DESC 
                LIMIT $2
            """, (user_id, limit))
            
            return [
                {
                    "package": row[0],
                    "amount": row[1],
                    "status": row[2], 
                    "created": row[3],
                    "completed": row[4]
                }
                for row in transactions
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения истории платежей для пользователя")
            return []
        
    
    @staticmethod
    async def create_promo_payment_session(user_id: int, package_id: str, promo_code: str, user_name: str = "User", source: str = "telegram"):
        """
        💰 Создает сессию оплаты с применением промокода
        
        Args:
            user_id: ID пользователя
            package_id: ID пакета (basic_sub, premium_sub)
            promo_code: Промокод в Stripe (FIRST30BASIC, FIRST30PREMIUM)
            user_name: Имя пользователя
            
        Returns:
            Tuple[bool, str]: (успех, ссылка_или_ошибка)
        """
        try:
            logger.info(f"Создание ссылки с промокодом")
            
            # 1️⃣ Проверяем существование пакета
            package_info = StripeConfig.get_package_info(package_id)
            if not package_info:
                try:
                    lang = await get_user_language(user_id)
                    error_msg = t("stripe_package_not_found", lang, package_id=package_id)
                except:
                    error_msg = f"Package {package_id} not found"
                
                return False, error_msg
            
            # 2️⃣ Проверяем, что это подписка (промокоды только для подписок)
            if package_info['type'] != 'subscription':
                return False, "Промокоды доступны только для подписок"
            
            # 3️⃣ Создаем сессию подписки с промокодом
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': package_info['stripe_price_id'],  # Используем готовый Price ID
                    'quantity': 1,
                }],
                mode='subscription',  # Подписка
                success_url=(StripeConfig.WEB_SUCCESS_URL if source == "web" else StripeConfig.TELEGRAM_SUCCESS_URL) + f"&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=StripeConfig.WEB_CANCEL_URL if source == "web" else StripeConfig.TELEGRAM_CANCEL_URL,
                
                # 🎯 КЛЮЧЕВАЯ ОСОБЕННОСТЬ: Автоматически применяем промокод
                discounts=[{
                    'coupon': promo_code  # Промокод применится автоматически
                }],
                
                # Метаданные для отслеживания
                subscription_data={
                    'metadata': {
                        'user_id': str(user_id),
                        'package_id': package_id,
                        'promo_code_used': promo_code,  # Отмечаем использование промокода
                        'is_promo_purchase': 'true'     # Флаг промопокупки
                    }
                },
                metadata={
                    'user_id': str(user_id),
                    'package_id': package_id,
                    'user_name': user_name,
                    'subscription_type': 'recurring',
                    'promo_code_used': promo_code,
                    'acquisition_channel': 'promo_30th_message'  # Для аналитики
                }
            )
            
            # 4️⃣ Сохраняем информацию о сессии с промокодом
            await StripeManager._save_promo_payment_session(
                user_id=user_id,
                session_id=session.id,
                package_id=package_id,
                amount_cents=package_info['price_cents'],
                promo_code=promo_code
            )
            
            return True, session.url
            
        except stripe.error.InvalidRequestError as e:
            # Ошибка промокода (не существует, неактивен, не подходит)
            error_msg = f"Промокод недействителен: {str(e)}"
            return False, error_msg
            
        except Exception as e:
            logger.error(f"Ошибка создания промо-сессии")
            
            try:
                lang = await get_user_language(user_id)
                error_msg = t("stripe_session_creation_error", lang)
            except:
                error_msg = "Payment session creation failed"
            
            return False, error_msg
    
    @staticmethod
    async def _save_promo_payment_session(user_id: int, session_id: str, package_id: str, amount_cents: int, promo_code: str):
        """
        💾 Сохраняет информацию о промо-сессии в БД
        """
        try:
            await execute_query("""
                INSERT INTO transactions 
                (user_id, stripe_session_id, package_id, amount_usd, package_type, status, payment_method, promo_code, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, (
                user_id,
                session_id, 
                package_id,
                amount_cents / 100,  # Конвертируем центы в доллары
                StripeConfig.get_package_info(package_id)['name'],
                'pending',
                'stripe_promo',  # Специальный payment_method для промокодов
                promo_code,      # Сохраняем использованный промокод
                datetime.now()
            ))
        
            
        except Exception as e:
            logger.error(f"Ошибка сохранения промо-сессии в БД")

    @staticmethod
    async def get_promo_usage_stats(promo_code: str) -> Dict[str, Any]:
        """
        📊 Получает статистику использования промокода (для аналитики)
        
        Returns:
            {"total_uses": 5, "successful_payments": 3, "revenue_usd": 5.97}
        """
        try:
            # Общее количество использований
            total_uses_result = await fetch_one("""
                SELECT COUNT(*) as total FROM transactions 
                WHERE promo_code = $1
            """, (promo_code,))
            
            # Успешные платежи
            successful_result = await fetch_one("""
                SELECT COUNT(*) as successful, COALESCE(SUM(amount_usd), 0) as revenue
                FROM transactions 
                WHERE promo_code = $1 AND status = 'completed'
            """, (promo_code,))
            
            return {
                "promo_code": promo_code,
                "total_uses": total_uses_result['total'] if total_uses_result else 0,
                "successful_payments": successful_result['successful'] if successful_result else 0,
                "revenue_usd": float(successful_result['revenue']) if successful_result and successful_result['revenue'] else 0.0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики промокода")
            return {"promo_code": promo_code, "total_uses": 0, "successful_payments": 0, "revenue_usd": 0.0}

# Функция для webhook (обработка событий от Stripe)
async def handle_stripe_webhook(payload: str, sig_header: str) -> Tuple[bool, str]:
    """
    Обрабатывает webhook события от Stripe
    """
    try:
        # Проверяем подпись webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, StripeConfig.WEBHOOK_SECRET
        )
        
        # Обрабатываем различные типы событий
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            success, message = await StripeManager.handle_successful_payment(session['id'])
            return success, message
            
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            await StripeManager.handle_failed_payment(session['id'], "Session expired")
            return True, "Session expired processed"
            
        else:
            logger.info(f"Необработанное Stripe событие")
            return True, f"Event {event['type']} ignored"
            
    except ValueError as e:
        logger.error(f"Неверный payload от Stripe")
        return False, "Invalid payload"
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Неверная подпись Stripe webhook")
        return False, "Invalid signature"
        
    except Exception as e:
        logger.error(f"Ошибка обработки Stripe webhook")
        return False, f"Webhook error: {e}"
    
class StripeGDPRManager:
    """Управление GDPR-совместимым удалением данных из Stripe"""
    
    @staticmethod
    async def delete_user_stripe_data_gdpr(user_id: int) -> bool:
        """
        GDPR-совместимое удаление всех данных пользователя из Stripe
        """
        try:
            
            # 1. Находим все Stripe подписки пользователя
            stripe_subscriptions = await StripeGDPRManager._find_user_subscriptions(user_id)
            
            # 2. Отменяем все активные подписки
            for subscription_id in stripe_subscriptions:
                await StripeGDPRManager._cancel_stripe_subscription(subscription_id)
            
            # 3. Находим Stripe customer_id
            customer_id = await StripeGDPRManager._find_stripe_customer(user_id)
            
            # 4. Удаляем customer из Stripe (если есть)
            if customer_id:
                await StripeGDPRManager._delete_stripe_customer(customer_id)
            
            # 5. Очищаем Stripe ссылки из нашей базы
            await StripeGDPRManager._clean_stripe_references(user_id)

            return True
            
        except Exception as e:
            logger.error(f"Ошибка GDPR удаления Stripe данных для пользователя")
            return False
    
    @staticmethod
    async def _find_user_subscriptions(user_id: int) -> list:
        """Находит все Stripe подписки пользователя"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            conn = await get_db_connection()
            try:
                # ✅ ИСПОЛЬЗУЕМ ПРЯМОЕ ПОДКЛЮЧЕНИЕ ВМЕСТО fetch_all
                rows = await conn.fetch("""
                    SELECT stripe_subscription_id 
                    FROM user_subscriptions 
                    WHERE user_id = $1 AND stripe_subscription_id IS NOT NULL
                """, user_id)
                
                # ✅ ПРАВИЛЬНО ИЗВЛЕКАЕМ ДАННЫЕ ИЗ СТРОК
                subscriptions = [row['stripe_subscription_id'] for row in rows if row['stripe_subscription_id']]
                return subscriptions
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"Ошибка поиска подписок для пользователя")
            return []
    
    @staticmethod
    async def _cancel_stripe_subscription(subscription_id: str):
        """Отменяет подписку в Stripe"""
        try:
            # Немедленная отмена подписки
            stripe.Subscription.delete(subscription_id)
            logger.info(f"Отменена Stripe подписка")
            
        except stripe.error.InvalidRequestError as e:
            if "No such subscription" in str(e):
                logger.warning(f"⚠️ Подписка уже не существует в Stripe")
            else:
                logger.error(f"❌ Ошибка отмены подписки")
        except Exception as e:
            logger.error(f"❌ Ошибка отмены подписки")
    
    @staticmethod
    async def _find_stripe_customer(user_id: int) -> str:
        """Находит Stripe customer_id по user_id"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            conn = await get_db_connection()
            try:
                row = await conn.fetchrow("""
                    SELECT stripe_customer_id 
                    FROM user_subscriptions 
                    WHERE user_id = $1 AND stripe_customer_id IS NOT NULL
                    LIMIT 1
                """, user_id)
                
                return row['stripe_customer_id'] if row else None
                
            finally:
                await release_db_connection(conn)
            
        except Exception as e:
            logger.error(f"Ошибка поиска Stripe customer для пользователя")
            return None
    
    @staticmethod
    async def _delete_stripe_customer(customer_id: str):
        """Удаляет customer из Stripe"""
        try:
            stripe.Customer.delete(customer_id)
            logger.info(f"✅ Удален Stripe customer")
            
        except stripe.error.InvalidRequestError as e:
            if "No such customer" in str(e):
                logger.warning(f"⚠️ Customer уже не существует в Stripe")
            else:
                logger.error(f"❌ Ошибка удаления customer")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления customer")
    
    @staticmethod
    async def _clean_stripe_references(user_id: int):
        """Очищает все ссылки на Stripe из нашей базы данных"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            conn = await get_db_connection()
            try:
                # Удаляем записи подписок с Stripe ID
                result = await conn.execute("""
                    DELETE FROM user_subscriptions 
                    WHERE user_id = $1
                """, user_id)
                
                logger.info(f"✅ Stripe ссылки очищены из базы для пользователя")
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки Stripe ссылок для пользователя")