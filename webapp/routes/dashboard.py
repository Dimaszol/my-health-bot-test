# webapp/routes/dashboard.py
# 🏠 Личный кабинет пользователя - FASTAPI ВЕРСИЯ (полностью async!)

import sys
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import markdown

# Создаём templates и регистрируем фильтр markdown
templates = Jinja2Templates(directory="webapp/templates")

def markdown_filter(text):
    """Преобразует markdown в HTML"""
    if not text:
        return ""
    return markdown.markdown(text, extensions=['nl2br', 'sane_lists'])

# Регистрируем фильтр
templates.env.filters['markdown'] = markdown_filter

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
# templates = Jinja2Templates(directory="webapp/templates")

def calculate_profile_completion(user):
    """Рассчитывает процент заполненности медицинской анкеты (12 полей)"""
    if not user:
        return 0
    
    # Проверяем является ли user словарём или объектом
    if isinstance(user, dict):
        fields = [
            user.get('name'),                    # Имя
            user.get('birth_year'),              # Год рождения
            user.get('gender'),                  # Пол
            user.get('height_cm'),               # Рост
            user.get('weight_kg'),               # Вес
            user.get('chronic_conditions'),      # Хронические заболевания
            user.get('allergies'),               # Аллергии
            user.get('family_history'),          # Семейная история
            user.get('medications'),             # Лекарства
            user.get('smoking'),                 # Курение
            user.get('alcohol'),                 # Алкоголь
            user.get('physical_activity')        # Физическая активность
        ]
    else:
        # Если это объект с атрибутами
        fields = [
            user.name,
            user.birth_year,
            user.gender,
            user.height_cm,
            user.weight_kg,
            user.chronic_conditions,
            user.allergies,
            user.family_history,
            user.medications,
            user.smoking,
            user.alcohol,
            user.physical_activity
        ]
    
    filled_fields = sum(1 for field in fields if field)
    total_fields = len(fields)
    
    return round((filled_fields / total_fields) * 100)

def get_plan_display_name(subscription_type: str, lang: str = 'ru') -> str:
    """
    Конвертирует внутренние названия тарифов в ключи переводов
    """
    plan_mapping = {
        'basic_sub': 'plan_lite',
        'premium_sub': 'plan_pro',
        None: 'plan_free'
    }
    
    plan_key = plan_mapping.get(subscription_type, 'plan_free')
    return t(plan_key, lang)

async def get_user_stats(user_id: int) -> dict:
    """
    Получить статистику пользователя
    ✅ ПОЛНОСТЬЮ ASYNC!
    """
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
            "SELECT COUNT(*) FROM chat_history WHERE user_id = $1 AND role = 'user'", 
            user_id
        )
        
        # Лимиты
        limits = await conn.fetchrow(
            "SELECT documents_left, gpt4o_queries_left FROM user_limits WHERE user_id = $1",
            user_id
        )
        
        # ✅ НОВОЕ: Получаем package_id из user_subscriptions
        subscription = await conn.fetchrow("""
            SELECT package_id 
            FROM user_subscriptions 
            WHERE user_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        subscription_type = subscription['package_id'] if subscription else None
        
        return {
            'total_documents': total_docs or 0,
            'total_messages': total_messages or 0,
            'documents_left': limits['documents_left'] if limits else 2,
            'queries_left': limits['gpt4o_queries_left'] if limits else 10,
            'subscription_type': subscription_type  # ✅ ДОБАВИЛИ
        }
        
    except Exception as e:
        print(f"❌ Ошибка get_user_stats: {e}")
        return {
            'total_documents': 0,
            'total_messages': 0,
            'documents_left': 0,
            'queries_left': 0,
            'subscription_type': None  # ✅ ДОБАВИЛИ в fallback
        }
        
    finally:
        await release_db_connection(conn)  # ✅ ВСЕГДА освобождаем!


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

    """
    # ✅ НОВОЕ: Проверяем истекшие лимиты ДО отображения дашборда
    from subscription_manager import SubscriptionManager
    await SubscriptionManager.check_and_reset_expired_limits(user_id)
    
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
    
    # Проверяем источник регистрации
    from db_postgresql import get_db_connection, release_db_connection
    conn = await get_db_connection()
    try:
        user_info = await conn.fetchrow(
            "SELECT registration_source FROM users WHERE user_id = $1",
            user_id
        )
        show_telegram_connect = user_info['registration_source'] == 'web' if user_info else False
    finally:
        await release_db_connection(conn)

    from db_postgresql import get_user_language
    # Получаем язык пользователя
    lang = await get_user_language(user_id)

    # Получаем красивое название тарифа
    current_plan_name = get_plan_display_name(
        subscription_type=stats.get('subscription_type'),
        lang=lang
    )

    # Формируем контекст
    context = get_template_context(request)
    context.update({
        'user': profile,
        'documents': documents,
        'chat_history': chat_history,
        'stats': stats,
        'show_telegram_connect': show_telegram_connect,
        'current_plan_name': current_plan_name,
        'profile_completion': calculate_profile_completion(profile)
    })
    
    return templates.TemplateResponse('dashboard.html', context)


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request, user_id: int = Depends(get_current_user)):
    """
    Страница документов
    
    ✅ ОБНОВЛЕНО: Загружаем medical_timeline + DEBUG логи
    """
    from db_postgresql import get_db_connection, release_db_connection
    from medical_timeline import get_timeline_by_document  # ✅ НОВЫЙ ИМПОРТ
    from subscription_manager import check_document_limit
    has_document_limits = await check_document_limit(user_id)
    
    conn = await get_db_connection()
    
    try:
        # ✅ ВАЖНО: Выбираем ВСЕ поля, включая raw_text и summary
        documents = await conn.fetch("""
            SELECT 
                id, 
                title, 
                file_path, 
                file_type, 
                raw_text,
                summary,
                uploaded_at,
                confirmed
            FROM documents
            WHERE user_id = $1
            ORDER BY uploaded_at DESC
        """, user_id)
        
        # Преобразуем в список словарей
        docs_list = [dict(doc) for doc in documents]
        
        # ✅ НОВОЕ: Для каждого документа загружаем его medical_timeline записи
        for doc in docs_list:
            # Получаем timeline записи для этого документа
            timeline_entries = await get_timeline_by_document(doc['id'], user_id)
            
            # Добавляем записи в документ
            doc['timeline_entries'] = timeline_entries
        
        # 🐛 DEBUG: Выводим в консоль для проверки
        print(f"\n📋 Загружено документов: {len(docs_list)}")
        for doc in docs_list:
            print(f"  - ID: {doc['id']}, title: {doc['title']}")
            print(f"    has raw_text: {bool(doc.get('raw_text'))}")
            print(f"    has summary: {bool(doc.get('summary'))}")
            if doc.get('raw_text'):
                print(f"    raw_text length: {len(doc['raw_text'])} chars")
            if doc.get('summary'):
                print(f"    summary length: {len(doc['summary'])} chars")
            # ✅ НОВЫЙ DEBUG: количество timeline записей
            timeline_count = len(doc.get('timeline_entries', []))
            print(f"    timeline entries: {timeline_count}")
        
    finally:
        await release_db_connection(conn)
    
    # ✅ ИСПОЛЬЗУЕМ get_template_context как в старой версии!
    context = get_template_context(request)
    context['documents'] = docs_list
    context['has_document_limits'] = has_document_limits
    
    return templates.TemplateResponse("documents.html", context)

