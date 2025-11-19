# hard_limit_checker.py
"""
🚫 Модуль проверки жёсткого лимита на 100 сообщений

Блокирует бесплатное использование после 100 сообщений, если пользователь
не покупал ничего за последние 35 дней.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple
from db_postgresql import fetch_one, get_user_language

logger = logging.getLogger(__name__)


async def check_100_message_hard_limit(user_id: int) -> Tuple[bool, str]:
    """
    🚫 Проверяет достиг ли пользователь жёсткого лимита в 100 сообщений
    
    Блокирует дальнейшее использование если:
    1. total_messages_count >= 100
    2. Не было покупок за последние 35 дней
    
    Логика: Если была любая покупка (подписка или разовая) за 35 дней,
    значит пользователь платил недавно → пропускаем.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Tuple[bool, str]: (можно_продолжить, сообщение_об_ошибке)
        - (True, "") - лимит не достигнут, можно продолжить
        - (False, "текст ошибки") - лимит достигнут, показываем сообщение
    """
    try:
        # 1️⃣ Проверяем счётчик сообщений и наличие покупок одним запросом
        result = await fetch_one("""
            SELECT 
                u.total_messages_count,
                EXISTS(
                    SELECT 1 
                    FROM transactions t
                    WHERE t.user_id = u.user_id
                      AND t.status = 'completed'
                      AND t.completed_at >= NOW() - INTERVAL '35 days'
                ) as has_recent_purchase
            FROM users u
            WHERE u.user_id = $1
        """, (user_id,))
        
        if not result:
            logger.warning(f"❌ Пользователь {user_id} не найден в БД")
            return True, ""  # Если пользователь не найден - пропускаем
        
        total_messages = result[0] if isinstance(result, tuple) else result.get('total_messages_count', 0)
        has_recent_purchase = result[1] if isinstance(result, tuple) else result.get('has_recent_purchase', False)
        
        # 2️⃣ Если меньше 100 сообщений - проверка не нужна
        if total_messages < 100:
            return True, ""
        
        logger.info(f"📊 Пользователь {user_id}: {total_messages} сообщений (проверяем hard limit)")
        
        # 3️⃣ Если была покупка за последние 35 дней - разрешаем
        if has_recent_purchase:
            logger.info(f"✅ Пользователь {user_id}: есть покупка за последние 35 дней")
            return True, ""
        
        # 4️⃣ НЕТ ПОКУПОК И >= 100 СООБЩЕНИЙ - БЛОКИРУЕМ!
        logger.warning(f"🚫 Пользователь {user_id}: достигнут hard limit (100+ сообщений, нет покупок за 35 дней)")
        
        # Формируем сообщение на нужном языке
        lang = await get_user_language(user_id)
        
        error_message = (
                "🎉 <b>Бесплатный лимит исчерпан!</b>\n\n"
                "💡 Чтобы продолжить пользоваться медицинским ботом, выберите один из вариантов:\n\n"
                "💎 <b>Оформить подписку</b>\n"
                "   • До 100 сообщений в день\n"
                "   • Детальные медицинские консультации\n"
                "   • Загрузка до 40 документов в день\n"
                "   • Приоритетная поддержка\n\n"
                "🎯 <b>Купить дополнительные консультации</b>\n"
                "   • Разовая покупка без подписки\n"
                "   • Детальные ответы от GPT-4\n"
                "   • Действует 30 дней\n\n"
                "📲 Нажмите /subscription чтобы выбрать тариф"
            )
               
        return False, error_message
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки hard limit для пользователя {user_id}: {e}")
        # В случае ошибки - разрешаем (чтобы не блокировать пользователя из-за технической проблемы)
        return True, ""