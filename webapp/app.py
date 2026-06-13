# webapp/app.py
# 🌐 Главный файл FastAPI приложения для медицинского бота
# ✅ ПОЛНОСТЬЮ АСИНХРОННЫЙ - без костылей с loop!

import os
import sys
import re
from pathlib import Path
# Добавляем webapp директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from middleware.rate_limit import add_rate_limit_middleware
import markdown
import bleach
from starlette_csrf import CSRFMiddleware

# 📁 Добавляем корневую папку в путь (чтобы импортировать db_postgresql.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 🔧 Импортируем настройки
from config import Config, validate_config

# 🌍 Импортируем функции локализации
from translations import t, get_current_language, set_language, get_supported_languages

# 🗄️ Импортируем функции базы данных
from db_postgresql import initialize_db_pool, close_db_pool, update_user_profile

from utils.flash import get_flashed_messages, flash, redirect_with_flash

from utils.context import get_template_context

from utils.telegram_notifications import send_admin_notification

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

"""
🎯 ЧТО ДЕЛАЕТ ЭТО ПРИЛОЖЕНИЕ:

1. Запускает FastAPI сервер (ASYNC!)
2. Позволяет пользователям входить через Google
3. Показывает личный кабинет с данными из PostgreSQL
4. Предоставляет чат с ИИ (используя gpt.py)
5. Позволяет загружать медицинские документы
6. 🆕 ПОЛНОСТЬЮ АСИНХРОННЫЙ - нет костылей с loop.run_until_complete!

ВСЕ данные берутся из той же БД, что использует Telegram бот!
"""

# ==========================================
# 🔄 LIFESPAN: Управление жизненным циклом
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    (современная замена on_event startup/shutdown)
    """
    # ==========================================
    # 🚀 STARTUP (выполняется при запуске)
    # ==========================================
    print("\n" + "="*50)
    print("🏥 МЕДИЦИНСКИЙ БОТ - FASTAPI ВЕРСИЯ")
    print("="*50)
    print("🔄 Инициализация базы данных...")
    
    try:
        await initialize_db_pool()
        print("✅ База данных подключена!")
    except Exception as e:
        print("Ошибка подключения к БД")
        raise
    
    # ==========================================
    # 🧠 ИНИЦИАЛИЗАЦИЯ ВЕКТОРНОЙ БАЗЫ
    # ==========================================
    print("🧠 Инициализация векторной базы (pgvector)...")
    
    try:
        from vector_db_postgresql import initialize_vector_db
        
        # Инициализируем векторную базу
        await initialize_vector_db()
        
        print("✅ Векторная база инициализирована!")
        
    except Exception as e:
        print("Ошибка инициализации векторной базы")
        print("⚠️ Веб-сервис будет работать БЕЗ векторного поиска")
    
    print(f"📊 База данных: PostgreSQL (Supabase)")
    print(f"🌍 Поддержка языков: RU, UK, EN, DE")
    print(f"⚡ Режим: Асинхронный (FastAPI)")
    print("="*50 + "\n")
    
    # ✅ yield = приложение работает здесь
    from webapp.email_scheduler import start_email_scheduler
    start_email_scheduler()
    print("✅ Email scheduler запущен")
    yield
    
    # ==========================================
    # 🛑 SHUTDOWN (выполняется при остановке)
    # ==========================================
    print("\n🧹 Закрытие соединений...")
    import asyncio

    # Закрываем векторную БД
    try:
        from vector_db_postgresql import close_vector_db
        await close_vector_db()
        print("✅ Векторная БД закрыта")
    except Exception as e:
        print("Ошибка при закрытии векторной БД")

    # Закрываем основную БД с таймаутом (для разработки)
    try:
        await asyncio.wait_for(close_db_pool(), timeout=2.0)
        print("✅ Основная БД закрыта")
    except asyncio.TimeoutError:
        print("⚠️ Таймаут закрытия БД — принудительно завершаем")
        # В разработке это нормально — соединения закроются автоматически
    except Exception as e:
        print("Ошибка при закрытии БД")

    try:
        from webapp.email_scheduler import stop_email_scheduler
        stop_email_scheduler()
        print("✅ Email scheduler остановлен")
    except Exception as e:
        print("Ошибка при остановке email scheduler")

# 🏗️ СОЗДАЁМ FASTAPI ПРИЛОЖЕНИЕ 
app = FastAPI(
    title="Medical Bot - Web",
    description="Async web interface for medical bot",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# 🔐 ДОБАВЛЯЕМ ПОДДЕРЖКУ СЕССИЙ (ПЕРВЫМ!)
app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SECRET_KEY,
    same_site="lax",
    https_only=os.getenv('HTTPS_ONLY', 'true').lower() == 'true',  # По умолчанию True
    max_age=3600 * 24 * 7
)

# 🛡️ Rate Limiting - защита от DoS/DDoS атак
add_rate_limit_middleware(app)

# 🛡️ ДОБАВЛЯЕМ CSRF ЗАЩИТУ (ПОСЛЕ SessionMiddleware!)
app.add_middleware(
    CSRFMiddleware,
    secret=Config.SECRET_KEY,
    cookie_name="csrf_token",
    cookie_path="/",
    cookie_domain=None,
    cookie_secure=os.getenv('HTTPS_ONLY', 'true').lower() == 'true',  # По умолчанию True
    cookie_httponly=False,
    cookie_samesite="lax",
    header_name="X-CSRF-Token",
    safe_methods={"GET", "HEAD", "OPTIONS"},
    exempt_urls={
        re.compile(r"^/api/.*"),
        re.compile(r"^/webhook/.*"),
        re.compile(r"^/auth/.*")
    }
)

# 🛡️ ДОБАВЛЯЕМ ЗАГОЛОВКИ БЕЗОПАСНОСТИ
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления заголовков безопасности ко всем ответам
    """
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Добавляем все заголовки из config.py
        for header_name, header_value in Config.SECURITY_HEADERS.items():
            if header_value:
                # ✅ Для PDF/изображений разрешаем iframe с того же домена
                if header_name == "X-Frame-Options" and (
                    request.url.path.startswith("/api/document-pdf/") or 
                    request.url.path.startswith("/api/document-image/")
                ):
                    response.headers[header_name] = "SAMEORIGIN"
                else:
                    response.headers[header_name] = header_value
        
        return response

