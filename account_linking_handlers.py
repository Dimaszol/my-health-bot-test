from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from db_postgresql import get_user, get_db_connection, release_db_connection, get_user_language, t
from account_merger import AccountMerger


async def handle_linking_code(message: types.Message, bot: Bot):
    telegram_id = message.from_user.id
    
    # ✅ ИЗВЛЕКАЕМ КОД из текста
    text = message.text.strip() if message.text else ""
    
    # Если это /start с параметром - берём параметр
    if text.startswith('/start '):
        code = text.split(maxsplit=1)[1].strip()
    else:
        # Если просто код отправлен напрямую
        code = text
    
    print(f"📝 Обрабатываем код: '{code}' (длина: {len(code)})")
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Проверяем формат кода (должно быть 6 цифр)
    if not code.isdigit() or len(code) != 6:
        await message.answer(
            t('bot_code_format_error', lang),
            parse_mode='HTML'
        )
        return
    
    conn = await get_db_connection()
    
    try:
        # ====================================
        # ШАГ 1: ИЩЕМ КОД В БАЗЕ ДАННЫХ
        # ====================================
        link_record = await conn.fetchrow("""
            SELECT 
                link_code,
                web_user_id,
                telegram_user_id,
                expires_at,
                is_used
            FROM account_links
            WHERE link_code = $1
        """, code)
        
        # Код не найден
        if not link_record:
            await message.answer(
                t('bot_code_not_found', lang),
                parse_mode='HTML'
            )
            return
        
        # Код уже использован
        if link_record['is_used']:
            await message.answer(
                t('bot_code_already_used', lang),
                parse_mode='HTML'
            )
            return
        
        # Код истёк
        if link_record['expires_at'] < datetime.now():
            await message.answer(
                t('bot_code_not_found', lang),  # Тот же текст
                parse_mode='HTML'
            )
            return
        
        web_user_id = link_record['web_user_id']
        
        print(f"🔗 Код связывания найден:")
        print(f"   Code: {code}")
        print(f"   Web user_id: {web_user_id}")
        print(f"   Telegram ID: {telegram_id}")
        
        # ====================================
        # ШАГ 2: ПОЛУЧАЕМ ДАННЫЕ ВЕБ-ПОЛЬЗОВАТЕЛЯ
        # ====================================
        web_user = await conn.fetchrow("""
            SELECT google_id, email, registration_source
            FROM users 
            WHERE user_id = $1
        """, web_user_id)
        
        if not web_user:
            await message.answer(
                "❌ Ошибка: веб-пользователь не найден.",
                parse_mode='HTML'
            )
            return
        
        # ====================================
        # ШАГ 3: ПРОВЕРЯЕМ СУЩЕСТВУЕТ ЛИ TELEGRAM АККАУНТ
        # ====================================
        telegram_user = await conn.fetchrow("""
            SELECT user_id, registration_source
            FROM users 
            WHERE user_id = $1
        """, telegram_id)
        
        # ====================================
        # СЦЕНАРИЙ A: Telegram аккаунта нет - простое подключение
        # ====================================
        if not telegram_user:
            print("📝 Telegram аккаунт не найден - просто добавляем ID")
            
            # Помечаем код как использованный
            await conn.execute("""
                UPDATE account_links 
                SET 
                    is_used = TRUE,
                    telegram_user_id = $1
                WHERE link_code = $2
            """, telegram_id, code)
            
            # Выполняем слияние
            result = await AccountMerger.merge_accounts(
                telegram_id,
                web_user_id,
                web_user['google_id'],
                web_user['email']
            )
            
            if result['success']:
                await message.answer(
                    t('bot_link_success', lang),
                    parse_mode='HTML'
                )
                
                # ✅ ДОБАВЛЯЕМ: Показываем приветствие и меню
                user_data = await get_user(telegram_id)
                name = user_data.get('name', 'Пользователь')
                
                from keyboards import main_menu_keyboard
                await message.answer(
                    t("welcome", lang, name=name),
                    reply_markup=main_menu_keyboard(lang)
                )
                await message.answer(t("how_to_use_1", lang))
            else:
                await message.answer(
                    t('error_linking', lang),
                    parse_mode='HTML'
                )
            
            return
        
        # ====================================
        # СЦЕНАРИЙ B: Оба аккаунта существуют - нужно подтверждение
        # ====================================
        if telegram_user and web_user:
            print("⚠️ Оба аккаунта существуют - запрашиваем подтверждение")
            
            # Создаём клавиатуру подтверждения
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t('bot_merge_confirm_yes', lang),
                        callback_data=f"merge_confirm:{code}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t('bot_merge_confirm_no', lang),
                        callback_data=f"merge_cancel:{code}"
                    )
                ]
            ])
            
            await message.answer(
                t('bot_accounts_will_merge', lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return
        
        # ====================================
        # СЦЕНАРИЙ C: Есть только Telegram аккаунт
        # ====================================
        print("📱 Есть только Telegram - добавляем Google данные")
        
        # Помечаем код как использованный
        await conn.execute("""
            UPDATE account_links 
            SET 
                is_used = TRUE,
                telegram_user_id = $1
            WHERE link_code = $2
        """, telegram_id, code)
        
        # Выполняем связывание
        result = await AccountMerger.merge_accounts(
            telegram_id,
            web_user_id,
            web_user['google_id'],
            web_user['email']
        )
        
        if result['success']:
            await message.answer(
                t('bot_link_success', lang),
                parse_mode='HTML'
            )
            
            # ✅ ДОБАВЛЯЕМ: Показываем приветствие и меню
            user_data = await get_user(telegram_id)
            name = user_data.get('name', 'Пользователь')
            
            from keyboards import main_menu_keyboard
            await message.answer(
                t("welcome", lang, name=name),
                reply_markup=main_menu_keyboard(lang)
            )
            await message.answer(t("how_to_use_1", lang))
        else:
            await message.answer(
                t('error_linking', lang),
                parse_mode='HTML'
            )
    
    except Exception as e:
        print(f"❌ Ошибка при обработке кода связывания: {e}")
        import traceback
        traceback.print_exc()
        
        await message.answer(
            t('error_linking', lang),
            parse_mode='HTML'
        )
    
    finally:
        await release_db_connection(conn)


async def handle_merge_confirmation(callback_query: types.CallbackQuery, bot: Bot):
    """
    Обработка подтверждения слияния аккаунтов
    
    КОГДА ВЫЗЫВАЕТСЯ:
    - Пользователь нажал "Да, объединить" или "Нет, отменить"
    """
    telegram_id = callback_query.from_user.id
    data = callback_query.data
    
    # Получаем язык
    lang = await get_user_language(telegram_id)
    
    # Парсим callback_data
    action, code = data.split(':', 1)
    
    # ====================================
    # ОТМЕНА СЛИЯНИЯ
    # ====================================
    if action == 'merge_cancel':
        await callback_query.message.edit_text(
            t('bot_merge_cancelled', lang),
            parse_mode='HTML'
        )
        await callback_query.answer()
        return
    
    # ====================================
    # ПОДТВЕРЖДЕНИЕ СЛИЯНИЯ
    # ====================================
    if action == 'merge_confirm':
        conn = await get_db_connection()
        
        try:
            # Получаем данные кода
            link_record = await conn.fetchrow("""
                SELECT web_user_id, is_used, expires_at
                FROM account_links
                WHERE link_code = $1
            """, code)
            
            if not link_record or link_record['is_used']:
                await callback_query.message.edit_text(
                    t('bot_code_already_used', lang),
                    parse_mode='HTML'
                )
                await callback_query.answer()
                return
            
            if link_record['expires_at'] < datetime.now():
                await callback_query.message.edit_text(
                    t('bot_code_not_found', lang),
                    parse_mode='HTML'
                )
                await callback_query.answer()
                return
            
            web_user_id = link_record['web_user_id']
            
            # Получаем данные веб-пользователя
            web_user = await conn.fetchrow("""
                SELECT google_id, email
                FROM users 
                WHERE user_id = $1
            """, web_user_id)
            
            if not web_user:
                await callback_query.message.edit_text(
                    "❌ Ошибка: пользователь не найден.",
                    parse_mode='HTML'
                )
                await callback_query.answer()
                return
            
            # Помечаем код как использованный
            await conn.execute("""
                UPDATE account_links 
                SET 
                    is_used = TRUE,
                    telegram_user_id = $1
                WHERE link_code = $2
            """, telegram_id, code)
            
            # ВЫПОЛНЯЕМ СЛИЯНИЕ
            result = await AccountMerger.merge_accounts(
                telegram_id,
                web_user_id,
                web_user['google_id'],
                web_user['email']
            )
            
            if result['success']:
                await callback_query.message.edit_text(
                    t('bot_merge_success', lang),
                    parse_mode='HTML'
                )
                
                # ✅ ДОБАВЛЯЕМ: Показываем приветствие и меню
                user_data = await get_user(telegram_id)
                name = user_data.get('name', 'Пользователь')
                
                from keyboards import main_menu_keyboard
                await bot.send_message(
                    chat_id=telegram_id,
                    text=t("welcome", lang, name=name),
                    reply_markup=main_menu_keyboard(lang)
                )
                await bot.send_message(
                    chat_id=telegram_id,
                    text=t("how_to_use_1", lang)
                )
            else:
                await callback_query.message.edit_text(
                    t('error_linking', lang),
                    parse_mode='HTML'
                )
            
            await callback_query.answer()
        
        except Exception as e:
            print(f"❌ Ошибка при слиянии: {e}")
            import traceback
            traceback.print_exc()
            
            await callback_query.message.edit_text(
                t('error_linking', lang),
                parse_mode='HTML'
            )
            await callback_query.answer()
        
        finally:
            await release_db_connection(conn)