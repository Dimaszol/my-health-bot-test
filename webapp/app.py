# webapp/app.py
# 🌐 Главный файл FastAPI приложения для медицинского бота
# ✅ ПОЛНОСТЬЮ АСИНХРОННЫЙ - без костылей с loop!

import os
import sys
import re
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from middleware.rate_limit import add_rate_limit_middleware
import markdown
import bleach
from starlette_csrf import CSRFMiddleware

# 📁 Добавляем корневую папку в путь (чтобы импортировать db_postgresql.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 🔧 Импортируем настройки
from webapp.config import Config, validate_config

# 🌍 Импортируем функции локализации
from webapp.translations import t, get_current_language, set_language, get_supported_languages

# 🗄️ Импортируем функции базы данных
from db_postgresql import initialize_db_pool, close_db_pool, update_user_profile

from webapp.utils.flash import get_flashed_messages, flash

from webapp.utils.context import get_template_context


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

# 🏗️ СОЗДАЁМ FASTAPI ПРИЛОЖЕНИЕ
app = FastAPI(
    title="Медицинский Бот - Веб Версия",
    description="Асинхронный веб-интерфейс для медицинского бота",
    version="2.0.0",
    lifespan=lifespan
)

# 🔐 ДОБАВЛЯЕМ ПОДДЕРЖКУ СЕССИЙ (как в Flask)
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

# 🛡️ Rate Limiting - защита от DoS/DDoS атак
add_rate_limit_middleware(app)

# 🛡️ ДОБАВЛЯЕМ CSRF ЗАЩИТУ
from starlette_csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    secret=Config.SECRET_KEY,  # Используем тот же ключ что и для сессий
    cookie_name="csrf_token",
    cookie_path="/",
    cookie_domain=None,
    cookie_secure=False,  # ⚠️ Поставь True когда будет HTTPS!
    cookie_httponly=True,
    cookie_samesite="lax",
    header_name="X-CSRF-Token",
    safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"},  # Эти методы не проверяются
    exempt_urls={
        re.compile(r"^/api/.*"),  # Исключаем все API эндпоинты
        re.compile(r"^/webhook/.*")  # Исключаем вебхуки
    }
)

# 🛡️ ДОБАВЛЯЕМ ЗАГОЛОВКИ БЕЗОПАСНОСТИ
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления заголовков безопасности ко всем ответам
    
    Защищает от:
    - XSS атак (Content-Security-Policy)
    - Clickjacking (X-Frame-Options)
    - MIME-type снифинга (X-Content-Type-Options)
    """
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Добавляем все заголовки из config.py
        for header_name, header_value in Config.SECURITY_HEADERS.items():
            # Пропускаем пустые значения (например HSTS в development)
            if header_value:
                response.headers[header_name] = header_value
        
        return response

# Применяем middleware
app.add_middleware(SecurityHeadersMiddleware)

# 🔒 HTTPS REDIRECT: Перенаправляем HTTP → HTTPS в production
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if Config.IS_PRODUCTION:
    app.add_middleware(HTTPSRedirectMiddleware)
    print("✅ HTTPS redirect включён (production режим)")

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
    from webapp.routes import auth, dashboard, api, webhook, faq, account_linking, legal
    
    # Регистрируем роутеры (как blueprints в Flask)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(api.router, prefix="/api", tags=["api"])
    app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
    app.include_router(faq.router, tags=["faq"])
    app.include_router(account_linking.router, tags=["account_linking"])
    app.include_router(legal.router, tags=["legal"])
    
    print("✅ Все роутеры зарегистрированы")
    
except ImportError as e:
    print("Ошибка импорта роутеров")


# ==========================================
# 📍 БАЗОВЫЕ МАРШРУТЫ
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Главная страница
    
    Логика:
    - Если пользователь уже вошёл → редирект в dashboard
    - Если не вошёл → показываем главную страницу
    """
    if request.session.get('user_id'):
        return RedirectResponse(url='/dashboard', status_code=302)
    
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


@app.get("/logout")
async def logout(request: Request):
    """
    Выход из системы
    Очищаем сессию и редиректим на главную
    """
    request.session.clear()
    return RedirectResponse(url='/', status_code=302)


@app.get("/set-language/{lang}")
async def set_language_route(request: Request, lang: str):
    """
    Смена языка интерфейса
    
    ✅ СМОТРИ КАК ЧИСТО! Никаких psycopg2!
    Просто используем готовую async функцию из db_postgresql.py
    """
    if lang in ['ru', 'uk', 'en', 'de']:
        request.session['language'] = lang
        
        # Если пользователь авторизован - сохраняем в БД
        user_id = request.session.get('user_id')
        if user_id:
            try:
                # ✅ ПРОСТО AWAIT! Используем готовую функцию!
                await update_user_profile(user_id, 'language', lang)
            except Exception as e:
                print("Ошибка сохранения языка")
    
    # Редиректим обратно на предыдущую страницу
    referer = request.headers.get('referer', '/')
    return RedirectResponse(url=referer, status_code=302)


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