# Применяем middleware
app.add_middleware(SecurityHeadersMiddleware)

# 🔒 HTTPS REDIRECT: Перенаправляем HTTP → HTTPS в production
from starlette.responses import RedirectResponse

if Config.IS_PRODUCTION:
    @app.middleware("http")
    async def https_redirect_except_health(request: Request, call_next):
        # Пропускаем /health без редиректа
        if request.url.path == "/health":
            return await call_next(request)
        
        # Railway использует X-Forwarded-Proto заголовок
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        
        # Редиректим только если реально пришёл по HTTP (не через Railway proxy)
        if forwarded_proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url, status_code=307)
        
        return await call_next(request)
    
    print("✅ HTTPS redirect включён (production режим, исключая /health)")

# ==========================================
# 🎯 UTM TRACKING: Отслеживание источников трафика (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ==========================================
class UTMTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для отслеживания UTM параметров
    Сохраняет только для главной страницы и только для новых пользователей
    """
    async def dispatch(self, request: Request, call_next):
        # ✅ БЕЗОПАСНАЯ ПРОВЕРКА: сначала проверяем что сессия существует
        try:
            # Проверяем только для главной страницы
            if request.url.path == "/":
                # Безопасная проверка наличия сессии
                has_session = "session" in request.scope
                
                if has_session and 'user_id' not in request.session:
                    # Сохраняем UTM параметры в сессию
                    utm_params = {}
                    for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid']:
                        value = request.query_params.get(key)
                        if value:
                            utm_params[key] = value
                    
                    # Сохраняем в сессию если есть хоть один параметр
                    if utm_params:
                        for key, value in utm_params.items():
                            request.session[key] = value
        except Exception:
            # Если что-то пошло не так - просто пропускаем
            pass
        
        response = await call_next(request)
        return response

# Применяем UTM tracking middleware В САМОМ КОНЦЕ
app.add_middleware(UTMTrackingMiddleware)

# 📁 НАСТРОЙКА ШАБЛОНОВ И СТАТИКИ
# Используем те же папки что были в Flask
templates = Jinja2Templates(directory="webapp/templates")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

# ✅ Фильтр для преобразования markdown в HTML (с защитой от XSS)
def markdown_filter(text):
    """Преобразует markdown в HTML с санитизацией"""
    if not text:
        return ""
    
    # 1. Преобразуем markdown в HTML
    html = markdown.markdown(
        text,
        extensions=['nl2br', 'sane_lists']
    )
    
    # 2. ✅ ОЧИЩАЕМ HTML от опасных тегов и атрибутов
    safe_html = bleach.clean(
        html,
        tags=[
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'code', 'pre', 'blockquote', 'hr', 'table',
            'thead', 'tbody', 'tr', 'th', 'td'
        ],
        attributes={
            'a': ['href', 'title'],  # Только безопасные атрибуты для ссылок
            '*': ['class']  # Разрешаем class для всех тегов (для стилей)
        },
        protocols=['http', 'https', 'mailto'],  # Разрешённые протоколы в ссылках
        strip=True  # Удаляем запрещённые теги вместо экранирования
    )
    
    return safe_html

templates.env.filters['markdown'] = markdown_filter

# ==========================================
# 📚 РЕГИСТРАЦИЯ РОУТЕРОВ (Blueprints в FastAPI)
# ==========================================

try:
    from routes import auth, dashboard, api, webhook, faq, account_linking, legal, seo
    
    # Регистрируем роутеры (как blueprints в Flask)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(api.router, prefix="/api", tags=["api"])
    app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
    app.include_router(faq.router, tags=["faq"])
    app.include_router(account_linking.router, tags=["account_linking"])
    app.include_router(legal.router, tags=["legal"])
    app.include_router(seo.router, tags=["seo"])
    
    print("✅ Все роутеры зарегистрированы")
    
except ImportError as e:
    print("Ошибка импорта роутеров")

# ==========================================
# 📍 БАЗОВЫЕ МАРШРУТЫ
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Главная страница (английская версия)
    """
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
    # Устанавливаем английский язык
    request.session['language'] = 'en'
    
    context = get_template_context(request)
    return templates.TemplateResponse('index.html', context)

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Страница входа через Google OAuth
    """
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
    context = get_template_context(request)
    return templates.TemplateResponse('login.html', context)

@app.get("/{lang}/login", response_class=HTMLResponse)
async def login_with_lang(request: Request, lang: str):
    if lang not in ['ru', 'uk', 'de']:
        raise HTTPException(status_code=404)
    
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
    request.session['language'] = lang
    context = get_template_context(request)
    return templates.TemplateResponse('login.html', context)

@app.get("/lab-test-analysis", response_class=HTMLResponse)
@app.get("/blood-test", response_class=HTMLResponse)
async def lab_test_landing(request: Request):   
    
    # Если пользователь уже авторизован → редирект в dashboard
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
    # Устанавливаем язык (по умолчанию английский для рекламы)
    if 'language' not in request.session:
        request.session['language'] = 'en'
    
    # 📊 Трекинг: пользователь пришёл с рекламы
    request.session['utm_source'] = 'google_ads'
    request.session['utm_campaign'] = 'lab_test_intent'
    request.session['landing_page'] = 'lab_test_analysis'
    
    context = get_template_context(request)
    return templates.TemplateResponse('lab_test_landing.html', context)

@app.get("/{lang}/lab-test-analysis", response_class=HTMLResponse)
@app.get("/{lang}/blood-test", response_class=HTMLResponse)
async def lab_test_landing_lang(request: Request, lang: str):
    """
    🩺 ИНТЕНТ-СТРАНИЦА: Лабораторные анализы (с языковым префиксом)
    """
    # Валидация языка
    if lang not in ['ru', 'uk', 'en', 'de']:
        return RedirectResponse(url='/lab-test-analysis', status_code=302)
    
    if request.session.get('user_id'):
        return RedirectResponse(url=f'/{lang}/dashboard', status_code=302)
    
    # Устанавливаем язык из URL
    request.session['language'] = lang
    
    request.session['utm_source'] = 'google_ads'
    request.session['utm_campaign'] = 'lab_test_intent'
    request.session['landing_page'] = 'lab_test_analysis'
    
    context = get_template_context(request)
    return templates.TemplateResponse('lab_test_landing.html', context)

@app.get("/logout")
async def logout(request: Request):
    """
    Выход из системы
    Очищаем сессию и редиректим на главную
    """
    request.session.clear()
    return RedirectResponse(url='/', status_code=302)

@app.get("/googlebb589ce9e5007262.html")
async def google_verification():
    """Google Search Console verification"""
    return "google-site-verification: googlebb589ce9e5007262.html"

@app.get("/set-language/{lang}")
async def set_language_route(request: Request, lang: str):
    """
    Смена языка с сохранением текущей страницы
    
    Теперь учитывает текущую страницу и добавляет языковой префикс
    """
    if lang not in ['ru', 'uk', 'en', 'de']:
        return RedirectResponse(url='/', status_code=302)
    
    request.session['language'] = lang
    
    # Если пользователь авторизован - сохраняем в БД
    user_id = request.session.get('user_id')
    if user_id:
        try:
            await update_user_profile(user_id, 'language', lang)
        except Exception as e:
            print("Ошибка сохранения языка")
    
    # Получаем текущую страницу
    referer = request.headers.get('referer', '/')
    
    # Парсим путь из referer
    from urllib.parse import urlparse
    parsed = urlparse(referer)
    current_path = parsed.path
    
    # Убираем старый языковой префикс если есть
    if current_path.startswith('/de/') or current_path.startswith('/ru/') or current_path.startswith('/uk/'):
        current_path = current_path[3:]  # Убираем /de, /ru, /uk
    elif current_path in ['/de', '/ru', '/uk']:
        current_path = '/'
    
    # 🔹 Список страниц БЕЗ языкового префикса (внутренние страницы)
    internal_pages = ['/dashboard', '/login', '/logout', '/auth', '/api', '/webhook', '/account-linking']

    # Проверяем является ли это внутренней страницей
    is_internal = any(current_path.startswith(prefix) for prefix in internal_pages)

    # Добавляем новый языковой префикс
    if is_internal or lang == 'en':
        # Для внутренних страниц и английского - префикс не нужен
        new_path = current_path
    else:
        # Для публичных SEO-страниц добавляем префикс
        new_path = f'/{lang}{current_path}'
    
    return RedirectResponse(url=new_path, status_code=302)

@app.get("/sitemap.xml")
async def sitemap():
    from fastapi.responses import Response
    from datetime import date
    from db_postgresql import get_db_connection, release_db_connection

    domain = "https://pulsebook.health"
    langs = ['en', 'de', 'ru', 'uk']
    today = date.today().strftime('%Y-%m-%d')
    static_pages = ['/', '/faq', '/privacy', '/terms', '/medical-disclaimer', '/about']

    def lang_prefix(lang):
        return f"/{lang}" if lang != 'en' else ""

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    xml += '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

    def make_url(loc, priority, changefreq, lastmod, alternates=None):
        s = f'  <url>\n'
        s += f'    <loc>{loc}</loc>\n'
        s += f'    <lastmod>{lastmod}</lastmod>\n'
        s += f'    <priority>{priority}</priority>\n'
        s += f'    <changefreq>{changefreq}</changefreq>\n'
        if alternates:
            for hreflang, href in alternates.items():
                s += f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{href}"/>\n'
        s += f'  </url>\n'
        return s

    # Статические страницы — каждый язык отдельным URL + hreflang на все языки
    for page in static_pages:
        priority = "1.0" if page == '/' else "0.7"
        alternates = {lang: f"{domain}{lang_prefix(lang)}{page}" for lang in langs}
        alternates['x-default'] = f"{domain}{page}"
        for lang in langs:
            loc = f"{domain}{lang_prefix(lang)}{page}"
            p = priority if lang == 'en' else ("0.9" if page == '/' else "0.6")
            xml += make_url(loc, p, "monthly", today, alternates)

    # Каталог /analysis
    analysis_alternates = {lang: f"{domain}{lang_prefix(lang)}/analysis" for lang in langs}
    analysis_alternates['x-default'] = f"{domain}/analysis"
    for lang in langs:
        loc = f"{domain}{lang_prefix(lang)}/analysis"
        xml += make_url(loc, "0.9", "weekly", today, analysis_alternates)

    # SEO страницы показателей из БД — один блок на slug с hreflang
    try:
        conn = await get_db_connection()
        try:
            rows = await conn.fetch("""
                SELECT DISTINCT ON (s.slug) s.slug,
                       COALESCE(s.updated_at, s.created_at, NOW()) as last_updated
                FROM seo_indicators s
                JOIN indicators i ON s.slug = i.slug
                WHERE i.is_published = TRUE
            """)
            slugs = [(row['slug'], row['last_updated']) for row in rows]
        finally:
            await release_db_connection(conn)

        for slug, last_updated in slugs:
            lastmod = last_updated.strftime('%Y-%m-%d')
            alternates = {lang: f"{domain}{lang_prefix(lang)}/analysis/{slug}" for lang in langs}
            alternates['x-default'] = f"{domain}/analysis/{slug}"
            for lang in langs:
                loc = f"{domain}{lang_prefix(lang)}/analysis/{slug}"
                xml += make_url(loc, "0.8", "monthly", lastmod, alternates)

    except Exception:
        pass

    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt")
async def robots():
    """
    robots.txt для поисковиков
    """
    from fastapi.responses import Response
    
    domain = "https://pulsebook.health" 
    
    content = f"""User-agent: *
