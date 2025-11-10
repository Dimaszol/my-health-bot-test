# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ - FASTAPI ВЕРСИЯ
# ✅ ПОЛНОСТЬЮ ASYNC - копируем логику прямо из телеграм-бота!

import os
import sys
import tempfile
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from webapp.translations import t
from error_handler import log_error_with_context


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
    
    from subscription_manager import check_gpt4o_limit, spend_gpt4o_limit, SubscriptionManager
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

class CheckoutRequest(BaseModel):
    """Модель для запроса создания Stripe Checkout"""
    package_id: str

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
        # Убираем пробелы с краев
        formatted_response = formatted_response.strip()
        
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
        await save_message(user_id, 'assistant', formatted_response)
        
        print(f"✅ [ШАГ 8] Готово!")
        print(f"🎉 Запрос обработан успешно!")
        
        # Возвращаем успех
        return {
            'success': True,
            'response': ai_response,
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
# 🔒 ПРОВЕРКА ЛИМИТОВ ДЛЯ ФОТО
# ==========================================

@router.get("/check-photo-limits")
async def check_photo_limits(
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    Проверяет есть ли у пользователя доступ к анализу фото
    (нужны лимиты GPT-4o для детальных консультаций)
    """
    try:
        lang = await get_user_language(user_id)
        
        if not LIMITS_AVAILABLE:
            return JSONResponse(content={
                'success': False,
                'has_limits': False,
                'message': 'Функция временно недоступна'
            })
        
        # Проверяем лимиты GPT-4o
        has_limits = await check_gpt4o_limit(user_id)
        
        from db_postgresql import t
        
        return JSONResponse(content={
            'success': True,
            'has_limits': has_limits,
            'message': t('photo_requires_premium', lang) if not has_limits else ''
        })
        
    except Exception as e:
        print(f"❌ Ошибка проверки лимитов: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'has_limits': False,
                'message': 'Ошибка проверки лимитов'
            }
        )


# ==========================================
# 📸 ЗАГРУЗКА И АНАЛИЗ ФОТО (один endpoint)
# ==========================================

# Создаем промпт прямо здесь (без зависимости от photo_analyzer)
def create_photo_analysis_prompt(user_question: str, context: str, lang: str) -> str:
    """Создает промпт для анализа фото"""
    
    lang_names = {
        'ru': 'Russian',
        'en': 'English', 
        'uk': 'Ukrainian',
        'de': 'German'
    }
    response_language = lang_names.get(lang, 'English')
    
    return f"""You are a medical AI assistant analyzing a medical image.

USER QUESTION: "{user_question}"

USER CONTEXT:
{context}

INSTRUCTIONS:
1. Analyze the image in the context of the user's specific question
2. Consider the provided user information when giving recommendations  
3. Give a comprehensive but understandable answer
4. If this appears to be a medical condition, suggest whether medical consultation is needed
5. Be supportive and informative, but avoid definitive diagnoses
6. Always respond in {response_language} language

Focus your analysis specifically on answering the user's question while considering their medical context."""

@router.post("/analyze-photo")
async def analyze_photo_with_question(
    request: Request,
    file: UploadFile = File(...),
    question: str = Form(...),
    user_id: int = Depends(get_current_user)
):
    """
    📸 Загрузка фото + анализ с вопросом пользователя
    
    Объединяем загрузку и анализ в один endpoint для простоты
    
    Процесс (как в телеграм-боте):
    1. Валидация файла (размер, тип)
    2. Проверка лимитов GPT-4o
    3. Сохранение файла временно
    4. Сбор контекста пользователя
    5. Отправка в Gemini Vision API
    6. Списание лимита
    7. Возврат результата
    """
    
    photo_path = None
    
    try:
        lang = await get_user_language(user_id)
        
        # ==========================================
        # ВАЛИДАЦИЯ ФАЙЛА
        # ==========================================
        
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Пожалуйста, загрузите изображение (PNG, JPG, JPEG, GIF, WEBP)'
                }
            )
        
        # Проверяем вопрос
        user_question = question.strip()
        if not user_question:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Пожалуйста, задайте вопрос к изображению'
                }
            )
        
        print(f"📸 [WEB] Загрузка фото от user_id={user_id}")
        print(f"❓ Вопрос: {user_question}")
        
        # ==========================================
        # ПРОВЕРКА ЛИМИТОВ GPT-4o
        # ==========================================
        
        if LIMITS_AVAILABLE:
            has_premium_limits = await check_gpt4o_limit(user_id)
            
            if not has_premium_limits:
                from db_postgresql import t
                return JSONResponse(
                    status_code=403,
                    content={
                        'success': False,
                        'error': t('gpt4o_limit_exceeded', lang),
                        'show_subscription': True
                    }
                )
        
        # ==========================================
        # СОХРАНЕНИЕ ФАЙЛА ВРЕМЕННО
        # ==========================================
        
        from file_utils import create_simple_file_path, validate_file_size
        
        try:
            # Создаем временный путь
            photo_path = create_simple_file_path(user_id, f"temp_photo_{uuid.uuid4().hex[:8]}.jpg")
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': str(e)}
            )
        
        # Сохраняем файл
        with open(photo_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Проверяем размер (максимум 5 МБ)
        if not validate_file_size(photo_path):
            os.remove(photo_path)
            from db_postgresql import t
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': t('photo_too_large', lang)
                }
            )
        
        print(f"✅ Фото сохранено: {photo_path}")
        
        # ==========================================
        # СОХРАНЯЕМ ВОПРОС В ИСТОРИЮ
        # ==========================================
        
        await save_message(user_id, 'user', f"📷 {user_question}")
        
        # ==========================================
        # СОБИРАЕМ КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ
        # ==========================================
        
        try:
            from save_utils import format_user_profile
            from db_postgresql import get_last_messages
            
            profile_text = await format_user_profile(user_id)
            last_messages = await get_last_messages(user_id, limit=5)
            
            # Формируем историю
            history_text = ""
            if last_messages:
                history_text = "\n\nПоследние сообщения:\n"
                for msg in last_messages:
                    # msg это tuple: (role, message, timestamp)
                    role_label = "Пользователь" if msg[0] == 'user' else "Ассистент"
                    history_text += f"{role_label}: {msg[1][:200]}\n"

            context = f"{profile_text}\n{history_text}".strip()
            
        except Exception as e:
            print(f"⚠️ Ошибка сбора контекста: {e}")
            context = ""
        
        # ==========================================
        # СОЗДАЕМ ПРОМПТ ДЛЯ GEMINI
        # ==========================================
                
        custom_prompt = create_photo_analysis_prompt(user_question, context, lang)
        
        # ==========================================
        # ОТПРАВЛЯЕМ НА АНАЛИЗ В GEMINI VISION
        # ==========================================
        
        print(f"🔬 Отправляем на анализ в Gemini Vision...")
        
        from gemini_analyzer import send_to_gemini_vision
        
        analysis_result, error_message = await send_to_gemini_vision(
            photo_path, lang, custom_prompt
        )
        
        # Удаляем временный файл
        try:
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
                print(f"🗑️ Временный файл удален")
        except Exception as e:
            print(f"⚠️ Ошибка удаления файла: {e}")
        
        if error_message:
            from db_postgresql import t
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': f"{t('photo_analysis_error', lang)}: {error_message}"
                }
            )
        
        if not analysis_result:
            from db_postgresql import t
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': t('photo_analysis_failed', lang)
                }
            )
        
        # ==========================================
        # СПИСЫВАЕМ ЛИМИТ GPT-4o
        # ==========================================
        
        if LIMITS_AVAILABLE:
            await spend_gpt4o_limit(user_id, None, None)
            print(f"💎 Лимит потрачен для user {user_id} (анализ фото)")
        
        # ==========================================
        # СОХРАНЯЕМ ОТВЕТ В ИСТОРИЮ
        # ==========================================
        
        response_text = f"📸 Анализ изображения:\n\n{analysis_result}"
        await save_message(user_id, 'assistant', response_text)
        
        # ==========================================
        # ФОРМАТИРУЕМ ДЛЯ ВЕБА
        # ==========================================
        
        formatted_result = format_for_web(response_text)
        
        print(f"✅ Анализ фото завершен успешно")
        
        return JSONResponse(content={
            'success': True,
            'response': formatted_result
        })
        
    except Exception as e:
        # Удаляем файл в случае ошибки
        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except:
                pass
        
        print(f"❌ Ошибка анализа фото: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': 'Ошибка анализа изображения. Попробуйте снова.'
            }
        )

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(None),
    user_id: int = Depends(get_current_user)
):
    """
    📤 ЗАГРУЗКА И ОБРАБОТКА ДОКУМЕНТА (ВАРИАНТ 1 - мультиязычный)
    
    Копируем логику из upload.py (Telegram бота)
    """
    
    # ✅ СНАЧАЛА получаем язык пользователя
    lang = await get_user_language(user_id)
    
    # ==========================================
    # 🔒 БЛОК 1: ПРОВЕРКА ОСНОВНЫХ ЛИМИТОВ
    # ==========================================
    
    print(f"🔍 Проверяем основные лимиты документов...")
    
    # ✅ Проверяем основные лимиты документов (documents_left)
    from subscription_manager import check_document_limit
    
    has_document_limits = await check_document_limit(user_id)
    
    if not has_document_limits:
        print(f"❌ Лимит документов исчерпан (documents_left = 0)")
        
        # Получаем текущие лимиты для сообщения
        limits = await SubscriptionManager.get_user_limits(user_id)
        
        # Формируем мультиязычное сообщение
        from db_postgresql import t
        error_message = t("document_limit_exceeded", lang,
                         documents_left=limits['documents_left'],
                         gpt4o_queries_left=limits['gpt4o_queries_left'])
        
        return JSONResponse(
            status_code=403,  # 403 = Forbidden (нет лимитов)
            content={
                'success': False,
                'error': error_message
            }
        )
    
    print(f"✅ Лимиты проверены - можно загружать")
    
    try:
        if not file.filename:
            from db_postgresql import t
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': t('file_not_selected', lang)}
            )
        
        # Проверяем расширение
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            from db_postgresql import t
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': t('unsupported_file_type', lang)
                }
            )
        
        print(f"📤 Загрузка документа от user_id={user_id}: {filename}")
        
        # Создаём временную папку для загрузок
        temp_dir = f"temp_{user_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Сохраняем файл ВРЕМЕННО
        local_file = os.path.join(temp_dir, filename)
        
        # ✅ Сохраняем асинхронно
        content = await file.read()
        with open(local_file, 'wb') as f:
            f.write(content)
        
        print(f"✅ Файл сохранён временно: {local_file}")
        
        # ===================================================
        # 🔧 КОПИРУЕМ ЛОГИКУ ИЗ upload.py (TELEGRAM БОТА)
        # ===================================================
        
        # Импортируем функции из бота
        from save_utils import send_to_gpt_vision, convert_pdf_to_images
        from gpt import (
            ask_structured, 
            is_medical_text, 
            generate_medical_summary, 
            generate_title_from_text
        )
        from db_postgresql import save_document, t
        from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
        from file_storage import get_file_storage
        
        file_type = "pdf" if file_ext == "pdf" else "image"
        vision_text = ""
        
        # STEP 1: Извлекаем текст в зависимости от типа файла
        if file_ext == 'pdf':
            try:
                image_paths = convert_pdf_to_images(local_file, f"{temp_dir}/pages")
                
                if not image_paths:
                    return JSONResponse(
                        status_code=400,
                        content={'success': False, 'error': t('pdf_read_failed', lang)}
                    )
                
                # Ограничиваем до 5 страниц
                if len(image_paths) > 5:
                    print(f"⚠️ PDF содержит {len(image_paths)} страниц, обрабатываем первые 5")
                    image_paths = image_paths[:5]
                
                # Извлекаем текст с каждой страницы
                for img_path in image_paths:
                    try:
                        page_text, _ = await send_to_gpt_vision(img_path, lang)
                        if page_text:
                            vision_text += page_text + "\n\n"
                    except Exception as page_error:
                        print(f"⚠️ Ошибка обработки страницы: {page_error}")
                        continue
                
                vision_text = vision_text.strip()
                
                if not vision_text:
                    return JSONResponse(
                        status_code=400,
                        content={'success': False, 'error': t('pdf_read_failed', lang)}
                    )
                    
            except Exception as e:
                print(f"❌ Ошибка обработки PDF: {e}")
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=400,
                    content={'success': False, 'error': t('pdf_processing_error', lang)}
                )
        
        elif file_ext in ['jpg', 'jpeg', 'png', 'webp']:
            # Изображение → анализируем через Vision API
            try:
                vision_text, _ = await send_to_gpt_vision(local_file, lang)
            except Exception as e:
                print(f"❌ Ошибка анализа изображения: {e}")
                return JSONResponse(
                    status_code=400,
                    content={'success': False, 'error': t('image_analysis_error', lang)}
                )
        
        else:
            # Текстовый файл → читаем напрямую
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    vision_text = f.read()
            except UnicodeDecodeError:
                try:
                    with open(local_file, 'r', encoding='cp1251') as f:
                        vision_text = f.read()
                except Exception as e:
                    print(f"❌ Ошибка чтения файла: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={'success': False, 'error': t('file_read_error', lang)}
                    )
        
        # STEP 2: Проверяем что это медицинский документ
        if not await is_medical_text(vision_text):
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': t('not_medical_doc', lang)}
            )
        
        # STEP 3: Генерируем заголовок
        if title and title.strip():
            auto_title = title.strip()
            print(f"✅ Используем название от пользователя: {auto_title}")
        else:
            auto_title = await generate_title_from_text(text=vision_text[:1500], lang=lang)
            print(f"🤖 Сгенерирован заголовок: {auto_title}")
        
        # STEP 4: Создаём структурированный текст и резюме
        raw_text = await ask_structured(vision_text[:8000], lang=lang)
        summary = await generate_medical_summary(vision_text[:8000], lang)
        
        # STEP 5: Сохраняем файл в постоянное хранилище
        storage = get_file_storage()
        success, permanent_path = storage.save_file(
            user_id=user_id,
            filename=filename,
            source_path=local_file
        )
        
        if not success:
            return JSONResponse(
                status_code=500,
                content={'success': False, 'error': t('file_storage_error', lang)}
            )
        
        print(f"✅ Файл сохранён постоянно: {permanent_path}")
        
        # STEP 6: Сохраняем в БД
        document_id = await save_document(
            user_id=user_id,
            title=auto_title,
            file_path=permanent_path,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary
        )
        
        print(f"✅ Документ сохранён в БД: document_id={document_id}")
        
        # STEP 7: Добавляем в векторную базу
        chunks = await split_into_chunks(summary, document_id, user_id)
        await add_chunks_to_vector_db(document_id, user_id, chunks)
        
        print(f"✅ Документ добавлен в векторную базу")
        
        # ✅ НОВОЕ: Извлекаем и сохраняем medical_timeline
        print(f"🏥 Извлекаем medical timeline...")
        try:
            from medical_timeline import update_medical_timeline_on_document_upload
            
            # Используем полный текст документа для извлечения медицинских событий
            medical_timeline_success = await update_medical_timeline_on_document_upload(
                user_id=user_id,
                document_id=document_id,
                document_text=raw_text,  # Используем исходный текст
                use_gemini=False  # По умолчанию GPT
            )
            
            if medical_timeline_success:
                print(f"✅ Medical timeline обновлён успешно!")
            else:
                print(f"⚠️ Medical timeline не обновлён (возможно нет важных данных)")
                
        except Exception as timeline_error:
            # Не прерываем загрузку документа если timeline не сохранился
            print(f"⚠️ Ошибка обновления medical timeline: {timeline_error}")
            import traceback
            traceback.print_exc()

        # STEP 8: Удаляем временные файлы
        try:
            if os.path.exists(local_file):
                os.remove(local_file)
            pages_dir = f"{temp_dir}/pages"
            if os.path.exists(pages_dir):
                import shutil
                shutil.rmtree(pages_dir)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception as cleanup_error:
            print(f"⚠️ Не удалось удалить временные файлы: {cleanup_error}")
        
        print(f"🎉 Документ успешно обработан!")
        
        # ==========================================
        # 💳 БЛОК 2: СПИСАНИЕ ЛИМИТОВ
        # ==========================================
        
        print(f"💳 Списываем основной лимит документов...")
        
        # Списываем основной лимит документов
        await SubscriptionManager.spend_limits(user_id, documents=1)
        print(f"✅ Основной лимит документов списан")
        
        print(f"🎉 Лимит успешно списан!")
        
        # ✅ Возвращаем успех
        return {
            'success': True,
            'document_id': document_id,
            'title': auto_title,
            'summary': summary[:200] + '...' if len(summary) > 200 else summary,
            'message': t('document_uploaded_successfully', lang, title=auto_title)
        }
    
    # ❌ ЕДИНСТВЕННЫЙ except для всех ошибок
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()
        
        # Пытаемся удалить временные файлы даже при ошибке
        try:
            if 'local_file' in locals() and os.path.exists(local_file):
                os.remove(local_file)
            if 'temp_dir' in locals():
                pages_dir = f"{temp_dir}/pages"
                if os.path.exists(pages_dir):
                    import shutil
                    shutil.rmtree(pages_dir)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        except:
            pass  # Игнорируем ошибки очистки
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': t('document_processing_error', lang) if 'lang' in locals() else 'Error processing document'
            }
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
    🗑️ Удаление документа
    
    Удаляет документ из ВСЕХ связанных таблиц:
    - documents
    - document_vectors (векторная БД)
    - medical_timeline (медицинская карта)
    - файл с диска
    """
    try:
        conn = await get_db_connection()
        
        try:
            # 1️⃣ Проверяем что документ принадлежит пользователю
            doc = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
                document_id, user_id
            )
            
            if not doc:
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'error': 'Документ не найден'}
                )
            
            print(f"🗑️ Начинаем удаление документа document_id={document_id}")
            
            # 2️⃣ Удаляем из векторной базы
            try:
                from vector_db_postgresql import delete_chunks_by_document
                await delete_chunks_by_document(document_id)
                print(f"✅ Удалено из векторной БД")
            except Exception as e:
                print(f"⚠️ Ошибка удаления из векторной БД: {e}")
            
            # 3️⃣ Удаляем из medical_timeline
            try:
                deleted_timeline = await conn.execute(
                    "DELETE FROM medical_timeline WHERE source_document_id = $1",
                    document_id
                )
                print(f"✅ Удалено из medical_timeline: {deleted_timeline}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления из medical_timeline: {e}")
            
            # 4️⃣ Удаляем файл с диска
            if doc['file_path']:
                try:
                    from supabase_storage import get_file_storage
                    storage = get_file_storage()
                    storage.delete_file(doc['file_path'])
                    print(f"✅ Файл удалён с диска")
                except Exception as e:
                    print(f"⚠️ Ошибка удаления файла: {e}")
            
            # 5️⃣ Удаляем из основной таблицы documents
            await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            print(f"✅ Удалено из таблицы documents")
            
        finally:
            await release_db_connection(conn)
        
        print(f"🎉 Документ полностью удалён: document_id={document_id}")
        
        return {
            'success': True,
            'message': 'Документ удалён'
        }
        
    except Exception as e:
        print(f"❌ Ошибка удаления документа: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': 'Ошибка удаления'}
        )

# ==========================================
# 🗑️ УДАЛЕНИЕ АККАУНТА (GDPR)
# ==========================================

@router.post("/delete-account")
async def delete_account_route(
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    🗑️ Полное удаление аккаунта пользователя (GDPR-compliant)
    
    Удаляет:
    - Все документы и файлы
    - Подписки Stripe
    - Историю чата
    - Медицинские данные
    - Garmin данные
    - Векторы
    - Профиль пользователя
    """
    try:
        lang = request.session.get('lang', 'ru')
        
        print(f"🗑️ Начинаем удаление аккаунта user_id={user_id}")
        
        # Вызываем функцию полного удаления из db_postgresql.py
        from db_postgresql import delete_user_gdpr_compliant
        success = await delete_user_gdpr_compliant(user_id)
        
        if not success:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': t('account_deletion_error', lang)
                }
            )
        
        print(f"✅ Аккаунт успешно удалён: user_id={user_id}")
        
        # Очищаем сессию
        request.session.clear()
        
        return {
            'success': True,
            'message': t('account_deleted_success', lang),
            'redirect': '/'
        }
        
    except Exception as e:
        print(f"❌ Ошибка удаления аккаунта: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': t('account_deletion_error', lang) if 'lang' in locals() else 'Error deleting account'
            }
        )
        
