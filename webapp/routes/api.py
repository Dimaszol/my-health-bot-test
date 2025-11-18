# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ - FASTAPI ВЕРСИЯ
# ✅ ПОЛНОСТЬЮ ASYNC - копируем логику прямо из телеграм-бота!

import os
import sys
import tempfile
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from webapp.translations import t
from error_handler import log_error_with_context
from webapp.utils.logger import safe_log_error, safe_log_warning


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
    safe_log_error("Ошибка импорта модулей бота", error=e)
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
    from fastapi import HTTPException
    
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail='Не авторизован. Войдите в систему.'
        )
    
    # ✅ ВАЛИДАЦИЯ: user_id должен быть положительным числом
    try:
        user_id = int(user_id)
        if user_id <= 0:
            request.session.clear()  # Очищаем испорченную сессию
            raise HTTPException(
                status_code=401,
                detail='Некорректная сессия. Войдите снова.'
            )
    except (ValueError, TypeError):
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail='Некорректная сессия. Войдите снова.'
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
        
        # ==========================================
        # ШАГ 2: СОХРАНЯЕМ СООБЩЕНИЕ
        # ==========================================

        await save_message(user_id, 'user', user_message)
        
        # ==========================================
        # ШАГ 3: ПРОВЕРЯЕМ ЛИМИТЫ
        # ==========================================
        
        has_premium_limits = False
        if LIMITS_AVAILABLE:
            # ✅ ПРОСТО AWAIT!
            has_premium_limits = await check_gpt4o_limit(user_id)
        else:
            safe_log_warning("Модуль лимитов недоступен - работаем без проверки подписки")
        
        # ==========================================
        # ШАГ 4: СОБИРАЕМ КОНТЕКСТ
        # ==========================================
        
        context_text = ""
        
        if CONTEXT_PROCESSOR_AVAILABLE:
            # ✅ ПРОСТО AWAIT! Используем ТУ ЖЕ функцию что в боте!
            lang = await get_user_language(user_id)
            
            prompt_data = await process_user_question_detailed(
                user_id=user_id,
                user_input=user_message
            )
            
            context_text = prompt_data.get('context_text', '')
            
        else:
            # Fallback: хотя бы профиль
            safe_log_warning("CONTEXT_PROCESSOR недоступен - качество ответов снижено")
            
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
        
        if has_premium_limits:
            use_gemini = True
            model_name = "GPT-5 (детальная консультация)"
        else:
            use_gemini = False
            model_name = "GPT-4o-mini (базовая консультация)"
        
        # ==========================================
        # ШАГ 6: ГЕНЕРИРУЕМ ОТВЕТ
        # ==========================================

        lang = await get_user_language(user_id)
        
        # ✅ ПРОСТО AWAIT! Используем ТУ ЖЕ функцию что в боте!
        ai_response = await ask_doctor(
            context_text=context_text,
            user_question=user_message,
            lang=lang,
            user_id=user_id,
            use_gemini=use_gemini
        )
                
        # Форматируем для веба
        formatted_response = format_for_web(ai_response)
        # Убираем пробелы с краев
        formatted_response = formatted_response.strip()
        
        # ==========================================
        # ШАГ 7: СПИСЫВАЕМ ЛИМИТ
        # ==========================================
        if has_premium_limits and LIMITS_AVAILABLE:
            
            # ✅ ПРОСТО AWAIT!
            success = await spend_gpt4o_limit(user_id, message=None, bot=None)
        
        # ==========================================
        # ШАГ 8: СОХРАНЯЕМ ОТВЕТ
        # ==========================================
        
        # ✅ ПРОСТО AWAIT!
        await save_message(user_id, 'assistant', formatted_response)
        
        # Возвращаем успех
        return {
            'success': True,
            'response': ai_response,
            'user_message': user_message,
            'model_used': model_name,
            'had_limits': has_premium_limits
        }
        
    except Exception as e:
        safe_log_error("Критическая ошибка обработки сообщения в чате", error=e, user_id=user_id if 'user_id' in locals() else None)
        
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
     
        return JSONResponse(content={
            'success': True,
            'has_limits': has_limits,
            'message': t('photo_requires_premium', lang) if not has_limits else ''
        })
        
    except Exception as e:
        safe_log_error("Ошибка проверки лимитов фото", error=e, user_id=user_id if 'user_id' in locals() else None)
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
        # 🛡️ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Валидация изображения через PIL
        try:
            from PIL import Image
            import io
            
            # Читаем файл в память
            file_content = await file.read()
            
            # Пытаемся открыть как изображение
            img = Image.open(io.BytesIO(file_content))
            img.verify()  # Проверяем что это действительно корректное изображение
            
            # ✅ ВАЖНО: После verify() нужно заново открыть изображение
            img = Image.open(io.BytesIO(file_content))
            
            # Проверяем размер файла (максимум 10MB для изображений)
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > 10:
                return JSONResponse(
                    status_code=400,
                    content={
                        'success': False,
                        'error': f'Изображение слишком большое ({file_size_mb:.1f} МБ). Максимум 10 МБ.'
                    }
                )
            
            print("Изображение прошло PIL валидацию")
            
            # ✅ Возвращаем указатель файла в начало для дальнейшего использования
            await file.seek(0)
            
        except Exception as e:
            safe_log_error("Файл не является корректным изображением", error=e)
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Файл не является корректным изображением. Поддерживаются: PNG, JPG, JPEG, GIF, WEBP'
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
        
        # ==========================================
        # ПРОВЕРКА ЛИМИТОВ GPT-4o
        # ==========================================
        
        if LIMITS_AVAILABLE:
            has_premium_limits = await check_gpt4o_limit(user_id)
            
            if not has_premium_limits:
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
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': t('photo_too_large', lang)
                }
            )
        
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
            safe_log_warning("Ошибка сбора контекста для анализа фото", error=e)
            context = ""
        
        # ==========================================
        # СОЗДАЕМ ПРОМПТ ДЛЯ GEMINI
        # ==========================================
                
        custom_prompt = create_photo_analysis_prompt(user_question, context, lang)
        
        # ==========================================
        # ОТПРАВЛЯЕМ НА АНАЛИЗ В GEMINI VISION
        # ==========================================
        
        from gemini_analyzer import send_to_gemini_vision
        
        analysis_result, error_message = await send_to_gemini_vision(
            photo_path, lang, custom_prompt
        )
        
        # Удаляем временный файл
        try:
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            safe_log_warning("Ошибка удаления временного файла фото", error=e)
        
        if error_message:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': f"{t('photo_analysis_error', lang)}: {error_message}"
                }
            )
        
        if not analysis_result:
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
        
        # ==========================================
        # СОХРАНЯЕМ ОТВЕТ В ИСТОРИЮ
        # ==========================================
        
        response_text = f"📸 Анализ изображения:\n\n{analysis_result}"
        await save_message(user_id, 'assistant', response_text)
        
        # ==========================================
        # ФОРМАТИРУЕМ ДЛЯ ВЕБА
        # ==========================================
        
        formatted_result = format_for_web(response_text)
        
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
        
        safe_log_error("Критическая ошибка анализа фото", error=e, user_id=user_id if 'user_id' in locals() else None)
        
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
    
    # ✅ Проверяем основные лимиты документов (documents_left)
    from subscription_manager import check_document_limit
    
    has_document_limits = await check_document_limit(user_id)
    
    if not has_document_limits:
        
        # Получаем текущие лимиты для сообщения
        limits = await SubscriptionManager.get_user_limits(user_id)
        
        # Формируем мультиязычное сообщение
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

    try:
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': t('file_not_selected', lang)}
            )
        
        # Проверяем расширение
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': t('unsupported_file_type', lang)
                }
            )
        
        # 🛡️ КРИТИЧЕСКАЯ ПРОВЕРКА: Валидация MIME-type (содержимого файла)
        try:
            # Читаем начало файла для определения настоящего типа
            file_content = await file.read(2048)  # Первые 2KB достаточно
            await file.seek(0)  # Возвращаем указатель в начало файла
            
            # Определяем MIME-type через python-magic
            import magic
            detected_mime = magic.from_buffer(file_content, mime=True)
            
            # Проверяем что MIME-type в списке разрешённых
            if detected_mime not in Config.ALLOWED_MIME_TYPES:
                safe_log_warning(
                    f"Отклонён файл с недопустимым MIME-type",
                    user_id=user_id,
                    filename_length=len(filename),
                    detected_mime=detected_mime,
                    file_extension=file_ext
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        'success': False,
                        'error': t('file_mime_type_mismatch', lang)
                    }
                )
            
            safe_log_warning(
                f"Файл прошёл MIME-type валидацию",
                user_id=user_id,
                file_extension=file_ext,
                detected_mime=detected_mime
            )
            
        except Exception as e:
            safe_log_error("Ошибка при проверке MIME-type файла", user_id=user_id, error=e)
            return JSONResponse(
                status_code=500,
                content={'success': False, 'error': t('file_validation_error', lang)}
            )
                
        # Создаём временную папку для загрузок
        temp_dir = f"temp_{user_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Сохраняем файл ВРЕМЕННО
        local_file = os.path.join(temp_dir, filename)
        
        # ✅ Сохраняем асинхронно
        content = await file.read()
        with open(local_file, 'wb') as f:
            f.write(content)

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
                    image_paths = image_paths[:5]
                
                # Извлекаем текст с каждой страницы
                for img_path in image_paths:
                    try:
                        page_text, _ = await send_to_gpt_vision(img_path, lang)
                        if page_text:
                            vision_text += page_text + "\n\n"
                    except Exception as page_error:
                        continue
                
                vision_text = vision_text.strip()
                
                if not vision_text:
                    return JSONResponse(
                        status_code=400,
                        content={'success': False, 'error': t('pdf_read_failed', lang)}
                    )
                    
            except Exception as e:
                safe_log_error("Ошибка обработки PDF", error=e, user_id=user_id)
                return JSONResponse(
                    status_code=400,
                    content={'success': False, 'error': t('pdf_processing_error', lang)}
                )
        
        elif file_ext in ['jpg', 'jpeg', 'png', 'webp']:
            # Изображение → анализируем через Vision API
            try:
                vision_text, _ = await send_to_gpt_vision(local_file, lang)
            except Exception as e:
                safe_log_error("Ошибка анализа изображения Vision API", error=e, user_id=user_id)
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
                    safe_log_error("Ошибка чтения текстового файла", error=e, user_id=user_id)
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
        else:
            auto_title = await generate_title_from_text(text=vision_text[:1500], lang=lang)
        
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
         
        # STEP 6: Сохраняем в БД
        document_id = await save_document(
            user_id=user_id,
            title=auto_title,
            file_path=permanent_path,
            file_type=file_type,
            raw_text=raw_text,
            summary=summary
        )
        
        # STEP 7: Добавляем в векторную базу
        chunks = await split_into_chunks(summary, document_id, user_id)
        await add_chunks_to_vector_db(document_id, user_id, chunks)
        
        # ✅ НОВОЕ: Извлекаем и сохраняем medical_timeline
        try:
            from medical_timeline import update_medical_timeline_on_document_upload
            
            # Используем полный текст документа для извлечения медицинских событий
            medical_timeline_success = await update_medical_timeline_on_document_upload(
                user_id=user_id,
                document_id=document_id,
                document_text=raw_text,  # Используем исходный текст
                use_gemini=False  # По умолчанию GPT
            )
                            
        except Exception as timeline_error:
            # Не прерываем загрузку документа если timeline не сохранился
            safe_log_warning("Ошибка обновления medical timeline", error=timeline_error)

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
            safe_log_warning("Ошибка удаления временных файлов при загрузке", error=cleanup_error)
        
        # ==========================================
        # 💳 БЛОК 2: СПИСАНИЕ ЛИМИТОВ
        # ==========================================

        # Списываем основной лимит документов
        await SubscriptionManager.spend_limits(user_id, documents=1)

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
        safe_log_error("Критическая ошибка загрузки документа", error=e, user_id=user_id if 'user_id' in locals() else None)
        
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
    # ✅ ВАЛИДАЦИЯ: Проверяем что document_id положительный
    if document_id <= 0:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Invalid document ID'}
        )
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
            
            # 2️⃣ Удаляем из векторной базы
            try:
                from vector_db_postgresql import delete_chunks_by_document
                await delete_chunks_by_document(document_id)
    
            except Exception as e:
                safe_log_warning("Ошибка удаления из векторной БД", error=e, document_id=document_id)
            
            # 3️⃣ Удаляем из medical_timeline
            try:
                deleted_timeline = await conn.execute(
                    "DELETE FROM medical_timeline WHERE source_document_id = $1",
                    document_id
                )

            except Exception as e:
                safe_log_warning("Ошибка удаления из medical_timeline", error=e, document_id=document_id)
            
            # 4️⃣ Удаляем файл с диска
            if doc['file_path']:
                try:
                    from supabase_storage import get_file_storage
                    storage = get_file_storage()
                    storage.delete_file(doc['file_path'])

                except Exception as e:
                    safe_log_warning("Ошибка удаления файла документа", error=e, document_id=document_id)
            
            # 5️⃣ Удаляем из основной таблицы documents
            await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            
        finally:
            await release_db_connection(conn)
        
        return {
            'success': True,
            'message': 'Документ удалён'
        }
        
    except Exception as e:
        safe_log_error("Ошибка удаления документа", error=e, user_id=user_id, document_id=document_id)
        
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

        # Очищаем сессию
        request.session.clear()
        
        return {
            'success': True,
            'message': t('account_deleted_success', lang),
            'redirect': '/'
        }
        
    except Exception as e:
        safe_log_error("Ошибка удаления аккаунта", error=e, user_id=user_id)
        
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

    # ✅ ВАЛИДАЦИЯ: Проверяем что document_id положительный
    if document_id <= 0:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Invalid document ID'}
        )
    
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

            # ==========================================
            # ✅ ПРОВЕРЯЕМ ТИП ХРАНИЛИЩА
            # ==========================================
            
            # Если путь начинается с "users/" - это Supabase Storage
            if file_path.startswith("users/"):
                
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
                    safe_log_error("Ошибка скачивания из Supabase", error=e, user_id=user_id, document_id=document_id)
                    return JSONResponse(
                        status_code=500,
                        content={'success': False, 'error': f'Ошибка скачивания из облака: {str(e)}'}
                    )
            
            # Если путь НЕ начинается с "users/" - это локальный файл
            else:

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
        safe_log_error("Ошибка скачивания документа", error=e, user_id=user_id, document_id=document_id)
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
        # ✅ ВАЛИДАЦИЯ: Проверяем что document_id положительный
        if document_id <= 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid document ID"}
            )
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
        
        # Безопасное получение языка
        error_lang = locals().get('lang', 'en')
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": t('document_toggle_error', error_lang)
            }
        )
