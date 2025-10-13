# webapp/routes/dashboard.py
# 🏠 Личный кабинет пользователя - ПОЛНОСТЬЮ СИНХРОННАЯ ВЕРСИЯ

import os
import sys
import psycopg2
from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from urllib.parse import urlparse, urlunparse

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 📘 СОЗДАЁМ BLUEPRINT
dashboard_bp = Blueprint('dashboard', __name__)


# 🔧 ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Получить чистый DATABASE_URL
def get_clean_database_url():
    """Убирает asyncpg параметры из DATABASE_URL для psycopg2"""
    database_url = os.getenv('DATABASE_URL')
    parsed = urlparse(database_url)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '', '', ''
    ))


# 🔧 СИНХРОННЫЕ ФУНКЦИИ для работы с БД
def get_user_profile_sync(user_id: int):
    """Синхронная версия get_user_profile"""
    try:
        conn = psycopg2.connect(get_clean_database_url())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, row))
        else:
            result = {}
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Ошибка get_user_profile_sync: {e}")
        return {}


def get_documents_by_user_sync(user_id: int, limit: int = 999):
    """Синхронная версия get_documents_by_user"""
    try:
        conn = psycopg2.connect(get_clean_database_url())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, file_type, uploaded_at, summary
            FROM documents 
            WHERE user_id = %s AND confirmed = TRUE
            ORDER BY uploaded_at DESC 
            LIMIT %s
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Ошибка get_documents_by_user_sync: {e}")
        return []


def get_last_messages_sync(user_id: int, limit: int = 50):
    """Синхронная версия get_last_messages"""
    try:
        conn = psycopg2.connect(get_clean_database_url())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, message, timestamp
            FROM chat_history 
            WHERE user_id = %s 
            ORDER BY id DESC 
            LIMIT %s
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        # Возвращаем в правильном порядке (от старых к новым)
        result = []
        for role, message, timestamp in reversed(rows):
            result.append({
                'role': role,
                'message': message,
                'timestamp': timestamp
            })
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Ошибка get_last_messages_sync: {e}")
        return []


def get_user_stats_sync(user_id: int):
    """Синхронная версия get_user_stats"""
    try:
        conn = psycopg2.connect(get_clean_database_url())
        cursor = conn.cursor()
        
        # Количество документов
        cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id = %s", (user_id,))
        total_docs = cursor.fetchone()[0]
        
        # Количество сообщений
        cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = %s", (user_id,))
        total_messages = cursor.fetchone()[0]
        
        # Лимиты
        cursor.execute("""
            SELECT documents_left, gpt4o_queries_left 
            FROM user_limits 
            WHERE user_id = %s
        """, (user_id,))
        limits = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            'total_documents': total_docs or 0,
            'total_messages': total_messages or 0,
            'documents_left': limits[0] if limits else 2,
            'queries_left': limits[1] if limits else 10
        }
    except Exception as e:
        print(f"❌ Ошибка get_user_stats_sync: {e}")
        return {
            'total_documents': 0,
            'total_messages': 0,
            'documents_left': 0,
            'queries_left': 0
        }


# 🔒 ДЕКОРАТОР: Проверка авторизации
def login_required(f):
    """
    Декоратор для защиты маршрутов
    
    Что делает:
    - Проверяет есть ли user_id в сессии
    - Если НЕТ → редирект на /login
    - Если ДА → выполняет функцию
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# 🏠 ГЛАВНАЯ СТРАНИЦА КАБИНЕТА
@dashboard_bp.route('/')
@login_required
def dashboard():
    """Главная страница личного кабинета"""
    user_id = session.get('user_id')
    
    # Используем синхронные функции
    profile = get_user_profile_sync(user_id)
    documents = get_documents_by_user_sync(user_id, limit=5)
    chat_history = get_last_messages_sync(user_id, limit=10)
    stats = get_user_stats_sync(user_id)
    
    return render_template('dashboard.html',
        user=profile,
        documents=documents,
        chat_history=chat_history,
        stats=stats
    )


# 📄 СТРАНИЦА ДОКУМЕНТОВ
@dashboard_bp.route('/documents')
@login_required
def documents():
    """Страница со списком всех документов пользователя"""
    user_id = session.get('user_id')
    docs = get_documents_by_user_sync(user_id)
    return render_template('documents.html', documents=docs)


# 💬 СТРАНИЦА ЧАТА
@dashboard_bp.route('/chat')
@login_required
def chat():
    """Страница чата с ИИ"""
    user_id = session.get('user_id')
    history = get_last_messages_sync(user_id, limit=50)
    profile = get_user_profile_sync(user_id)
    
    return render_template('chat.html', 
        chat_history=history,
        user=profile
    )


# 👤 СТРАНИЦА ПРОФИЛЯ
@dashboard_bp.route('/profile')
@login_required
def profile():
    """Детальная страница профиля пользователя"""
    user_id = session.get('user_id')
    profile_data = get_user_profile_sync(user_id)
    
    return render_template('profile.html', user=profile_data)