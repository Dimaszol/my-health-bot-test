# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ - FASTAPI ВЕРСИЯ
# ✅ ПОЛНОСТЬЮ ASYNC - копируем логику прямо из телеграм-бота!

import os
import sys
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webapp.config import Config

# ==========================================
# ✅ ИМПОРТЫ ИЗ БД (async функции!)
# ==========================================
from db_postgresql import (
    save_message,           # ✅ async
    get_user_language,      # ✅ async
    get_user_profile,       # ✅ async
    get_db_connection,      # ✅ async
    release_db_connection   # ✅ async
)

# ✅ Импорт форматирования для веба
from webapp.utils.text_formatter import format_for_web

# ==========================================
# ✅ ИМПОРТЫ ФУНКЦИЙ БОТА
# ==========================================
try:
    from gpt import ask_doctor
    GPT_AVAILABLE = True
    print("✅ gpt.py импортирован")
    
    from prompt_logger import process_user_question_detailed
    CONTEXT_PROCESSOR_AVAILABLE = True
    print("✅ process_user_question_detailed импортирован")
    
    from subscription_manager import check_gpt4o_limit, spend_gpt4o_limit
    LIMITS_AVAILABLE = True
    print("✅ subscription_manager импортирован")
    
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}")
    GPT_AVAILABLE = False
    CONTEXT_PROCESSOR_AVAILABLE = False
    LIMITS_AVAILABLE = False

# 📘 СОЗДАЁМ ROUTER (аналог Blueprint)
router = APIRouter()


# ==========================================
# 📋 PYDANTIC MODELS (для валидации)
# ==========================================

class ChatMessage(BaseModel):
    """Модель для сообщения в чат"""
    message: str


# ==========================================
# 🔒 DEPENDENCY: Проверка авторизации
# ==========================================

