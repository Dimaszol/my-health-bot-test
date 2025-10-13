# webapp/routes/auth.py
# 🔐 Авторизация через Google OAuth для медицинского бота

import os
import sys
import asyncio
from flask import Blueprint, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webapp.config import Config
from db_postgresql import get_user_profile

"""
🎯 КАК РАБОТАЕТ GOOGLE OAUTH (простыми словами):

1. Пользователь нажимает "Войти через Google" → /auth/google
2. Flask перенаправляет пользователя на сайт Google
3. Google спрашивает: "Разрешить доступ к вашему email и имени?"
4. Пользователь нажимает "Да"
5. Google отправляет пользователя обратно → /auth/google/callback
6. Flask получает данные пользователя (email, имя, google_id)
7. Flask проверяет: есть ли такой пользователь в БД?
   - Если ДА → входим (сохраняем user_id в session)
   - Если НЕТ → создаём нового пользователя, потом входим
8. Редирект в личный кабинет

БЕЗОПАСНОСТЬ: Мы НЕ храним пароли! Google всё проверяет за нас.
"""

# 📘 СОЗДАЁМ BLUEPRINT (модуль маршрутов)
auth_bp = Blueprint('auth', __name__)

# 🔧 НАСТРОЙКА GOOGLE OAUTH
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


# 🚀 МАРШРУТ 1: Начало входа через Google
@auth_bp.route('/google')
def google_login():
    """
    Перенаправляет пользователя на страницу входа Google
    
    Что происходит:
    1. Генерируем redirect_uri (куда Google вернёт пользователя)
    2. Отправляем пользователя на Google для авторизации
    """
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


# 🔄 МАРШРУТ 2: Обработка ответа от Google
@auth_bp.route('/google/callback')
def google_callback():
    """
    Google возвращает пользователя сюда после успешного входа
    """
    try:
        # Получаем токен от Google
        token = google.authorize_access_token()
        
        # Получаем информацию о пользователе
        user_info = token.get('userinfo')
        
        if not user_info:
            print("❌ Не удалось получить данные пользователя от Google")
            return redirect(url_for('login'))
        
        # Извлекаем данные
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', 'Пользователь')
        
        print(f"✅ Пользователь вошёл через Google: {email}")
        
        # 🔧 СИНХРОННОЕ РЕШЕНИЕ: Используем psycopg2 напрямую
        user = find_or_create_web_user_sync(google_id, email, name)
        
        if user:
            # Сохраняем user_id в сессии
            session['user_id'] = user['user_id']
            session['email'] = email
            session['name'] = name
            session['google_id'] = google_id
            
            print(f"✅ Пользователь авторизован: user_id={user['user_id']}")
            
            return redirect(url_for('dashboard.dashboard'))
        else:
            print("❌ Не удалось создать пользователя")
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"❌ Ошибка при входе через Google: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login'))


# 🔧 СИНХРОННАЯ ФУНКЦИЯ для создания пользователя
def find_or_create_web_user_sync(google_id: str, email: str, name: str):
    """
    СИНХРОННАЯ версия создания пользователя для Flask
    Использует psycopg2 вместо asyncpg
    """
    import psycopg2
    import os
    from urllib.parse import urlparse, urlunparse
    
    database_url = os.getenv('DATABASE_URL')
    
    # 🔧 ИСПРАВЛЕНИЕ: Убираем asyncpg-специфичные параметры из URL
    # psycopg2 не понимает pool_timeout, pool_max_size и т.д.
    parsed = urlparse(database_url)
    
    # Убираем query параметры (они для asyncpg)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '',  # params
        '',  # query ← убираем это
        ''   # fragment
    ))
    
    try:
        conn = psycopg2.connect(clean_url)
        cursor = conn.cursor()
        
        # 1. Ищем существующего пользователя
        cursor.execute(
            "SELECT user_id, name, email FROM users WHERE google_id = %s",
            (google_id,)
        )
        
        user = cursor.fetchone()
        
        if user:
            print(f"📍 Найден существующий пользователь: {email}")
            cursor.close()
            conn.close()
            return {
                'user_id': user[0],
                'name': user[1],
                'email': user[2]
            }
        
        # 2. Создаём нового пользователя
        print(f"🆕 Создаём нового веб-пользователя: {email}")
        
        # Генерируем ID
        cursor.execute("SELECT generate_temp_web_user_id()")
        temp_user_id = cursor.fetchone()[0]
        
        # Создаём пользователя
        cursor.execute("""
            INSERT INTO users (user_id, name, google_id, email, registration_source, created_at)
            VALUES (%s, %s, %s, %s, 'web', NOW())
            ON CONFLICT (user_id) DO NOTHING
        """, (temp_user_id, name, google_id, email))
        
        # Создаём лимиты
        cursor.execute("""
            INSERT INTO user_limits (user_id, documents_left, gpt4o_queries_left, subscription_type)
            VALUES (%s, 2, 10, 'free')
            ON CONFLICT (user_id) DO NOTHING
        """, (temp_user_id,))
        
        conn.commit()
        
        print(f"✅ Веб-пользователь создан: user_id={temp_user_id}")
        
        cursor.close()
        conn.close()
        
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


# 🔧 ИНИЦИАЛИЗАЦИЯ OAUTH при импорте модуля
def init_oauth(app):
    """
    Инициализирует OAuth с Flask приложением
    
    Вызывается из app.py при регистрации blueprint
    """
    oauth.init_app(app)