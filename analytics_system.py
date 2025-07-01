# analytics_system.py - МИНИМАЛЬНАЯ ВЕРСИЯ для быстрого старта

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Analytics:
    """Минимальная система аналитики"""
    
    @staticmethod
    async def track(user_id: int, event: str, properties: Dict = None):
        """Основная функция трекинга событий"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            properties = properties or {}
            
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "INSERT INTO analytics_events (user_id, event, properties, timestamp) VALUES ($1, $2, $3, $4)",
                    user_id, event, json.dumps(properties), datetime.now()
                )
                
                # Логируем для отладки
                print(f"📊 Analytics: {event} | User: {user_id}")
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            # НЕ ПАДАЕМ если аналитика не работает
            print(f"❌ Analytics error: {e}")

    # КЛЮЧЕВЫЕ СОБЫТИЯ ДЛЯ MVP
    
    @staticmethod
    async def track_user_started(user_id: int, language: str = None, is_new: bool = True):
        """Пользователь запустил бота"""
        await Analytics.track(user_id, "user_started", {
            "language": language,
            "is_new_user": is_new
        })
    
    @staticmethod
    async def track_registration_completed(user_id: int):
        """Завершил регистрацию"""
        await Analytics.track(user_id, "registration_completed", {})
    
    @staticmethod
    async def track_document_uploaded(user_id: int, file_type: str = "unknown"):
        """Загрузил документ"""
        await Analytics.track(user_id, "document_uploaded", {
            "file_type": file_type
        })
    
    @staticmethod
    async def track_question_asked(user_id: int, question_length: int = 0):
        """Задал вопрос боту"""
        await Analytics.track(user_id, "question_asked", {
            "question_length": question_length
        })

    @staticmethod
    async def track_payment_completed(user_id: int, plan: str = "unknown", price: float = 0):
        """Завершил оплату"""
        await Analytics.track(user_id, "payment_completed", {
            "plan": plan,
            "price_usd": price
        })

    # ПРОСТЫЕ ОТЧЕТЫ
    
    @staticmethod
    async def get_stats(days: int = 7) -> Dict:
        """Получить простую статистику"""
        try:
            from db_postgresql import get_db_connection, release_db_connection
            
            conn = await get_db_connection()
            try:
                start_date = datetime.now() - timedelta(days=days)
                
                # Основные метрики
                total_users = await conn.fetchval(
                    "SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE timestamp >= $1",
                    start_date
                )
                
                new_users = await conn.fetchval(
                    "SELECT COUNT(*) FROM analytics_events WHERE event = 'user_started' AND properties->>'is_new_user' = 'true' AND timestamp >= $1",
                    start_date
                )
                
                registrations = await conn.fetchval(
                    "SELECT COUNT(*) FROM analytics_events WHERE event = 'registration_completed' AND timestamp >= $1",
                    start_date
                )
                
                documents = await conn.fetchval(
                    "SELECT COUNT(*) FROM analytics_events WHERE event = 'document_uploaded' AND timestamp >= $1",
                    start_date
                )
                
                questions = await conn.fetchval(
                    "SELECT COUNT(*) FROM analytics_events WHERE event = 'question_asked' AND timestamp >= $1",
                    start_date
                )
                
                payments = await conn.fetchval(
                    "SELECT COUNT(*) FROM analytics_events WHERE event = 'payment_completed' AND timestamp >= $1",
                    start_date
                )
                
                return {
                    "total_users": total_users or 0,
                    "new_users": new_users or 0,
                    "registrations": registrations or 0,
                    "documents": documents or 0,
                    "questions": questions or 0,
                    "payments": payments or 0,
                    "registration_rate": (registrations / new_users * 100) if new_users > 0 else 0,
                    "document_rate": (documents / total_users * 100) if total_users > 0 else 0
                }
                
            finally:
                await release_db_connection(conn)
                
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return {}