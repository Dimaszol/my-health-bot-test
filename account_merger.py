# account_merger.py
# 🔗 Модуль для слияния аккаунтов веб и телеграм пользователей

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime
from db_postgresql import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

class AccountMerger:
    """
    Класс для объединения веб и телеграм аккаунтов
    
    ЛОГИКА:
    1. Проверяем есть ли уже оба аккаунта в базе
    2. Если оба есть → запускаем слияние
    3. Если только один → просто добавляем второй идентификатор
    4. Primary ключ всегда = telegram_id
    """
    
    @staticmethod
    async def merge_accounts(telegram_id: int, web_user_id: int, google_id: str, email: str) -> Dict:
        """
        Главная функция слияния аккаунтов
        
        Args:
            telegram_id: ID пользователя в Telegram (станет PRIMARY KEY)
            web_user_id: ID пользователя в вебе (временный, будет удалён)
            google_id: Google ID пользователя
            email: Email пользователя
            
        Returns:
            Dict с результатом:
            {
                'success': bool,
                'action': 'linked' | 'merged',
                'primary_user_id': int,
                'message': str
            }
        """
        conn = await get_db_connection()
        
        try:
            # ====================================
            # ПРОВЕРКА 1: Существует ли Telegram аккаунт?
            # ====================================
            telegram_user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                telegram_id
            )
            
            # ====================================
            # ПРОВЕРКА 2: Существует ли Web аккаунт?
            # ====================================
            web_user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                web_user_id
            )
            
            # ====================================
            # СЦЕНАРИЙ 1: Telegram аккаунта НЕТ (новый пользователь)
            # ====================================
            if not telegram_user:
                # Обновляем web аккаунт: меняем user_id на telegram_id
                await AccountMerger._convert_web_to_telegram(
                    conn, web_user_id, telegram_id, google_id, email
                )
                
                return {
                    'success': True,
                    'action': 'linked',
                    'primary_user_id': telegram_id,
                    'message': 'Telegram успешно подключен к вашему аккаунту'
                }
            
            # ====================================
            # СЦЕНАРИЙ 2: Оба аккаунта существуют → СЛИЯНИЕ
            # ====================================
            if telegram_user and web_user:
                
                # Выполняем полное слияние
                await AccountMerger._full_merge(
                    conn, 
                    telegram_id,  # PRIMARY
                    web_user_id,  # SECONDARY (удалится)
                    telegram_user,
                    web_user,
                    google_id,
                    email
                )
                
                return {
                    'success': True,
                    'action': 'merged',
                    'primary_user_id': telegram_id,
                    'message': 'Аккаунты успешно объединены! Все данные сохранены'
                }
            
            # ====================================
            # СЦЕНАРИЙ 3: Есть только Telegram аккаунт
            # ====================================
                        
            await conn.execute("""
                UPDATE users 
                SET 
                    google_id = $1,
                    email = $2,
                    registration_source = 'both',
                    last_updated = NOW()
                WHERE user_id = $3
            """, google_id, email, telegram_id)
            
            return {
                'success': True,
                'action': 'linked',
                'primary_user_id': telegram_id,
                'message': 'Веб-версия успешно подключена к вашему Telegram аккаунту'
            }
            
        except Exception as e:
            logger.error("Ошибка при слиянии аккаунтов")
            return {
                'success': False,
                'action': 'error',
                'message': 'Произошла ошибка при слиянии аккаунтов'
            }
        finally:
            await release_db_connection(conn)
    
    
    @staticmethod
    async def _convert_web_to_telegram(conn, old_web_id: int, new_telegram_id: int, 
                                       google_id: str, email: str):
        """
        Конвертирует веб аккаунт в телеграм аккаунт
        Просто меняем user_id везде на telegram_id
        """
               
        # 1. Обновляем все связанные таблицы (меняем user_id)
        tables_to_update = [
            'user_limits',
            'documents',
            'document_vectors',
            'chat_history',
            'medications',
            'notification_settings',
            'notification_history',
            'transactions',
            'medical_timeline',
            'analytics_events',
            'garmin_connections',
            'garmin_daily_data',
            'garmin_analysis_history'
        ]
        
        for table in tables_to_update:
            try:
                await conn.execute(
                    f"UPDATE {table} SET user_id = $1 WHERE user_id = $2",
                    new_telegram_id, old_web_id
                )
                
            except Exception as e:
                # Таблица может не существовать - это нормально
                logger.debug(f"   ⚠ {table}: {e}")
        
        # 2. Обновляем основную таблицу users
        await conn.execute("""
            UPDATE users 
            SET 
                user_id = $1,
                registration_source = 'both'
            WHERE user_id = $2
        """, new_telegram_id, old_web_id)
    
    @staticmethod
    async def _full_merge(conn, primary_id: int, secondary_id: int, 
                        telegram_user: Dict, web_user: Dict,
                        google_id: str, email: str):
        """
        Полное слияние двух существующих аккаунтов
        
        PRIMARY = telegram_user (остаётся)
        SECONDARY = web_user (удаляется после переноса данных)
        """
                
        # ====================================
        # ШАГ 1: ПЕРЕНОСИМ ДАННЫЕ ИЗ ВСЕХ ТАБЛИЦ
        # ====================================
                
        tables_to_transfer = [
            'documents',
            'document_vectors',
            'chat_history',
            'notification_history',
            'transactions',
            'medical_timeline',
            'analytics_events',
            'garmin_daily_data',
            'garmin_analysis_history'
        ]
        
        for table in tables_to_transfer:
            try:
                result = await conn.execute(
                    f"UPDATE {table} SET user_id = $1 WHERE user_id = $2",
                    primary_id, secondary_id
                )
                
            except Exception as e:
                logger.debug(f"   ⚠ {table}: {e}")
        
        # ====================================
        # ШАГ 2: ОБРАБАТЫВАЕМ ТАБЛИЦЫ С UNIQUE CONSTRAINT
        # ====================================
        
        # notification_settings: оставляем Telegram настройки
        telegram_settings = await conn.fetchrow(
            "SELECT * FROM notification_settings WHERE user_id = $1", primary_id
        )
        
        if telegram_settings:
            # Удаляем веб настройки (оставляем telegram)
            await conn.execute(
                "DELETE FROM notification_settings WHERE user_id = $1", secondary_id
            )

        else:
            # Если в Telegram нет настроек, переносим из веба
            await conn.execute(
                "UPDATE notification_settings SET user_id = $1 WHERE user_id = $2",
                primary_id, secondary_id
            )
        
        # medications: объединяем (могут быть дубли)
        await AccountMerger._merge_medications(conn, primary_id, secondary_id)
        
        # garmin_connections: оставляем одно подключение
        await AccountMerger._merge_garmin_connection(conn, primary_id, secondary_id)
        
        # ====================================
        # ШАГ 3: ОБЪЕДИНЯЕМ user_limits (ПРИОРИТЕТ WEB!)
        # ====================================
        
        # Получаем лимиты обоих аккаунтов
        telegram_limits = await conn.fetchrow(
            "SELECT * FROM user_limits WHERE user_id = $1", primary_id
        )
        web_limits = await conn.fetchrow(
            "SELECT * FROM user_limits WHERE user_id = $1", secondary_id
        )
        
        if telegram_limits and web_limits:
            # ПРИОРИТЕТ ПОДПИСКИ: WEB!
            subscription_type = web_limits['subscription_type']
            subscription_expires = web_limits['subscription_expires_at']
            
            # Если в веб была бесплатная подписка, проверяем telegram
            if subscription_type == 'free' and telegram_limits['subscription_type'] != 'free':
                subscription_type = telegram_limits['subscription_type']
                subscription_expires = telegram_limits['subscription_expires_at']
            
            # Лимиты: берём МАКСИМУМ
            documents_left = max(
                telegram_limits.get('documents_left', 0),
                web_limits.get('documents_left', 0)
            )
            queries_left = max(
                telegram_limits.get('gpt4o_queries_left', 0),
                web_limits.get('gpt4o_queries_left', 0)
            )
            
            # Обновляем PRIMARY аккаунт
            await conn.execute("""
                UPDATE user_limits 
                SET 
                    subscription_type = $1,
                    subscription_expires_at = $2,
                    documents_left = $3,
                    gpt4o_queries_left = $4,
                    email = $5,
                    updated_at = NOW()
                WHERE user_id = $6
            """, subscription_type, subscription_expires, documents_left, queries_left, email, primary_id)
            
            # Удаляем лимиты вторичного аккаунта
            await conn.execute("DELETE FROM user_limits WHERE user_id = $1", secondary_id)
        
        # ====================================
        # ШАГ 4: УДАЛЯЕМ ВТОРИЧНЫЙ АККАУНТ (ВАЖНО - ДО ОБНОВЛЕНИЯ PRIMARY!)
        # ====================================
        
        await conn.execute("DELETE FROM users WHERE user_id = $1", secondary_id)

        # ====================================
        # ШАГ 5: ОБЪЕДИНЯЕМ ТАБЛИЦУ users (ТЕПЕРЬ БЕЗОПАСНО!)
        # ====================================
        
        # Собираем все поля для объединения (берём заполненные значения)
        merged_fields = {
            'google_id': google_id,  # ← Теперь безопасно! Web аккаунт удалён
            'email': email,
            'registration_source': 'both',
            
            # Имя: приоритет ЗАПОЛНЕННЫМ данным (WEB приоритетнее!)
            'name': web_user.get('name') or telegram_user.get('name'),
            
            # Данные анкеты: берём заполненное (WEB приоритет!)
            'birth_year': web_user.get('birth_year') or telegram_user.get('birth_year'),
            'gender': web_user.get('gender') or telegram_user.get('gender'),
            'height_cm': web_user.get('height_cm') or telegram_user.get('height_cm'),
            'weight_kg': web_user.get('weight_kg') or telegram_user.get('weight_kg'),
            'chronic_conditions': web_user.get('chronic_conditions') or telegram_user.get('chronic_conditions'),
            'medications': web_user.get('medications') or telegram_user.get('medications'),
            'allergies': web_user.get('allergies') or telegram_user.get('allergies'),
            'smoking': web_user.get('smoking') or telegram_user.get('smoking'),
            'alcohol': web_user.get('alcohol') or telegram_user.get('alcohol'),
            'physical_activity': web_user.get('physical_activity') or telegram_user.get('physical_activity'),
            'family_history': web_user.get('family_history') or telegram_user.get('family_history'),
            
            # Язык: приоритет Telegram
            'language': telegram_user.get('language') or web_user.get('language', 'en'),
            
            # GDPR
            'gdpr_consent': True,
            'gdpr_consent_time': datetime.now(),
            
            # Статистика: суммируем
            'total_messages_count': (telegram_user.get('total_messages_count', 0) + 
                                    web_user.get('total_messages_count', 0)),
            
            # Username из Telegram
            'username': telegram_user.get('username'),
            
            # Даты
            'created_at': min(
                telegram_user.get('created_at', datetime.now()),
                web_user.get('created_at', datetime.now())
            ),
            'last_updated': datetime.now()
        }
        
        # Формируем запрос обновления
        update_parts = []
        values = []
        param_num = 1
        
        for field, value in merged_fields.items():
            update_parts.append(f"{field} = ${param_num}")
            values.append(value)
            param_num += 1
        
        values.append(primary_id)  # WHERE user_id = ...
        
        await conn.execute(f"""
            UPDATE users 
            SET {', '.join(update_parts)}
            WHERE user_id = ${param_num}
        """, *values)
    
    @staticmethod
    async def _merge_medications(conn, primary_id: int, secondary_id: int):
        """Объединяем расписания лекарств, удаляя дубли"""
        try:
            # Получаем лекарства вторичного аккаунта
            secondary_meds = await conn.fetch(
                "SELECT name, time, label FROM medications WHERE user_id = $1",
                secondary_id
            )
            
            if not secondary_meds:
                return
            
            # Получаем существующие лекарства primary аккаунта
            primary_meds = await conn.fetch(
                "SELECT name, time FROM medications WHERE user_id = $1",
                primary_id
            )
            
            # Создаём set для быстрой проверки дублей
            existing = {(m['name'].lower(), m['time']) for m in primary_meds if m['time']}
            
            # Добавляем только уникальные лекарства
            for med in secondary_meds:
                key = (med['name'].lower(), med['time'])
                if key not in existing and med['time']:
                    await conn.execute("""
                        INSERT INTO medications (user_id, name, time, label)
                        VALUES ($1, $2, $3, $4)
                    """, primary_id, med['name'], med['time'], med['label'])
                    existing.add(key)
            
            # Удаляем лекарства вторичного аккаунта
            await conn.execute("DELETE FROM medications WHERE user_id = $1", secondary_id)
            
        except Exception as e:
            logger.error("Ошибка при объединении лекарств")
    
    
    @staticmethod
    async def _merge_garmin_connection(conn, primary_id: int, secondary_id: int):
        """Объединяем подключения Garmin (оставляем активное)"""
        try:
            # Проверяем есть ли подключения
            primary_garmin = await conn.fetchrow(
                "SELECT * FROM garmin_connections WHERE user_id = $1", primary_id
            )
            secondary_garmin = await conn.fetchrow(
                "SELECT * FROM garmin_connections WHERE user_id = $1", secondary_id
            )
            
            if primary_garmin and secondary_garmin:
                # Если оба подключения активны, оставляем то что новее
                if primary_garmin['is_active']:
                    await conn.execute(
                        "DELETE FROM garmin_connections WHERE user_id = $1", secondary_id
                    )
                else:
                    await conn.execute(
                        "DELETE FROM garmin_connections WHERE user_id = $1", primary_id
                    )
                    await conn.execute(
                        "UPDATE garmin_connections SET user_id = $1 WHERE user_id = $2",
                        primary_id, secondary_id
                    )

            elif secondary_garmin and not primary_garmin:
                # Переносим подключение из веба
                await conn.execute(
                    "UPDATE garmin_connections SET user_id = $1 WHERE user_id = $2",
                    primary_id, secondary_id
                )
            
        except Exception as e:
            logger.error("Ошибка при объединении Garmin")