# ==========================================
# 🗑️ СКАЧИВАНИЕ ДОКУМЕНТА
# ==========================================

@router.get("/download-document/{document_id}")
async def download_document(
    document_id: int,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    📥 Скачивание документа
    
    ✅ Использует существующий метод download_file из supabase_storage.py
    """
    from fastapi.responses import FileResponse
    import tempfile
    
    try:
        conn = await get_db_connection()
        
        try:
            # 🔐 БЕЗОПАСНОСТЬ: Проверяем что документ принадлежит пользователю
            doc = await conn.fetchrow(
                "SELECT * FROM documents WHERE id = $1 AND user_id = $2",
                document_id, user_id
            )
            
            if not doc:
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'error': 'Документ не найден'}
                )
            
            file_path = doc['file_path']
            
            if not file_path:
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'error': 'Путь к файлу не указан в БД'}
                )
            
            # Получаем оригинальное имя файла
            original_filename = doc['title']
            if not original_filename.endswith(('.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png')):
                ext = os.path.splitext(file_path)[1]
                original_filename = f"{original_filename}{ext}"
            
            print(f"📥 Скачивание документа: document_id={document_id}, file={original_filename}")
            print(f"📁 Путь в БД: {file_path}")
            
            # ==========================================
            # ✅ ПРОВЕРЯЕМ ТИП ХРАНИЛИЩА
            # ==========================================
            
            # Если путь начинается с "users/" - это Supabase Storage
            if file_path.startswith("users/"):
                print(f"☁️ Файл в Supabase Storage")
                
                # Скачиваем из Supabase во временный файл
                from supabase_storage import get_storage_manager
                storage = get_storage_manager()
                
                # Создаём временный файл
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1])
                temp_path = temp_file.name
                temp_file.close()
                
                try:
                    # ✅ ИСПОЛЬЗУЕМ СУЩЕСТВУЮЩИЙ МЕТОД download_file
                    success = await storage.download_file(
                        storage_path=file_path,
                        local_path=temp_path
                    )
                    
                    if not success:
                        # Удаляем временный файл
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return JSONResponse(
                            status_code=404,
                            content={'success': False, 'error': 'Файл не найден в Supabase Storage'}
                        )
                    
                    print(f"✅ Файл скачан из Supabase во временный файл")
                    
                    # Возвращаем файл и удаляем его после отправки
                    return FileResponse(
                        path=temp_path,
                        filename=original_filename,
                        media_type='application/octet-stream',
                        background=None  # Файл будет удален автоматически
                    )
                    
                except Exception as e:
                    # Удаляем временный файл при ошибке
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"❌ Ошибка скачивания из Supabase: {e}")
                    import traceback
                    traceback.print_exc()
                    return JSONResponse(
                        status_code=500,
                        content={'success': False, 'error': f'Ошибка скачивания из облака: {str(e)}'}
                    )
            
            # Если путь НЕ начинается с "users/" - это локальный файл
            else:
                print(f"💾 Файл локальный")
                
                # Проверяем что файл существует
                if not os.path.exists(file_path):
                    return JSONResponse(
                        status_code=404,
                        content={'success': False, 'error': 'Файл не найден на сервере'}
                    )
                
                # Возвращаем локальный файл
                return FileResponse(
                    path=file_path,
                    filename=original_filename,
                    media_type='application/octet-stream'
                )
            
        finally:
            await release_db_connection(conn)
        
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': 'Ошибка скачивания файла'}
        )

@router.post("/toggle-document-confirmed/{document_id}")
async def toggle_document_confirmed(
    document_id: int,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    Переключает статус confirmed для документа
    """
    from db_postgresql import get_document_by_id, update_document_confirmed, get_user_language
    from error_handler import log_error_with_context
    
    try:
        # Получаем язык пользователя
        lang = await get_user_language(user_id)
        
        # Проверяем что документ принадлежит пользователю
        document = await get_document_by_id(document_id)
        
        if not document or document['user_id'] != user_id:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Access denied"}
            )
        
        # Получаем новое значение из тела запроса
        body = await request.json()
        new_confirmed = body.get("confirmed", True)
        
        # Обновляем статус в БД
        success = await update_document_confirmed(document_id, new_confirmed)
        
        if success:
            # Определяем сообщение в зависимости от статуса
            if new_confirmed:
                message = t("document_confirmed_enabled", lang)
            else:
                message = t("document_confirmed_disabled", lang)
            
            return JSONResponse(content={
                "success": True,
                "message": message,
                "confirmed": new_confirmed
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Database error"}
            )
            
    except Exception as e:
        log_error_with_context(e, {"function": "toggle_document_confirmed", "document_id": document_id})
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
# ==========================================
# 💳 РЕДАКТИРОВАНИЕ ПРОФАЙЛА
# ==========================================

@router.post("/profile/update")
async def update_profile(request: Request):
    """
    API для обновления профиля пользователя
    
    Принимает JSON с полем 'section' и соответствующими данными:
    - basic: name
    - medical: birth_year, gender, height_cm, weight_kg, chronic_conditions, allergies, medications
    - lifestyle: smoking, alcohol, physical_activity
    """
    try:
        # Проверяем авторизацию
        user_id = request.session.get('user_id')
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Не авторизован"}
            )
        
        # Получаем данные из запроса
        data = await request.json()
        section = data.get('section')
        
        if not section:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Не указана секция"}
            )
        
        # Импортируем функцию обновления
        from db_postgresql import update_user_profile_dict
        
        # Подготавливаем данные для обновления в зависимости от секции
        update_data = {}
        
        if section == 'basic':
            if 'name' in data:
                update_data['name'] = data['name']
        
        elif section == 'medical':
            if 'birth_year' in data and data['birth_year']:
                update_data['birth_year'] = int(data['birth_year'])
            if 'gender' in data:
                update_data['gender'] = data['gender'] if data['gender'] else None
            if 'height_cm' in data and data['height_cm']:
                update_data['height_cm'] = int(data['height_cm'])
            if 'weight_kg' in data and data['weight_kg']:
                update_data['weight_kg'] = float(data['weight_kg'])
            if 'chronic_conditions' in data:
                update_data['chronic_conditions'] = data['chronic_conditions'] if data['chronic_conditions'] else None
            if 'allergies' in data:
                update_data['allergies'] = data['allergies'] if data['allergies'] else None
            if 'medications' in data:
                update_data['medications'] = data['medications'] if data['medications'] else None
        
        elif section == 'lifestyle':
            if 'smoking' in data:
                update_data['smoking'] = data['smoking'] if data['smoking'] else None
            if 'alcohol' in data:
                update_data['alcohol'] = data['alcohol'] if data['alcohol'] else None
            if 'physical_activity' in data:
                update_data['physical_activity'] = data['physical_activity'] if data['physical_activity'] else None
        
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Неизвестная секция"}
            )
        
        # Обновляем данные в базе
        success = await update_user_profile_dict(user_id, update_data)
        
        if success:
            return JSONResponse(
                content={"success": True, "message": "Профиль обновлен"}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Ошибка обновления"}
            )
    
    except Exception as e:
        print(f"❌ Ошибка обновления профиля: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Внутренняя ошибка сервера"}
        )

