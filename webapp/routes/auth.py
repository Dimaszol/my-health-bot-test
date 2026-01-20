# webapp/routes/auth.py
# 🔐 Авторизация через Google OAuth для медицинского бота - FASTAPI ВЕРСИЯ

import os
import sys
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from webapp.utils.logger import safe_log_info, safe_log_error

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webapp.config import Config

# ✅ ИМПОРТИРУЕМ ASYNC ФУНКЦИИ из db_postgresql.py
from db_postgresql import get_db_connection, release_db_connection

"""
🎯 КАК РАБОТАЕТ GOOGLE OAUTH (простыми словами):

1. Пользователь нажимает "Войти через Google" → /auth/google
2. FastAPI перенаправляет пользователя на сайт Google
3. Google спрашивает: "Разрешить доступ к вашему email и имени?"
4. Пользователь нажимает "Да"
5. Google отправляет пользователя обратно → /auth/google/callback
6. FastAPI получает данные пользователя (email, имя, google_id)
7. FastAPI проверяет: есть ли такой пользователь в БД?
   - Если ДА → входим (сохраняем user_id в session)
   - Если НЕТ → создаём нового пользователя, потом входим
8. Редирект в личный кабинет

БЕЗОПАСНОСТЬ: Мы НЕ храним пароли! Google всё проверяет за нас.
"""

# 📘 СОЗДАЁМ ROUTER (аналог Blueprint)
router = APIRouter()

# 🔧 НАСТРОЙКА GOOGLE OAUTH
# ⚠️ ВАЖНО: Для FastAPI используем starlette_client, НЕ flask_client!
oauth = OAuth()

# Регистрируем Google как OAuth провайдера
google = oauth.register(
    name='google',
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'  # Запрашиваем: ID, email, имя
    }
)


# ==========================================
# 🔧 ASYNC ФУНКЦИЯ: Найти или создать пользователя
# ==========================================

async def find_or_create_web_user(google_id: str, email: str, name: str, session_language: str = 'en') -> dict:
    """
    Находит существующего пользователя или создаёт нового
    
    ✅ ПОЛНОСТЬЮ ASYNC! БЕЗ psycopg2!
    Используем готовые функции из db_postgresql.py
    """
    conn = await get_db_connection()
    
    try:
        # 1. Ищем существующего пользователя
        user = await conn.fetchrow(
            "SELECT user_id, name, email FROM users WHERE google_id = $1",
            google_id
        )
        
        if user:
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }
        
        # 2. Создаём нового пользователя
       
        # Генерируем ID
        temp_user_id = await conn.fetchval("SELECT generate_temp_web_user_id()")

        # Создаём пользователя с языком из сессии
        await conn.execute("""
            INSERT INTO users (
                user_id, name, google_id, email, 
                registration_source, language, 
                gdpr_consent, gdpr_consent_time,
                created_at
            )
            VALUES ($1, $2, $3, $4, 'web', $5, TRUE, NOW(), NOW())
            ON CONFLICT (user_id) DO NOTHING
        """, temp_user_id, name, google_id, email, session_language)

        # 🔥 ПРОВЕРЯЕМ: был ли пользователь удалён раньше
        deleted_limits = await conn.fetchrow("""
            SELECT * FROM deleted_users_limits 
            WHERE google_id = $1 OR email = $2
            ORDER BY deleted_at DESC
            LIMIT 1
        """, google_id, email)

        if deleted_limits:
            # Восстанавливаем старые лимиты с новым user_id
            await conn.execute("""
                INSERT INTO user_limits 
                (user_id, google_id, email, documents_left, gpt4o_queries_left, 
                subscription_type, subscription_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE SET
                    google_id = EXCLUDED.google_id,
                    email = EXCLUDED.email,
                    documents_left = EXCLUDED.documents_left,
                    gpt4o_queries_left = EXCLUDED.gpt4o_queries_left,
                    subscription_type = EXCLUDED.subscription_type,
                    subscription_expires_at = EXCLUDED.subscription_expires_at
            """, 
                temp_user_id,
                google_id,
                email,
                deleted_limits['documents_left'],
                deleted_limits['gpt4o_queries_left'],
                deleted_limits['subscription_type'],
                deleted_limits['subscription_expires_at']
            )
            # 🔥 Удаляем запись из deleted_users_limits
            await conn.execute("""
                DELETE FROM deleted_users_limits 
                WHERE google_id = $1 OR email = $2
            """, google_id, email)
        else:
            # Проверяем есть ли старые лимиты по email (из старой логики)
            existing_limits = await conn.fetchrow("""
                SELECT user_id, documents_left, gpt4o_queries_left, subscription_type, subscription_expires_at
                FROM user_limits
                WHERE email = $1
            """, email)

            if existing_limits:
                # Переносим старые лимиты + обновляем google_id
                await conn.execute("""
                    UPDATE user_limits 
                    SET user_id = $1, google_id = $2, email = $3, updated_at = NOW()
                    WHERE email = $3
                """, temp_user_id, google_id, email)
            else:
                # Создаём новые лимиты
                await conn.execute("""
                    INSERT INTO user_limits (user_id, google_id, email, documents_left, gpt4o_queries_left, subscription_type)
                    VALUES ($1, $2, $3, 1, 5, 'free')
                """, temp_user_id, google_id, email)
        
        return {
            'user_id': temp_user_id,
            'name': name,
            'email': email
        }
        
    except Exception as e:
        safe_log_error("Ошибка при создании пользователя", error=e)
        return None
        
    finally:
        await release_db_connection(conn)


