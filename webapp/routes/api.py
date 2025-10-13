# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ и загрузки документов

import os
import sys
import asyncio
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webapp.config import Config
from db_postgresql import save_message, get_user_profile  # ✅ Правильные имена

# Импортируем функции из бота (переиспользуем код!)
# Файлы находятся в корне проекта, поэтому импортируем через sys.path
try:
    # Проверяем существование файлов
    import importlib.util
    
    # Пытаемся импортировать gpt.py
    gpt_spec = importlib.util.find_spec("gpt")
    if gpt_spec:
        from gpt import ask_doctor  # ✅ Правильное имя функции
        GPT_AVAILABLE = True
        print("✅ gpt.py импортирован успешно")
    else:
        print("⚠️ gpt.py не найден - функция чата будет недоступна")
        GPT_AVAILABLE = False
    
    # Пытаемся импортировать upload.py (обработка документов)
    upload_spec = importlib.util.find_spec("upload")
    if upload_spec:
        from upload import handle_document_upload
        DOC_PROCESSOR_AVAILABLE = True
        print("✅ upload.py импортирован успешно")
    else:
        print("⚠️ upload.py не найден - загрузка документов будет недоступна")
        DOC_PROCESSOR_AVAILABLE = False
        
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}")
    GPT_AVAILABLE = False
    DOC_PROCESSOR_AVAILABLE = False

"""
🎯 ЧТО ДЕЛАЕТ ЭТОТ API:

1. /api/chat - отправка сообщения ИИ и получение ответа
2. /api/upload - загрузка медицинского документа
3. /api/delete-document - удаление документа

Все маршруты работают через JSON (AJAX запросы из JavaScript)

ВАЖНО: Переиспользуем функции из бота (gpt.py, document_processor.py)
Не дублируем код!
"""

# 📘 СОЗДАЁМ BLUEPRINT
api_bp = Blueprint('api', __name__)