@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request, user_id: int = Depends(get_current_user)):
    """
    Страница чата с ИИ
    
    """
    from subscription_manager import check_gpt4o_limit  # ← НОВОЕ
    
    # ✅ ПРОСТО AWAIT!
    messages_tuples = await get_last_messages(user_id, limit=50)
    profile = await get_user_profile(user_id)
    
    # ✅ ПРОВЕРЯЕМ ЛИМИТЫ НА ДЕТАЛЬНЫЕ КОНСУЛЬТАЦИИ
    has_detailed_consultations = await check_gpt4o_limit(user_id)  # ← НОВОЕ
    
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
        'user': profile,
        'has_detailed_consultations': has_detailed_consultations  # ← НОВОЕ
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

@router.get("/subscription", response_class=HTMLResponse)
async def subscription_page(request: Request, user_id: int = Depends(get_current_user)):
    """
    Страница подписок и тарифов
    
    Показывает:
    - Доступные тарифные планы
    - Текущую подписку пользователя
    - Оставшиеся лимиты
    """
    from stripe_config import StripeConfig
    from subscription_manager import SubscriptionManager
    from db_postgresql import get_user_language, get_db_connection, release_db_connection

    # Получаем язык пользователя
    lang = await get_user_language(user_id)
    
    # Получаем текущие лимиты
    limits = await SubscriptionManager.get_user_limits(user_id)
    
    # ✅ НОВОЕ: Проверяем активную подписку в таблице user_subscriptions
    current_package_id = None
    conn = await get_db_connection()
    try:
        subscription = await conn.fetchrow("""
            SELECT package_id, status 
            FROM user_subscriptions 
            WHERE user_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        if subscription:
            current_package_id = subscription['package_id']
            print(f"✅ Найдена активная подписка: {current_package_id}")
        else:
            print(f"ℹ️ У пользователя нет активной подписки")
    finally:
        await release_db_connection(conn)
    
    # Получаем все доступные тарифы
    packages = StripeConfig.get_all_packages()
    
    # Форматируем тарифы для шаблона
    formatted_packages = []
    for package_id, package_info in packages.items():
        formatted_packages.append({
            'id': package_id,
            'name_key': package_info['user_friendly_name_key'],
            'price': package_info['price_display'],
            'price_cents': package_info['price_cents'],
            'type': package_info['type'],
            'documents': package_info['documents'],
            'gpt4o_queries': package_info['gpt4o_queries'],
            'features_keys': package_info['features_keys'],
            'is_current': package_id == current_package_id  # ✅ ИСПРАВЛЕНО
        })

    # Сортируем по цене
    formatted_packages.sort(key=lambda x: x['price_cents'])
    
    # Подготавливаем контекст
    context = get_template_context(request)
    context['packages'] = formatted_packages
    context['limits'] = limits
    context['has_subscription'] = current_package_id is not None  # ✅ ИСПРАВЛЕНО
    
    return templates.TemplateResponse("subscription.html", context)
