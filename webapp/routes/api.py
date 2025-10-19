# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ - ПОЛНЫЙ ФУНКЦИОНАЛ КАК В ТЕЛЕГРАМ-БОТЕ
# ✅ ВСЕ ИМПОРТЫ ПРОВЕРЕНЫ И СООТВЕТСТВУЮТ БОТУ

import os
import sys
import asyncio
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webapp.config import Config

# ==========================================
# ✅ ИМПОРТЫ ИЗ БД (проверены в db_postgresql.py)
# ==========================================
from db_postgresql import (
    save_message,           # Сохранение сообщений в chat_history
    get_user_language,      # Получение языка пользователя
    get_user_profile,       # Получение профиля пользователя
    get_db_connection,      # Подключение к БД
    release_db_connection   # Освобождение подключения
)

# ==========================================
# ✅ ИМПОРТЫ ФУНКЦИЙ БОТА (проверены)
# ==========================================
try:
    # ✅ 1. Основная функция для работы с ИИ (из gpt.py)
    from gpt import ask_doctor
    GPT_AVAILABLE = True
    print("✅ gpt.py импортирован")
    
    # ✅ 2. Функция сбора контекста (из prompt_logger.py)
    from prompt_logger import process_user_question_detailed
    CONTEXT_PROCESSOR_AVAILABLE = True
    print("✅ process_user_question_detailed импортирован")
    
    # ✅ 3. Функции проверки и списания лимитов (из subscription_manager.py)
    from subscription_manager import check_gpt4o_limit, spend_gpt4o_limit
    LIMITS_AVAILABLE = True
    print("✅ subscription_manager импортирован")
    
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}")
    GPT_AVAILABLE = False
    CONTEXT_PROCESSOR_AVAILABLE = False
    LIMITS_AVAILABLE = False

# 📘 СОЗДАЁМ BLUEPRINT
api_bp = Blueprint('api', __name__)


# 🔒 ДЕКОРАТОР: Проверка авторизации
def api_login_required(f):
    """Проверяет что пользователь авторизован"""
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