# ==========================================
# 💳 STRIPE CHECKOUT - СОЗДАНИЕ СЕССИИ ОПЛАТЫ
# ==========================================

class CheckoutRequest(BaseModel):
    """Модель для запроса создания Stripe Checkout"""
    package_id: str

@router.post("/create-checkout")
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    💳 Создание Stripe Checkout Session для оплаты подписки
    
    Процесс:
    1. Проверяем существование пакета
    2. Получаем данные пользователя
    3. Создаём Stripe Checkout Session
    4. Возвращаем URL для оплаты
    """
    try:
        from stripe_manager import StripeManager
        from stripe_config import StripeConfig
        
        package_id = checkout_data.package_id
        
        # Проверяем существование пакета
        package_info = StripeConfig.get_package_info(package_id)
        if not package_info:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Неверный ID пакета'
                }
            )
        
        # Получаем данные пользователя
        lang = await get_user_language(user_id)
        user_profile = await get_user_profile(user_id)
        user_name = user_profile.get('name', 'User')
        
        print(f"💳 Создаём Stripe Checkout для пользователя {user_id}")
        print(f"   Пакет: {package_id}")
        print(f"   Имя: {user_name}")
        
        # Создаём Checkout Session через StripeManager
        session_url = await StripeManager.create_checkout_session(
            user_id=user_id,
            package_id=package_id,
            user_name=user_name
        )
        
        if not session_url:
            raise Exception("Не удалось создать Checkout Session")
        
        print(f"✅ Checkout Session создана: {session_url[:50]}...")
        
        return {
            'success': True,
            'checkout_url': session_url
        }
        
    except Exception as e:
        print(f"❌ Ошибка создания Checkout Session: {e}")
        import traceback
        traceback.print_exc()
        
        # Получаем язык для локализованного сообщения
        try:
            lang = await get_user_language(user_id)
            from db_postgresql import t
            error_message = t('stripe_session_creation_error', lang)
        except:
            error_message = 'Ошибка создания сессии оплаты'
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': error_message
            }
        )