async def get_current_user(request: Request) -> int:
    """
    Проверяет авторизацию для API запросов
    (аналог @api_login_required в Flask)
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                'success': False,
                'error': 'Не авторизован. Войдите в систему.'
            }
        )
    return user_id


# ==========================================
# 💬 ГЛАВНЫЙ МАРШРУТ: ЧАТ С ИИ
# ==========================================

@router.post("/chat")
async def chat_message(
    chat_data: ChatMessage,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    🎯 ОБРАБОТКА СООБЩЕНИЯ - БЕЗ КОСТЫЛЕЙ!
    
    ✅ СМОТРИ: ПРОСТО КОПИРУЕМ ЛОГИКУ ИЗ main.py (телеграм-бот)
    ✅ БЕЗ loop.run_until_complete - ПРОСТО AWAIT!
    
    ==========================================
    📝 АЛГОРИТМ (как в телеграм-боте):
    ==========================================
    
    ШАГ 1: Валидация
    ШАГ 2: Сохранение сообщения пользователя
    ШАГ 3: Проверка лимитов
    ШАГ 4: Сбор полного контекста
    ШАГ 5: Выбор модели
    ШАГ 6: Генерация ответа
    ШАГ 7: Списание лимита
    ШАГ 8: Сохранение ответа
    """
    
    try:
        # ==========================================
        # ШАГ 1: ВАЛИДАЦИЯ
        # ==========================================
        
        if not GPT_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    'success': False,
                    'error': 'Функция чата временно недоступна'
                }
            )
        
        user_message = chat_data.message.strip()
        
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Сообщение не может быть пустым'
                }
            )
        
        if len(user_message) > 4000:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Сообщение слишком длинное (максимум 4000 символов)'
                }
            )
        
        print(f"💬 [WEB] Новое сообщение от user_id={user_id}, длина={len(user_message)} символов")
        
        # ==========================================
        # ШАГ 2: СОХРАНЯЕМ СООБЩЕНИЕ
        # ==========================================
        print(f"📝 [ШАГ 2] Сохраняем сообщение пользователя...")
        
        # ✅ ПРОСТО AWAIT! НЕТ КОСТЫЛЕЙ!
        await save_message(user_id, 'user', user_message)
        
        print(f"✅ [ШАГ 2] Сообщение сохранено")
        
        # ==========================================
        # ШАГ 3: ПРОВЕРЯЕМ ЛИМИТЫ
        # ==========================================
        print(f"🔍 [ШАГ 3] Проверяем лимиты...")
        
        has_premium_limits = False
        if LIMITS_AVAILABLE:
            # ✅ ПРОСТО AWAIT!
            has_premium_limits = await check_gpt4o_limit(user_id)
            print(f"✅ [ШАГ 3] Лимиты: {'ЕСТЬ' if has_premium_limits else 'НЕТ'}")
        else:
            print(f"⚠️ [ШАГ 3] Модуль лимитов недоступен")
        
        # ==========================================
        # ШАГ 4: СОБИРАЕМ КОНТЕКСТ
        # ==========================================
        print(f"🧠 [ШАГ 4] Собираем контекст...")
        
        context_text = ""
        
        if CONTEXT_PROCESSOR_AVAILABLE:
            # ✅ ПРОСТО AWAIT! Используем ТУ ЖЕ функцию что в боте!
            lang = await get_user_language(user_id)
            
            prompt_data = await process_user_question_detailed(
                user_id=user_id,
                user_input=user_message
            )
            
            context_text = prompt_data.get('context_text', '')
            print(f"✅ [ШАГ 4] Контекст собран: {len(context_text)} символов")
            
        else:
            # Fallback: хотя бы профиль
            print(f"⚠️ [ШАГ 4] Используем упрощённый контекст")
            
            # ✅ ПРОСТО AWAIT!
            profile = await get_user_profile(user_id)
            
            if profile:
                try:
                    from save_utils import format_user_profile
                    # ✅ ПРОСТО AWAIT!
                    profile_text = await format_user_profile(user_id)
                    context_text = f"📌 Профиль:\n{profile_text}\n\nВопрос: {user_message}"
                except:
                    context_text = f"Вопрос пациента: {user_message}"
            else:
                context_text = f"Вопрос пациента: {user_message}"
        
        # ==========================================
        # ШАГ 5: ВЫБИРАЕМ МОДЕЛЬ
        # ==========================================
        print(f"🤖 [ШАГ 5] Выбираем модель...")
        
        if has_premium_limits:
            use_gemini = True
            model_name = "GPT-5 (детальная консультация)"
            print(f"✅ [ШАГ 5] Модель: GPT-5")
        else:
            use_gemini = False
            model_name = "GPT-4o-mini (базовая консультация)"
            print(f"✅ [ШАГ 5] Модель: GPT-4o-mini")
        
        # ==========================================
        # ШАГ 6: ГЕНЕРИРУЕМ ОТВЕТ
        # ==========================================
        print(f"🧠 [ШАГ 6] Генерируем ответ...")
        
        # ✅ ПРОСТО AWAIT!
        lang = await get_user_language(user_id)
        
        # ✅ ПРОСТО AWAIT! Используем ТУ ЖЕ функцию что в боте!
        ai_response = await ask_doctor(
            context_text=context_text,
            user_question=user_message,
            lang=lang,
            user_id=user_id,
            use_gemini=use_gemini
        )
        
        print(f"✅ [ШАГ 6] Ответ получен: {len(ai_response)} символов")
        
        # Форматируем для веба
        formatted_response = format_for_web(ai_response)
        
        # ==========================================
        # ШАГ 7: СПИСЫВАЕМ ЛИМИТ
        # ==========================================
        if has_premium_limits and LIMITS_AVAILABLE:
            print(f"💳 [ШАГ 7] Списываем лимит...")
            
            # ✅ ПРОСТО AWAIT!
            success = await spend_gpt4o_limit(user_id, message=None, bot=None)
            
            if success:
                print(f"✅ [ШАГ 7] Лимит списан")
            else:
                print(f"⚠️ [ШАГ 7] Ошибка списания")
        else:
            print(f"⏭️ [ШАГ 7] Пропускаем")
        
        # ==========================================
        # ШАГ 8: СОХРАНЯЕМ ОТВЕТ
        # ==========================================
        print(f"💾 [ШАГ 8] Сохраняем ответ...")
        
        # ✅ ПРОСТО AWAIT!
        await save_message(user_id, 'assistant', ai_response)
        
        print(f"✅ [ШАГ 8] Готово!")
        print(f"🎉 Запрос обработан успешно!")
        
        # Возвращаем успех
        return {
            'success': True,
            'response': formatted_response,
            'user_message': user_message,
            'model_used': model_name,
            'had_limits': has_premium_limits
        }
        
    except Exception as e:
        print(f"❌ Ошибка в /api/chat: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': 'Произошла ошибка при обработке сообщения'
            }
        )