# ==========================================
# 💬 ГЛАВНЫЙ МАРШРУТ: ЧАТ С ИИ
# ==========================================
@api_bp.route('/chat', methods=['POST'])
@api_login_required
def chat_message():
    """
    🎯 ОБРАБОТКА СООБЩЕНИЯ - ПОЛНЫЙ ФУНКЦИОНАЛ КАК В ТЕЛЕГРАМ-БОТЕ
    
    Принимает JSON: {"message": "У меня болит голова"}
    Возвращает JSON: {"success": true, "response": "...", "model_used": "GPT-5"}
    
    ==========================================
    📝 ПОШАГОВЫЙ АЛГОРИТМ (точно как в main.py):
    ==========================================
    
    ШАГ 1: Валидация и подготовка
    ШАГ 2: Сохранение сообщения пользователя
    ШАГ 3: Проверка лимитов (есть ли детальные консультации?)
    ШАГ 4: Сбор ПОЛНОГО контекста через process_user_question_detailed
    ШАГ 5: Выбор модели (GPT-5 или GPT-4o-mini)
    ШАГ 6: Генерация ответа через ask_doctor
    ШАГ 7: Списание лимита (если использовали GPT-5)
    ШАГ 8: Сохранение ответа и возврат пользователю
    """
    
    try:
        # ==========================================
        # ШАГ 1: ВАЛИДАЦИЯ И ПОДГОТОВКА
        # ==========================================
        
        # Проверяем что все функции доступны
        if not GPT_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Функция чата временно недоступна'
            }), 503
        
        # Получаем данные из запроса
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        # Валидация сообщения
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Сообщение не может быть пустым'
            }), 400
        
        if len(user_message) > 4000:
            return jsonify({
                'success': False,
                'error': 'Сообщение слишком длинное (максимум 4000 символов)'
            }), 400
        
        user_id = session.get('user_id')
        
        # Логируем (БЕЗ персональных данных - только user_id!)
        print(f"💬 [WEB] Новое сообщение от user_id={user_id}, длина={len(user_message)} символов")
        
        # ==========================================
        # 🔧 НАСТРОЙКА EVENT LOOP (для async функций)
        # ==========================================
        from flask import current_app
        loop = current_app.extensions.get('loop')
        
        if not loop:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        # ==========================================
        # ШАГ 2: СОХРАНЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
        # ==========================================
        print(f"📝 [ШАГ 2] Сохраняем сообщение пользователя...")
        
        loop.run_until_complete(
            save_message(user_id, 'user', user_message)
        )
        
        print(f"✅ [ШАГ 2] Сообщение сохранено в chat_history")
        
        # ==========================================
        # ШАГ 3: ПРОВЕРЯЕМ ЛИМИТЫ (как в боте!)
        # ==========================================
        print(f"🔍 [ШАГ 3] Проверяем лимиты детальных консультаций...")
        
        has_premium_limits = False
        if LIMITS_AVAILABLE:
            has_premium_limits = loop.run_until_complete(
                check_gpt4o_limit(user_id)
            )
            print(f"✅ [ШАГ 3] Лимиты проверены: {'ЕСТЬ детальные консультации' if has_premium_limits else 'НЕТ детальных консультаций'}")
        else:
            print(f"⚠️ [ШАГ 3] Модуль лимитов недоступен, используем базовую модель")
        
        # ==========================================
        # ШАГ 4: СОБИРАЕМ ПОЛНЫЙ КОНТЕКСТ
        # ==========================================
        print(f"🧠 [ШАГ 4] Собираем полный контекст через process_user_question_detailed...")
        
        context_text = ""
        
        if CONTEXT_PROCESSOR_AVAILABLE:
            # 🎯 ЭТО КЛЮЧЕВОЙ МОМЕНТ!
            # Используем ТУ ЖЕ функцию что и в телеграм-боте
            # Она соберёт: профиль + документы + историю + сводку + заметки
            
            lang = loop.run_until_complete(get_user_language(user_id))
            
            prompt_data = loop.run_until_complete(
                process_user_question_detailed(
                    user_id=user_id,
                    user_input=user_message
                )
            )
            
            # prompt_data содержит:
            # - context_text: полный контекст (всё что нужно ИИ)
            # - profile_text: профиль
            # - summary_text: сводка разговоров
            # - chunks_text: релевантные документы
            # - medical_timeline: медицинская карта
            # и т.д.
            
            context_text = prompt_data.get('context_text', '')
            print(f"✅ [ШАГ 4] Контекст собран: {len(context_text)} символов")
            print(f"📊 [ШАГ 4] Детали: профиль={len(prompt_data.get('profile_text', ''))}, документы={prompt_data.get('chunks_found', 0)} чанков")
            
        else:
            # Fallback: если функция недоступна, собираем хотя бы профиль
            print(f"⚠️ [ШАГ 4] process_user_question_detailed недоступен, используем упрощённый контекст")
            
            profile = loop.run_until_complete(get_user_profile(user_id))
            
            if profile:
                # Формируем базовый контекст из профиля
                from save_utils import format_user_profile
                profile_text = loop.run_until_complete(format_user_profile(user_id))
                context_text = f"📌 Профиль пациента:\n{profile_text}\n\nВопрос пациента: {user_message}"
            else:
                context_text = f"📌 Профиль пациента: не заполнен\n\nВопрос пациента: {user_message}"
        
        # ==========================================
        # ШАГ 5: ВЫБИРАЕМ МОДЕЛЬ (как в боте!)
        # ==========================================
        print(f"🤖 [ШАГ 5] Выбираем модель ИИ...")
        
        if has_premium_limits:
            use_gemini = True  # GPT-5 (детальные ответы)
            model_name = "GPT-5 (детальная консультация)"
            print(f"✅ [ШАГ 5] Выбрана модель: GPT-5 (у пользователя есть лимиты)")
        else:
            use_gemini = False  # GPT-4o-mini (базовые ответы)
            model_name = "GPT-4o-mini (базовая консультация)"
            print(f"✅ [ШАГ 5] Выбрана модель: GPT-4o-mini (нет лимитов)")
        
        # ==========================================
        # ШАГ 6: ГЕНЕРИРУЕМ ОТВЕТ (как в боте!)
        # ==========================================
        print(f"🧠 [ШАГ 6] Генерируем ответ через ask_doctor...")
        
        # Получаем язык пользователя
        lang = loop.run_until_complete(get_user_language(user_id))
        
        # 🎯 ВЫЗЫВАЕМ ask_doctor С ПОЛНЫМ КОНТЕКСТОМ
        # Точно так же как в main.py!
        ai_response = loop.run_until_complete(
            ask_doctor(
                context_text=context_text,      # Полный контекст
                user_question=user_message,     # Вопрос пользователя
                lang=lang,                      # Язык
                user_id=user_id,                # ID пользователя
                use_gemini=use_gemini          # Какую модель использовать
            )
        )
        
        print(f"✅ [ШАГ 6] Ответ получен: {len(ai_response)} символов")
        
        # ==========================================
        # ШАГ 7: СПИСЫВАЕМ ЛИМИТ (если использовали GPT-5)
        # ==========================================
        if has_premium_limits and LIMITS_AVAILABLE:
            print(f"💳 [ШАГ 7] Списываем 1 детальную консультацию...")
            
            # ✅ Используем правильную функцию из subscription_manager
            # spend_gpt4o_limit принимает: user_id, message, bot
            # Для веб-версии message и bot будут None
            success = loop.run_until_complete(
                spend_gpt4o_limit(user_id, message=None, bot=None)
            )
            
            if success:
                print(f"✅ [ШАГ 7] Лимит списан успешно")
            else:
                print(f"⚠️ [ШАГ 7] Ошибка списания лимита (но ответ уже сгенерирован)")
        else:
            print(f"⏭️ [ШАГ 7] Пропускаем (не использовали детальную модель)")
        
        # ==========================================
        # ШАГ 8: СОХРАНЯЕМ ОТВЕТ И ВОЗВРАЩАЕМ
        # ==========================================
        print(f"💾 [ШАГ 8] Сохраняем ответ ИИ...")
        
        loop.run_until_complete(
            save_message(user_id, 'assistant', ai_response)
        )
        
        print(f"✅ [ШАГ 8] Ответ сохранён в chat_history")
        print(f"🎉 Запрос обработан успешно!")
        
        # Возвращаем успешный ответ
        return jsonify({
            'success': True,
            'response': ai_response,
            'user_message': user_message,
            'model_used': model_name,  # Показываем какая модель использовалась
            'had_limits': has_premium_limits  # Были ли лимиты
        })
        
    except Exception as e:
        # ==========================================
        # ❌ ОБРАБОТКА ОШИБОК
        # ==========================================
        print(f"❌ Ошибка в /api/chat: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при обработке сообщения'
        }), 500


