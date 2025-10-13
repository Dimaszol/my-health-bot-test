# webapp/app.py
# 🌐 Главный файл Flask приложения для медицинского бота

import os
import sys
import asyncio
from flask import Flask, render_template, session, redirect, url_for
from flask_session import Session

# 📁 Добавляем корневую папку в путь (чтобы импортировать db_postgresql.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 🔧 Импортируем настройки
from webapp.config import Config, validate_config

# 🗄️ Импортируем функции базы данных
from db_postgresql import initialize_db_pool, close_db_pool

"""
🎯 ЧТО ДЕЛАЕТ ЭТО ПРИЛОЖЕНИЕ:

1. Запускает веб-сервер на http://localhost:5000
2. Позволяет пользователям входить через Google
3. Показывает личный кабинет с данными из PostgreSQL
4. Предоставляет чат с ИИ (используя gpt.py)
5. Позволяет загружать медицинские документы

ВСЕ данные берутся из той же БД, что использует Telegram бот!
"""

# 🏗️ СОЗДАЁМ FLASK ПРИЛОЖЕНИЕ
app = Flask(__name__)
app.config.from_object(Config)

# 📦 НАСТРОЙКА СЕССИЙ
# Сессии нужны чтобы запомнить кто вошёл в систему
app.config['SESSION_TYPE'] = 'filesystem'  # Храним сессии в файлах (не в памяти)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True  # Подписываем сессии (безопасность)
Session(app)

# 🌍 ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ для event loop
# Нужна для асинхронных функций (база данных работает асинхронно)
loop = None
db_initialized = False  # Флаг инициализации БД


# 🔄 ИНИЦИАЛИЗАЦИЯ БД при запуске приложения
async def init_database():
    """Инициализирует БД один раз при запуске"""
    global db_initialized
    
    if not db_initialized:
        await initialize_db_pool()
        print("✅ База данных подключена к Flask приложению")
        db_initialized = True


# 🔄 ПРОВЕРКА БД при запросе (не инициализация!)
@app.before_request
def check_db():
    """
    Проверяем БД перед запросом (но не инициализируем!)
    """
    global loop, db_initialized
    
    if loop is None:
        # Создаём event loop только один раз
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # БД уже должна быть инициализирована при старте приложения
    if not db_initialized:
        # Если вдруг не инициализирована - делаем это сейчас
        loop.run_until_complete(init_database())


# 🏠 ГЛАВНАЯ СТРАНИЦА
@app.route('/')
def index():
    """
    Показывает главную страницу
    
    Логика:
    - Если пользователь уже вошёл (есть session['user_id']) → редирект в dashboard
    - Если не вошёл → показываем главную страницу с кнопкой "Войти"
    """
    if 'user_id' in session:
        # Пользователь уже авторизован - отправляем в кабинет
        return redirect(url_for('dashboard.dashboard'))
    
    # Показываем главную страницу
    return render_template('index.html')


# 🔐 СТРАНИЦА ВХОДА
@app.route('/login')
def login():
    """
    Страница входа через Google OAuth
    
    Здесь будет кнопка "Войти через Google"
    """
    if 'user_id' in session:
        # Уже вошли - редирект в кабинет
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('login.html')


# 🚪 ВЫХОД
@app.route('/logout')
def logout():
    """
    Выход из системы
    
    Что делаем:
    1. Удаляем все данные из сессии
    2. Перенаправляем на главную страницу
    """
    session.clear()
    return redirect(url_for('index'))


# 📚 РЕГИСТРАЦИЯ МАРШРУТОВ (blueprints)
# Blueprints - это как модули, которые группируют связанные маршруты

try:
    from webapp.routes.auth import auth_bp, init_oauth
    from webapp.routes.dashboard import dashboard_bp
    from webapp.routes.api import api_bp
    
    # Инициализируем OAuth
    init_oauth(app)
    
    # Регистрируем маршруты
    app.register_blueprint(auth_bp, url_prefix='/auth')        # /auth/...
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')  # /dashboard/...
    app.register_blueprint(api_bp, url_prefix='/api')          # /api/...
    
    print("✅ Все маршруты зарегистрированы")
    
except ImportError as e:
    print(f"⚠️ Не удалось импортировать маршруты: {e}")
    print("Создайте файлы: routes/auth.py, routes/dashboard.py, routes/api.py")


# 🧹 ЗАКРЫТИЕ БД при остановке приложения (ПРАВИЛЬНО)
# Убрали teardown_appcontext - он закрывал пул после каждого запроса!
# Теперь пул будет закрыт только при остановке всего приложения

import atexit

@atexit.register
def cleanup():
    """
    Закрываем пул БД при завершении процесса Python
    Это вызовется только при реальной остановке приложения (Ctrl+C)
    """
    global loop
    if loop and not loop.is_closed():
        try:
            loop.run_until_complete(close_db_pool())
            print("🧹 База данных корректно закрыта")
        except:
            pass


# 🚀 ЗАПУСК ПРИЛОЖЕНИЯ
if __name__ == '__main__':
    # Проверяем настройки перед запуском
    if not validate_config():
        print("\n❌ Исправьте настройки в .env файле и попробуйте снова\n")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("🏥 МЕДИЦИНСКИЙ БОТ - ВЕБ ВЕРСИЯ")
    print("="*50)
    print(f"🌐 Открыть в браузере: http://localhost:5000")
    print(f"🔒 Безопасный режим: {'ON' if Config.DEBUG else 'OFF'}")
    print(f"📊 База данных: PostgreSQL (Supabase)")
    print("="*50 + "\n")
    
    # ✨ НОВОЕ: Инициализируем БД ПЕРЕД запуском сервера
    print("🔄 Инициализация базы данных...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_database())
    print("✅ База данных готова!\n")
    
    # Запускаем Flask сервер
    app.run(
        host='0.0.0.0',      # Слушаем на всех интерфейсах
        port=5000,           # Порт 5000
        debug=Config.DEBUG   # Режим отладки (из .env)
    )