# ==========================================
# 🚀 МАРШРУТ 1: Начало входа через Google
# ==========================================

@router.get("/google")
async def google_login(request: Request):
    """
    Перенаправляет пользователя на страницу входа Google
    
    ✅ ОТЛИЧИЕ ОТ FLASK:
    - Используем request.url_for вместо url_for
    - Добавляем await к authorize_redirect
    """
    # Генерируем URL для callback
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    
    # ✅ AWAIT! В Flask не было await
    return await google.authorize_redirect(request, redirect_uri)


# ==========================================
# 🔄 МАРШРУТ 2: Обработка ответа от Google
# ==========================================

@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Google возвращает пользователя сюда после успешного входа
    
    ✅ ИСПРАВЛЕНО: Теперь ищет по google_id (работает после слияния аккаунтов)
    """
    try:
        # ✅ AWAIT! Получаем токен от Google
        token = await google.authorize_access_token(request)
        
        # Получаем информацию о пользователе
        user_info = token.get('userinfo')
        
        if not user_info:
            print("❌ Не удалось получить данные пользователя от Google")
            return RedirectResponse(url='/login', status_code=302)
        
        # Извлекаем данные
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('given_name', user_info.get('name', 'Пользователь'))
        
        # ✅ НОВАЯ ЛОГИКА: Ищем пользователя по google_id
        conn = await get_db_connection()
        
        try:
            # Проверяем существует ли пользователь с таким google_id
            user = await conn.fetchrow("""
                SELECT user_id, name, email, registration_source
                FROM users 
                WHERE google_id = $1
            """, google_id)
            
            if user:
                
                # 🔒 ЗАЩИТА ОТ SESSION FIXATION: Пересоздаём сессию
                old_session_data = dict(request.session)
                request.session.clear()
                
                # Восстанавливаем только безопасные данные
                if 'language' in old_session_data:
                    request.session['language'] = old_session_data['language']

                # Сохраняем данные в сессии
                request.session['user_id'] = user['user_id']  # ← Может быть telegram_id!
                request.session['email'] = user['email']
                request.session['name'] = user['name']
                request.session['google_id'] = google_id
                
                # Загружаем язык
                lang_result = await conn.fetchrow(
                    "SELECT language FROM users WHERE user_id = $1",
                    user['user_id']
                )
                
                if lang_result and lang_result['language']:
                    request.session['language'] = lang_result['language']

                else:
                    # Оставляем текущий язык из сессии
                    if 'language' not in request.session:
                        request.session['language'] = 'en'
                
                # Редиректим в личный кабинет
                return RedirectResponse(url='/dashboard', status_code=302)
            
            else:
                
                # Получаем язык из сессии
                current_session_lang = request.session.get('language', 'en')
                
                # Создаём пользователя через старую функцию
                new_user = await find_or_create_web_user(google_id, email, name, current_session_lang)
                
                if new_user:
                    # 🔒 ЗАЩИТА ОТ SESSION FIXATION: Пересоздаём сессию для нового пользователя
                    request.session.clear()
                    
                    # Сохраняем в НОВУЮ сессию
                    request.session['user_id'] = new_user['user_id']
                    request.session['email'] = email
                    request.session['name'] = name
                    request.session['google_id'] = google_id
                    request.session['language'] = current_session_lang

                    # 🎯 ФЛАГ ДЛЯ GOOGLE ADS: это новая регистрация
                    request.session['just_registered'] = True
                    
                    return RedirectResponse(url='/dashboard', status_code=302)
                else:
                    print("❌ Не удалось создать пользователя")
                    return RedirectResponse(url='/login', status_code=302)
        
        finally:
            await release_db_connection(conn)
            
    except Exception as e:
        safe_log_error("Ошибка при входе через Google", error=e)
        return RedirectResponse(url='/login', status_code=302)