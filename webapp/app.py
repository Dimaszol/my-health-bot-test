# webapp/app.py
# 🌐 Главный файл FastAPI приложения для медицинского бота
# ✅ ПОЛНОСТЬЮ АСИНХРОННЫЙ - без костылей с loop!

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

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
        print(f"❌ Ошибка подключения к БД: {e}")
        raise
    
    print(f"📊 База данных: PostgreSQL (Supabase)")
    print(f"🌍 Поддержка языков: RU, UK, EN, DE")
    print(f"⚡ Режим: Асинхронный (FastAPI)")
    print("="*50 + "\n")
    
    # ✅ yield = приложение работает здесь
    yield
    
    # ==========================================
    # 🛑 SHUTDOWN (выполняется при остановке)
    # ==========================================
    print("\n🧹 Закрытие базы данных...")
    try:
        await close_db_pool()
        print("✅ База данных корректно закрыта")
    except Exception as e:
        print(f"⚠️ Ошибка при закрытии БД: {e}")

# 🏗️ СОЗДАЁМ FASTAPI ПРИЛОЖЕНИЕ
app = FastAPI(
    title="Медицинский Бот - Веб Версия",
    description="Асинхронный веб-интерфейс для медицинского бота",
    version="2.0.0",
    lifespan=lifespan
)

# 🔐 ДОБАВЛЯЕМ ПОДДЕРЖКУ СЕССИЙ (как в Flask)
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

# 📁 НАСТРОЙКА ШАБЛОНОВ И СТАТИКИ
# Используем те же папки что были в Flask
templates = Jinja2Templates(directory="webapp/templates")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
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
        print(f"🌍 Язык изменён на: {lang}")
        
        # Если пользователь авторизован - сохраняем в БД
        user_id = request.session.get('user_id')
        if user_id:
            try:
                # ✅ ПРОСТО AWAIT! Используем готовую функцию!
                await update_user_profile(user_id, 'language', lang)
                print(f"✅ Язык сохранён в БД для user_id={user_id}")
            except Exception as e:
                print(f"⚠️ Ошибка сохранения языка: {e}")
    
    # Редиректим обратно на предыдущую страницу
    referer = request.headers.get('referer', '/')
    return RedirectResponse(url=referer, status_code=302)


# ==========================================
# 📚 РЕГИСТРАЦИЯ РОУТЕРОВ (Blueprints в FastAPI)
# ==========================================

try:
    from webapp.routes import auth, dashboard, api
    
    # Регистрируем роутеры (как blueprints в Flask)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(api.router, prefix="/api", tags=["api"])
    
    print("✅ Все роутеры зарегистрированы")
    
except ImportError as e:
    print(f"⚠️ Роутеры будут добавлены следующим шагом: {e}")


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
            "error": str(e)
        }


# ==========================================
# 🚀 ЗАПУСК (для локальной разработки)
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # Проверяем настройки
    if not validate_config():
        print("\n❌ Исправьте настройки в .env файле и попробуйте снова\n")
        sys.exit(1)
    
    # ✅ ЧИТАЕМ DEBUG из .env
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print("\n🚀 Запуск FastAPI сервера...")
    print(f"🐛 Режим отладки: {'ON (автоперезагрузка)' if debug_mode else 'OFF'}")
    
    # Запускаем сервер на том же порту что был Flask (5000)
    uvicorn.run(
        "webapp.app:app",
        host="0.0.0.0",
        port=5000,
        reload=debug_mode,  # ← ИЗМЕНИЛИ! Теперь берётся из .env
        log_level="info"
    )