Allow: /
Disallow: /dashboard
Disallow: /api/
Disallow: /auth/
Disallow: /webhook/
Disallow: /set-language/
Disallow: /ops

Sitemap: {domain}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

@app.get("/.well-known/assetlinks.json")
async def assetlinks():
    """Digital Asset Links для TWA Android"""
    from fastapi.responses import JSONResponse
    # SHA256 заполнить после сборки APK через bubblewrap
    return JSONResponse(content=[
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "health.pulsebook.app",
                "sha256_cert_fingerprints": [
                    "0E:C4:70:DF:B5:C3:46:5E:16:17:03:41:A1:D8:B5:9F:9B:46:CE:70:11:56:25:08:F6:E5:F1:B3:FC:D8:06:9F",
                    "DE:D7:70:E3:98:D5:96:29:79:75:F1:7D:15:75:CF:76:AA:73:C9:1F:2A:87:00:25:B9:35:AC:4F:9E:A6:5C:58"
                ]
            }
        }
    ])

from routes import ops
app.include_router(ops.router, tags=["ops"])

# ==========================================
# 🧪 ТЕСТОВЫЕ РОУТЫ
# ==========================================

@app.get("/test")
async def test_route():
    """Проверка что FastAPI работает"""
    return {
        "status": "ok",
        "message": "FastAPI работает! 🚀",
        "version": "2.0.0",
        "framework": "FastAPI (async)"
    }


