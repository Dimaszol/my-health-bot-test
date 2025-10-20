# webapp/routes/dashboard.py
# 🏠 Личный кабинет пользователя - FASTAPI ВЕРСИЯ (полностью async!)

import sys
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ✅ ИМПОРТИРУЕМ ГОТОВЫЕ ASYNC ФУНКЦИИ из db_postgresql.py
# БЕЗ psycopg2! БЕЗ костылей!
from db_postgresql import (
    get_user_profile,           # ✅ async функция
    get_documents_by_user,      # ✅ async функция
    get_last_messages           # ✅ async функция (возвращает list of tuples)
)

# Импортируем функции локализации
from webapp.translations import t, get_current_language, get_supported_languages
from webapp.utils.context import get_template_context

# 📘 СОЗДАЁМ ROUTER (аналог Blueprint в Flask)
router = APIRouter()

# 📁 НАСТРОЙКА ШАБЛОНОВ
templates = Jinja2Templates(directory="webapp/templates")

async def get_user_stats(user_id: int) -> dict:
    """
    Получить статистику пользователя
    ✅ ПОЛНОСТЬЮ ASYNC!
    """
    try:
        from db_postgresql import get_db_connection, release_db_connection
        
        conn = await get_db_connection()
        
        try:
            # Количество документов
            total_docs = await conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE user_id = $1", 
                user_id
            )
            
            # Количество сообщений
            total_messages = await conn.fetchval(
                "SELECT COUNT(*) FROM chat_history WHERE user_id = $1", 
                user_id
            )
            
            # Лимиты
            limits = await conn.fetchrow(
                "SELECT documents_left, gpt4o_queries_left FROM user_limits WHERE user_id = $1",
                user_id
            )
            
            return {
                'total_documents': total_docs or 0,
                'total_messages': total_messages or 0,
                'documents_left': limits['documents_left'] if limits else 2,
                'queries_left': limits['gpt4o_queries_left'] if limits else 10
            }
        finally:
            await release_db_connection(conn)
            
    except Exception as e:
        print(f"❌ Ошибка get_user_stats: {e}")
        return {
            'total_documents': 0,
            'total_messages': 0,
            'documents_left': 0,
            'queries_left': 0
        }


# ==========================================
# 🔒 DEPENDENCY: Проверка авторизации
# ==========================================

async def get_current_user(request: Request) -> int:
    """
    Dependency для проверки авторизации
    (аналог декоратора @login_required в Flask)
    
    Что делает:
    - Проверяет есть ли user_id в сессии
    - Если НЕТ → редирект на /login
    - Если ДА → возвращает user_id
    """
    user_id = request.session.get('user_id')
    if not user_id:
        # Если не авторизован - редиректим
        raise RedirectResponse(url='/login', status_code=302)
    return user_id


# ==========================================
# 📍 МАРШРУТЫ ЛИЧНОГО КАБИНЕТА
# ==========================================

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: int = Depends(get_current_user)):
    """
    Главная страница личного кабинета
    
    ✅ СМОТРИ КАК ЧИСТО! Просто await вместо всех костылей!
    """
    # ✅ ПРОСТО AWAIT! Никаких loop.run_until_complete!
    profile = await get_user_profile(user_id)
    documents = await get_documents_by_user(user_id, limit=5)
    
    # get_last_messages возвращает list of tuples, преобразуем в dict
    messages_tuples = await get_last_messages(user_id, limit=10)
    chat_history = [
        {
            'role': role,
            'message': message,
            'timestamp': None  # Добавим если нужно
        }
        for role, message in messages_tuples
    ]
    
    stats = await get_user_stats(user_id)
    
    # Формируем контекст
    context = get_template_context(request)
    context.update({
        'user': profile,
        'documents': documents,
        'chat_history': chat_history,
        'stats': stats
    })
    
    return templates.TemplateResponse('dashboard.html', context)


@router.get("/documents", response_class=HTMLResponse)
async def documents(request: Request, user_id: int = Depends(get_current_user)):
    """
    Страница со списком всех документов пользователя
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
    """
    # ✅ ПРОСТО AWAIT!
    docs = await get_documents_by_user(user_id)
    
    context = get_template_context(request)
    context['documents'] = docs
    
    return templates.TemplateResponse('documents.html', context)


@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request, user_id: int = Depends(get_current_user)):
    """
    Страница чата с ИИ
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
    """
    # ✅ ПРОСТО AWAIT!
    messages_tuples = await get_last_messages(user_id, limit=50)
    profile = await get_user_profile(user_id)
    
    # Преобразуем в формат для шаблона
    chat_history = [
        {
            'role': role,
            'message': message,
            'timestamp': None
        }
        for role, message in messages_tuples
    ]
    
    context = get_template_context(request)
    context.update({
        'chat_history': chat_history,
        'user': profile
    })
    
    return templates.TemplateResponse('chat.html', context)


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user_id: int = Depends(get_current_user)):
    """
    Детальная страница профиля пользователя
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
    """
    # ✅ ПРОСТО AWAIT!
    profile_data = await get_user_profile(user_id)
    
    context = get_template_context(request)
    context['user'] = profile_data
    
    return templates.TemplateResponse('profile.html', context)


# ==========================================
# 📊 ИТОГО: ЧТО ИЗМЕНИЛОСЬ?
# ==========================================
"""
❌ БЫЛО (Flask + psycopg2):
- 150+ строк кода с psycopg2
- Костыли: get_clean_database_url()
- Костыли: cursor.execute() везде
- Костыли: conn.commit(), cursor.close(), conn.close()
- 4 синхронные функции-дубликаты

✅ СТАЛО (FastAPI + asyncpg):
- ~120 строк кода
- БЕЗ psycopg2!
- ПРОСТО await готовых функций из db_postgresql.py
- Переиспользуем код телеграм-бота!
- Dependency injection вместо декораторов

РАЗНИЦА: -30 строк, 0 костылей! 🎉
"""