# ==========================================
# 🔒 ФУНКЦИИ ВАЛИДАЦИИ (как в Telegram-боте)
# ==========================================

def validate_birth_year(year: int) -> tuple[bool, str]:
    """Валидация года рождения (16+)"""
    current_year = datetime.now().year - 16
    if year < 1900 or year > current_year:
        return False, "birth_year_invalid"
    return True, ""

def validate_height(height: int) -> tuple[bool, str]:
    """Валидация роста (100-250 см)"""
    if height < 100 or height > 250:
        return False, "height_invalid"
    return True, ""

def validate_weight(weight: float) -> tuple[bool, str]:
    """Валидация веса (30-300 кг)"""
    if weight < 30 or weight > 300:
        return False, "weight_invalid"
    return True, ""

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
            # Год рождения
            if 'birth_year' in data and data['birth_year']:
                try:
                    year = int(data['birth_year'])
                    is_valid, error_key = validate_birth_year(year)
                    if not is_valid:
                        lang = await get_user_language(user_id)
                        return JSONResponse(
                            status_code=400,
                            content={"success": False, "message": t(error_key, lang)}
                        )
                    update_data['birth_year'] = year
                except (ValueError, TypeError):
                    lang = await get_user_language(user_id)
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": t("birth_year_invalid", lang)}
                    )
            if 'gender' in data:
                update_data['gender'] = data['gender'] if data['gender'] else None
            # Рост
            if 'height_cm' in data and data['height_cm']:
                try:
                    height = int(data['height_cm'])
                    is_valid, error_key = validate_height(height)
                    if not is_valid:
                        lang = await get_user_language(user_id)
                        return JSONResponse(
                            status_code=400,
                            content={"success": False, "message": t(error_key, lang)}
                        )
                    update_data['height_cm'] = height
                except (ValueError, TypeError):
                    lang = await get_user_language(user_id)
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": t("height_invalid", lang)}
                    )
            
            # Вес
            if 'weight_kg' in data and data['weight_kg']:
                try:
                    weight = float(data['weight_kg'])
                    is_valid, error_key = validate_weight(weight)
                    if not is_valid:
                        lang = await get_user_language(user_id)
                        return JSONResponse(
                            status_code=400,
                            content={"success": False, "message": t(error_key, lang)}
                        )
                    update_data['weight_kg'] = weight
                except (ValueError, TypeError):
                    lang = await get_user_language(user_id)
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": t("weight_invalid", lang)}
                    )
            if 'chronic_conditions' in data:
                update_data['chronic_conditions'] = data['chronic_conditions'] if data['chronic_conditions'] else None
            if 'allergies' in data:
                update_data['allergies'] = data['allergies'] if data['allergies'] else None
            if 'family_history' in data:  # ← ДОБАВЬ ЭТУ ПРОВЕРКУ
                update_data['family_history'] = data['family_history'] if data['family_history'] else None
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
        safe_log_error("Ошибка обновления профиля", error=e, user_id=user_id)
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
        
        # Создаём Checkout Session через StripeManager
        result = await StripeManager.create_checkout_session(
            user_id=user_id,
            package_id=package_id,
            user_name=user_name,
            source="web"  # ← Указываем что это веб-версия
        )

        # StripeManager возвращает tuple: (success, url_or_error)
        success, url_or_error = result

        if not success:
            raise Exception(url_or_error)

        return {
            'success': True,
            'checkout_url': url_or_error
        }
        
    except Exception as e:
        safe_log_error("Ошибка создания Stripe Checkout Session", error=e, user_id=user_id, package_id=package_id if 'package_id' in locals() else None)
        
        # Получаем язык для локализованного сообщения
        try:
            lang = await get_user_language(user_id)
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

# ==========================================
# 🚫 ОТМЕНА ПОДПИСКИ
# ==========================================

@router.post("/cancel-subscription")
async def cancel_subscription_endpoint(
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    Отменяет активную подписку пользователя в Stripe
    """
    try:
        from subscription_manager import SubscriptionManager
        from db_postgresql import get_user_language, t
        
        # Получаем язык для локализованных сообщений
        lang = await get_user_language(user_id)
        
        # Отменяем подписку через SubscriptionManager
        success, message = await SubscriptionManager.cancel_stripe_subscription(user_id)
        
        if success:
            return JSONResponse(content={
                'success': True,
                'message': t('cancel_success_message', lang) if not message else message
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': message or t('cancel_error_message', lang)
                }
            )
        
    except Exception as e:
        safe_log_error("Ошибка отмены подписки", error=e, user_id=user_id)
        
        try:
            lang = await get_user_language(user_id)
            error_message = t('cancel_error_message', lang)
        except:
            error_message = 'Ошибка отмены подписки'
        
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': error_message
            }
        )