@app.get("/health")
async def health_check():
    """Health check для Railway/мониторинга"""
    try:
        from db_postgresql import db_pool
        
        if db_pool:
            return {
                "status": "healthy",
                "database": "connected",
                "version": "2.0.0"
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": "database_error"
        }

# ==========================================
# 🧪 ТЕСТОВЫЙ ENDPOINT ДЛЯ ПРОВЕРКИ ОБНОВЛЕНИЙ
# ==========================================
@app.get("/version")
async def version():
    return {
        "version": "1.0.1"        
    }

@app.get("/app-onboarding", response_class=HTMLResponse)
async def app_onboarding(request: Request):
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
    # Если явно выбран язык через параметр
    lang_param = request.query_params.get('lang', '')
    if lang_param == 'en':
        request.session['language'] = 'en'
    else:
        accept_lang = request.headers.get('accept-language', 'en')
        lang_code = accept_lang.split(',')[0].split('-')[0].lower()
        supported = ['de', 'ru', 'uk']
        lang = lang_code if lang_code in supported else 'en'
        request.session['language'] = lang
    
    context = get_template_context(request)
    return templates.TemplateResponse('index_app.html', context)

@app.get("/{lang}/app-onboarding", response_class=HTMLResponse)
async def app_onboarding_lang(request: Request, lang: str):
    if lang not in ['de', 'ru', 'uk']:
        raise HTTPException(status_code=404)
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    request.session['language'] = lang
    context = get_template_context(request)
    return templates.TemplateResponse('index_app.html', context)