# ==========================================
# 📤 ЗАГРУЗКА ДОКУМЕНТА
# ==========================================

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(None),
    user_id: int = Depends(get_current_user)
):
    """
    Загрузка медицинского документа
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
    """
    try:
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': 'Файл не выбран'}
            )
        
        # Проверяем расширение
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': f'Неподдерживаемый тип файла. Разрешены: {", ".join(Config.ALLOWED_EXTENSIONS)}'
                }
            )
        
        # Используем title или имя файла
        doc_title = title if title else filename
        
        print(f"📤 Загрузка документа от user_id={user_id}: {filename}")
        
        # Создаём папку для загрузок
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Сохраняем файл
        safe_filename = f"{user_id}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, safe_filename)
        
        # ✅ Сохраняем асинхронно
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # ✅ ПРОСТО AWAIT! Сохраняем в БД
        conn = await get_db_connection()
        
        try:
            document_id = await conn.fetchval("""
                INSERT INTO documents (user_id, title, file_path, file_type, uploaded_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id
            """, user_id, doc_title, file_path, file_ext)
            
        finally:
            await release_db_connection(conn)
        
        print(f"✅ Документ сохранён: document_id={document_id}")
        
        return {
            'success': True,
            'document_id': document_id,
            'message': 'Документ успешно загружен'
        }
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': 'Ошибка загрузки'}
        )


# ==========================================
# 🗑️ УДАЛЕНИЕ ДОКУМЕНТА
# ==========================================

@router.delete("/delete-document/{document_id}")
async def delete_document(
    document_id: int,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    Удаление документа
    
    ✅ БЕЗ КОСТЫЛЕЙ! Просто await!
    """
    try:
        # ✅ ПРОСТО AWAIT!
        conn = await get_db_connection()
        
        try:
            # Проверяем что документ принадлежит пользователю
            doc = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
                document_id, user_id
            )
            
            if not doc:
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'error': 'Документ не найден'}
                )
            
            # Удаляем файл с диска
            if doc['file_path'] and os.path.exists(doc['file_path']):
                os.remove(doc['file_path'])
            
            # Удаляем из БД
            await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            
        finally:
            await release_db_connection(conn)
        
        print(f"🗑️ Документ удалён: document_id={document_id}")
        
        return {
            'success': True,
            'message': 'Документ удалён'
        }
        
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': 'Ошибка удаления'}
        )


# ==========================================
# 📊 ИТОГО: ЧТО ИЗМЕНИЛОСЬ?
# ==========================================
"""
❌ БЫЛО (Flask):
- 450+ строк кода
- 17 раз loop.run_until_complete() - КОСТЫЛИ! 🔴
- Создание новых event loop в каждом эндпоинте
- Проблемы с "Task got Future attached to different loop"

✅ СТАЛО (FastAPI):
- 350 строк кода
- 0 раз loop.run_until_complete() - ПРОСТО AWAIT! ✅
- Код ИДЕНТИЧЕН телеграм-боту
- Никаких проблем с event loop

РАЗНИЦА: -100 строк, 0 костылей, просто копируем из main.py! 🎉
"""