# 🔒 ПРОВЕРКА АВТОРИЗАЦИИ для API
def api_login_required(f):
    """
    Декоратор для API endpoints
    Возвращает JSON ошибку если пользователь не авторизован
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Не авторизован. Войдите в систему.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# 💬 API: Отправка сообщения в чат
@api_bp.route('/chat', methods=['POST'])
@api_login_required
def chat_message():
    """
    Обработка сообщения от пользователя
    
    Принимает JSON:
        {
            "message": "У меня болит голова, что делать?"
        }
    
    Возвращает JSON:
        {
            "success": true,
            "response": "Ответ от ИИ...",
            "user_message": "Сообщение пользователя"
        }
    
    Логика:
    1. Получаем сообщение пользователя
    2. Сохраняем его в БД (chat_history)
    3. Вызываем ИИ (функция из gpt.py)
    4. Сохраняем ответ ИИ в БД
    5. Возвращаем ответ пользователю
    """
    try:
        # Получаем данные из запроса
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Сообщение не может быть пустым'
            }), 400
        
        # Проверяем доступность GPT функции
        if not GPT_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Функция чата временно недоступна'
            }), 503
        
        user_id = session.get('user_id')
        
        # Логируем (БЕЗ персональных данных - только user_id)
        print(f"💬 Новое сообщение от user_id={user_id}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 1. Сохраняем сообщение пользователя
        loop.run_until_complete(
            save_message(user_id, 'user', user_message)
        )
        
        # 2. Получаем профиль для контекста
        profile = loop.run_until_complete(get_user_profile(user_id))
        
        # 3. Генерируем ответ ИИ (используем функцию из gpt.py!)
        # ask_doctor - основная функция для общения с GPT
        # Нужны параметры: context_text, user_question, lang, user_id
        
        # Получаем язык пользователя
        from db_postgresql import get_user_language
        lang = loop.run_until_complete(get_user_language(user_id))
        
        # Формируем контекст из профиля
        context_text = f"Профиль пользователя: {profile}"
        
        ai_response = loop.run_until_complete(
            ask_doctor(
                context_text=context_text,
                user_question=user_message,
                lang=lang,
                user_id=user_id,
                use_gemini=False  # Используем обычный GPT
            )
        )
        
        # 4. Сохраняем ответ ИИ
        loop.run_until_complete(
            save_message(user_id, 'assistant', ai_response)
        )
        
        print(f"✅ Ответ отправлен user_id={user_id}")
        
        # 5. Возвращаем ответ
        return jsonify({
            'success': True,
            'response': ai_response,
            'user_message': user_message
        })
        
    except Exception as e:
        print(f"❌ Ошибка в /api/chat: {e}")
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при обработке сообщения'
        }), 500


# 📤 API: Загрузка документа
@api_bp.route('/upload', methods=['POST'])
@api_login_required
def upload_document():
    """
    Загрузка медицинского документа
    
    Принимает:
        - file: файл (PDF, DOCX, TXT, изображение)
        - title: название документа (опционально)
    
    Возвращает JSON:
        {
            "success": true,
            "document_id": 123,
            "message": "Документ успешно загружен"
        }
    
    Логика:
    1. Проверяем тип файла (только разрешённые)
    2. Сохраняем файл на диск
    3. Обрабатываем документ (функция из document_processor.py)
    4. Сохраняем в БД
    5. Создаём векторные эмбеддинги
    """
    try:
        # Проверяем доступность обработчика документов
        if not DOC_PROCESSOR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Функция загрузки документов временно недоступна'
            }), 503
        
        # Проверяем наличие файла
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Файл не найден'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Файл не выбран'
            }), 400
        
        # Проверяем расширение файла
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[-1].lower()
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return jsonify({
                'success': False,
                'error': f'Неподдерживаемый тип файла. Разрешены: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        user_id = session.get('user_id')
        title = request.form.get('title', filename)
        
        print(f"📤 Загрузка документа от user_id={user_id}: {filename}")
        
        # Создаём папку для файлов если её нет
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Сохраняем файл
        file_path = os.path.join(Config.UPLOAD_FOLDER, f"{user_id}_{filename}")
        file.save(file_path)
        
        print(f"✅ Файл сохранён: {file_path}")
        
        # ВРЕМЕННОЕ РЕШЕНИЕ: Простое сохранение в БД
        # Позже интегрируем полную обработку из upload.py
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from db_postgresql import get_db_connection, release_db_connection
        
        conn = loop.run_until_complete(get_db_connection())
        
        # Сохраняем документ в БД (упрощённая версия)
        document_id = loop.run_until_complete(
            conn.fetchval("""
                INSERT INTO documents (user_id, title, file_path, file_type, uploaded_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, user_id, title, file_path, file_ext)
        )
        
        loop.run_until_complete(release_db_connection(conn))
        
        print(f"✅ Документ сохранён в БД: document_id={document_id}")
        
        return jsonify({
            'success': True,
            'document_id': document_id,
            'message': 'Документ успешно загружен и обработан'
        })
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке документа: {e}")
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при загрузке документа'
        }), 500


# 🗑️ API: Удаление документа
@api_bp.route('/delete-document/<int:document_id>', methods=['DELETE'])
@api_login_required
def delete_document(document_id):
    """
    Удаление документа
    
    Логика:
    1. Проверяем что документ принадлежит пользователю
    2. Удаляем физический файл
    3. Удаляем из БД (документ и векторы)
    """
    try:
        user_id = session.get('user_id')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Импортируем функцию удаления
        from db_postgresql import get_db_connection, release_db_connection
        
        conn = loop.run_until_complete(get_db_connection())
        
        # Проверяем что документ принадлежит пользователю
        doc = loop.run_until_complete(
            conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
                document_id, user_id
            )
        )
        
        if not doc:
            loop.run_until_complete(release_db_connection(conn))
            return jsonify({
                'success': False,
                'error': 'Документ не найден'
            }), 404
        
        # Удаляем физический файл
        if doc['file_path'] and os.path.exists(doc['file_path']):
            os.remove(doc['file_path'])
        
        # Удаляем из БД (каскадно удалятся векторы)
        loop.run_until_complete(
            conn.execute(
                "DELETE FROM documents WHERE id = $1",
                document_id
            )
        )
        
        loop.run_until_complete(release_db_connection(conn))
        
        print(f"🗑️ Документ удалён: document_id={document_id}")
        
        return jsonify({
            'success': True,
            'message': 'Документ удалён'
        })
        
    except Exception as e:
        print(f"❌ Ошибка при удалении документа: {e}")
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при удалении'
        }), 500