@app.get("/{lang}", response_class=HTMLResponse)
async def index_with_language(request: Request, lang: str):
    """
    Главная страница с языковым префиксом (/de, /ru, /uk)
    
    Примеры:
    /de → немецкая версия
    /ru → русская версия
    /uk → украинская версия
    """
    # Проверяем что это язык
    if lang in ['de', 'ru', 'uk']:
        if request.session.get('user_id'):
            return RedirectResponse(url='/dashboard', status_code=302)
        
        # Устанавливаем выбранный язык
        request.session['language'] = lang
        
        context = get_template_context(request)
        return templates.TemplateResponse('index.html', context)
    
    # Если не язык — пропускаем дальше (это может быть /login, /faq и т.д.)
    raise HTTPException(status_code=404)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений"""
    if exc.status_code == 401:
        return RedirectResponse(url="/", status_code=302)
    
    # Для остальных ошибок - стандартная обработка
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# ==========================================
# 🚀 ЗАПУСК (для локальной разработки)
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # ✅ СОХРАНЯЕМ ПРОВЕРКУ КОНФИГУРАЦИИ (это важно!)
    if not validate_config():
        print("\n❌ Исправьте настройки в .env файле и попробуйте снова\n")
        sys.exit(1)
    
    # ✅ ЧИТАЕМ DEBUG из .env
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # ✅ УЛУЧШЕННЫЕ ЛОГИ
    print("\n" + "="*60)
    print("🚀 Запуск FastAPI сервера...")
    print(f"🐛 Режим отладки: {'🟢 ON (автоперезагрузка)' if debug_mode else '🔴 OFF'}")
    print("="*60 + "\n")
    
    # ==========================================
    # 🔧 ЗАПУСК С ПРАВИЛЬНЫМИ ПАРАМЕТРАМИ
    # ==========================================
    
    if debug_mode:
        # 🟢 РЕЖИМ РАЗРАБОТКИ: с автоперезагрузкой и фильтрацией файлов
        print("📝 Следим за изменениями в файлах...")
        print("💡 Чтобы ВЫКЛЮЧИТЬ автоперезагрузку, установите DEBUG=false в .env\n")
        
        uvicorn.run(
            "webapp.app:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            reload_delay=1.0,  # ← Задержка убирает двойные перезагрузки
            reload_excludes=[  # ← Игнорируем временные файлы (КРИТИЧНО!)
                "*.log",
                "*.tmp",
                "*.temp",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                "__pycache__",
                ".pytest_cache",
                "venv",
                "env",
                ".venv",
                "ENV",
                "myenv",
                "*.db",
                "*.sqlite",
                "logs",
                "temp",
                "tmp",
                "files",
                "uploads",
                "*_debug.py",
                "debug_*.py"
            ],
            log_level="info"
        )
    else:
        # 🔴 ПРОДАКШЕН РЕЖИМ: без автоперезагрузки
        print("🚀 Запуск в продакшен режиме (без автоперезагрузки)\n")
        
        uvicorn.run(
            "webapp.app:app",
            host="0.0.0.0",
            port=5000,
            reload=False,
            log_level="info"
        )