# ==========================================
# 📤 ЗАГРУЗКА ДОКУМЕНТА
# ==========================================
@api_bp.route('/upload', methods=['POST'])
@api_login_required
def upload_document():
    """Загрузка медицинского документа (пока упрощённая версия)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
        
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
        
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(Config.UPLOAD_FOLDER, f"{user_id}_{filename}")
        file.save(file_path)
        
        # Сохраняем в БД (упрощённо)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        conn = loop.run_until_complete(get_db_connection())
        
        document_id = loop.run_until_complete(
            conn.fetchval("""
                INSERT INTO documents (user_id, title, file_path, file_type, uploaded_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, user_id, title, file_path, file_ext)
        )
        
        loop.run_until_complete(release_db_connection(conn))
        
        print(f"✅ Документ сохранён: document_id={document_id}")
        
        return jsonify({
            'success': True,
            'document_id': document_id,
            'message': 'Документ успешно загружен'
        })
        
    except Exception as e:
        print(f"❌ Ошибка загрузки документа: {e}")
        return jsonify({'success': False, 'error': 'Ошибка загрузки'}), 500


# ==========================================
# 🗑️ УДАЛЕНИЕ ДОКУМЕНТА
# ==========================================
@api_bp.route('/delete-document/<int:document_id>', methods=['DELETE'])
@api_login_required
def delete_document(document_id):
    """Удаление документа"""
    try:
        user_id = session.get('user_id')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        conn = loop.run_until_complete(get_db_connection())
        
        doc = loop.run_until_complete(
            conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
                document_id, user_id
            )
        )
        
        if not doc:
            loop.run_until_complete(release_db_connection(conn))
            return jsonify({'success': False, 'error': 'Документ не найден'}), 404
        
        if doc['file_path'] and os.path.exists(doc['file_path']):
            os.remove(doc['file_path'])
        
        loop.run_until_complete(
            conn.execute("DELETE FROM documents WHERE id = $1", document_id)
        )
        
        loop.run_until_complete(release_db_connection(conn))
        
        print(f"🗑️ Документ удалён: document_id={document_id}")
        
        return jsonify({'success': True, 'message': 'Документ удалён'})
        
    except Exception as e:
        print(f"❌ Ошибка удаления документа: {e}")
        return jsonify({'success': False, 'error': 'Ошибка удаления'}), 500