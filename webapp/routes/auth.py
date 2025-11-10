# webapp/routes/auth.py
# 🔐 Авторизация через Google OAuth для медицинского бота - FASTAPI ВЕРСИЯ

import os
import sys
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

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
            print(f"📍 Найден существующий пользователь: {email}")
            return {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }
        
        # 2. Создаём нового пользователя
        print(f"🆕 Создаём нового веб-пользователя: {email}")
        
        # Генерируем ID
        temp_user_id = await conn.fetchval("SELECT generate_temp_web_user_id()")
        
        # Создаём пользователя с языком из сессии
        await conn.execute("""
            INSERT INTO users (user_id, name, google_id, email, registration_source, language, created_at)
            VALUES ($1, $2, $3, $4, 'web', $5, NOW())
            ON CONFLICT (user_id) DO NOTHING
        """, temp_user_id, name, google_id, email, session_language)
        
        # Создаём лимиты
        await conn.execute("""
            INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left, subscription_type)
            VALUES ($1, 2, 10, 'free')
            ON CONFLICT (user_id) DO NOTHING
        """, temp_user_id)
        
        print(f"✅ Веб-пользователь создан: user_id={temp_user_id}")
        
        return {
            'user_id': temp_user_id,
            'name': name,
            'email': email
        }
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")
        import traceback
        traceback.print_exc()
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
    redirect_uri = request.url_for('google_callback')
    
    # ✅ AWAIT! В Flask не было await
    return await google.authorize_redirect(request, redirect_uri)


# ==========================================
# 🔄 МАРШРУТ 2: Обработка ответа от Google
# ==========================================

@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Google возвращает пользователя сюда после успешного входа
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
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
        name = user_info.get('name', 'Пользователь')
        
        print(f"✅ Пользователь вошёл через Google: {email}")
        
        # ✅ AWAIT! Создаём/находим пользователя
        # Получаем текущий язык из сессии (тот что выбрал пользователь до входа)
        current_session_lang = request.session.get('language', 'en')

        # Создаём/находим пользователя, передаем текущий язык
        user = await find_or_create_web_user(google_id, email, name, current_session_lang)
        
        if user:
            # Сохраняем данные в сессии
            request.session['user_id'] = user['user_id']
            request.session['email'] = email
            request.session['name'] = name
            request.session['google_id'] = google_id
            
            # ✅ AWAIT! Получаем язык пользователя из БД
            try:
                conn = await get_db_connection()
                
                try:
                    result = await conn.fetchrow(
                        "SELECT language FROM users WHERE user_id = $1", 
                        user['user_id']
                    )
                    
                    if result and result['language']:
                        user_language = result['language']
                        # ✅ Загружаем язык из БД только если он там есть
                        request.session['language'] = user_language
                        print(f"✅ Язык загружен из БД: {user_language}")
                    else:
                        # ⚠️ Если язык не найден в БД - оставляем тот что был в сессии
                        # (для новых пользователей это язык который они выбрали до входа)
                        print(f"⚠️ Язык не найден в БД, оставляем текущий из сессии: {request.session.get('language', 'en')}")
                        
                finally:
                    await release_db_connection(conn)
                    
            except Exception as e:
                print(f"⚠️ Ошибка загрузки языка: {e}")
                if 'language' not in request.session:
                    request.session['language'] = 'en'
            
            print(f"✅ Пользователь авторизован: user_id={user['user_id']}")
            
            # Редиректим в личный кабинет
            return RedirectResponse(url='/dashboard', status_code=302)
            
        else:
            print("❌ Не удалось создать пользователя")
            return RedirectResponse(url='/login', status_code=302)
            
    except Exception as e:
        print(f"❌ Ошибка при входе через Google: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url='/login', status_code=302)


# ==========================================
# 📊 ИТОГО: ЧТО ИЗМЕНИЛОСЬ?
# ==========================================
"""
❌ БЫЛО (Flask + psycopg2):
- 200+ строк кода
- import psycopg2 - КОСТЫЛЬ! 🔴
- get_clean_database_url() - КОСТЫЛЬ! 🔴
- cursor.execute() везде - КОСТЫЛЬ! 🔴
- conn.commit(), cursor.close() - КОСТЫЛИ! 🔴
- Синхронная функция find_or_create_web_user_sync

✅ СТАЛО (FastAPI + asyncpg):
- 150 строк кода
- БЕЗ psycopg2! ✅
- БЕЗ get_clean_database_url()! ✅
- Просто await conn.fetchrow() ✅
- Async функция find_or_create_web_user ✅
- authlib.integrations.starlette_client вместо flask_client

ГЛАВНЫЕ ИЗМЕНЕНИЯ:
1. flask_client → starlette_client
2. def → async def
3. google.authorize_redirect(...) → await google.authorize_redirect(request, ...)
4. google.authorize_access_token() → await google.authorize_access_token(request)
5. psycopg2 → asyncpg (через готовые функции)
6. url_for() → request.url_for()
7. redirect() → RedirectResponse()

РАЗНИЦА: -50 строк, 0 костылей, полностью async! 🎉
"""