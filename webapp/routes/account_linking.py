# webapp/routes/account_linking.py
# 🔗 Эндпоинты для связывания Telegram и Web аккаунтов

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db_postgresql import get_db_connection, release_db_connection
from webapp.translations import t
from webapp.utils.context import get_template_context

router = APIRouter()
templates = Jinja2Templates(directory="webapp/templates")

# Имя вашего Telegram бота (ЗАМЕНИТЕ НА СВОЕ!)
TELEGRAM_BOT_USERNAME = "DrZolinBot"  # ⚠️ БЕЗ @


def get_current_user(request: Request) -> dict:
    """Получить текущего пользователя из сессии"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    
    return {
        'user_id': user_id,
        'email': request.session.get('email'),
        'name': request.session.get('name'),
        'google_id': request.session.get('google_id')
    }


@router.get("/dashboard/link_telegram")
async def show_link_telegram_page(request: Request):
    """
    Страница для связывания Telegram аккаунта
    
    ЛОГИКА:
    1. Проверяем авторизацию
    2. Генерируем 6-значный код
    3. Сохраняем в таблицу account_links
    4. Показываем страницу с кодом и кнопкой
    """
    # Проверка авторизации
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    
    lang = request.session.get('language', 'en')
    
    # Проверяем, не подключен ли уже Telegram
    conn = await get_db_connection()
    try:
        user_data = await conn.fetchrow(
            "SELECT registration_source FROM users WHERE user_id = $1",
            current_user['user_id']
        )
        
        if user_data and user_data['registration_source'] == 'both':
            # Telegram уже подключен
            context = get_template_context(request)
            context['already_linked'] = True
            return templates.TemplateResponse('link_telegram.html', context)
        
    finally:
        await release_db_connection(conn)
    
    # Генерируем 6-значный код
    link_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Сохраняем код в базу
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO account_links 
            (link_code, web_user_id, direction, expires_at, is_used)
            VALUES ($1, $2, 'web_to_telegram', $3, FALSE)
        """, 
            link_code,
            current_user['user_id'],
            datetime.now() + timedelta(minutes=10)  # Код действует 10 минут
        )
        
    finally:
        await release_db_connection(conn)
    
    # Формируем данные для страницы
    context = get_template_context(request)
    context.update({
        'link_code': link_code,
        'bot_username': TELEGRAM_BOT_USERNAME,
        'telegram_link': f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={link_code}",
        'code_expires_minutes': 10
    })
    
    return templates.TemplateResponse('link_telegram.html', context)


@router.post("/api/check-link-status")
async def check_link_status(request: Request):
    """
    API для проверки статуса связывания
    """
    try:
        # Проверка пользователя
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({
                'success': False, 
                'error': 'not_authenticated'
            }, status_code=401)
        
        # Получение кода
        try:
            data = await request.json()
            link_code = data.get('code')
        except Exception:
            return JSONResponse({
                'success': False,
                'error': 'invalid_json'
            }, status_code=400)
        
        if not link_code:
            return JSONResponse({
                'success': False,
                'error': 'no_code'
            })
        
        # Проверка в базе данных
        conn = await get_db_connection()
        try:
            link_record = await conn.fetchrow("""
                SELECT is_used, telegram_user_id, web_user_id, expires_at
                FROM account_links
                WHERE link_code = $1
            """, link_code)
            
            if not link_record:
                return JSONResponse({
                    'success': False,
                    'status': 'not_found'
                })
            
            # Проверка прав доступа
            is_owner = (
                link_record['web_user_id'] == current_user['user_id'] or 
                (link_record['is_used'] and link_record['telegram_user_id'] == current_user['user_id'])
            )
            
            if not is_owner:
                return JSONResponse({
                    'success': False,
                    'status': 'not_found'
                })
            
            # Проверка истёк ли код
            if link_record['expires_at'] < datetime.now():
                return JSONResponse({
                    'success': False,
                    'status': 'expired'
                })
            
            # Проверка использован ли код
            if link_record['is_used']:
                telegram_id = link_record['telegram_user_id']
                
                # Обновляем сессию
                request.session['user_id'] = telegram_id
                
                # Получаем данные пользователя
                user_data = await conn.fetchrow(
                    "SELECT name, email, google_id FROM users WHERE user_id = $1",
                    telegram_id
                )
                
                if user_data:
                    request.session['name'] = user_data['name']
                    request.session['email'] = user_data['email']
                    request.session['google_id'] = user_data['google_id']
                
                return JSONResponse({
                    'success': True,
                    'status': 'completed',
                    'telegram_id': telegram_id,
                    'redirect': True
                })
            
            # Код ещё не использован
            return JSONResponse({
                'success': True,
                'status': 'waiting'
            })
            
        finally:
            await release_db_connection(conn)
    
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': 'internal_error',
            'message': str(e)
        }, status_code=500)


@router.get("/api/refresh-link-code")
async def refresh_link_code(request: Request):
    """
    Сгенерировать новый код если старый истёк
    """
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
    
    # Генерируем новый код
    link_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    conn = await get_db_connection()
    try:
        # Помечаем старые коды как использованные
        await conn.execute("""
            UPDATE account_links 
            SET is_used = TRUE 
            WHERE web_user_id = $1 AND is_used = FALSE
        """, current_user['user_id'])
        
        # Создаём новый код
        await conn.execute("""
            INSERT INTO account_links 
            (link_code, web_user_id, direction, expires_at, is_used)
            VALUES ($1, $2, 'web_to_telegram', $3, FALSE)
        """, 
            link_code,
            current_user['user_id'],
            datetime.now() + timedelta(minutes=10)
        )
        
        return JSONResponse({
            'success': True,
            'code': link_code
        })
        
    finally:
        await release_db_connection(conn)