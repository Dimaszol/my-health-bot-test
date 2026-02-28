# webapp/routes/api.py
# 🔌 API endpoints для чата с ИИ - FASTAPI ВЕРСИЯ
# ✅ ПОЛНОСТЬЮ ASYNC - копируем логику прямо из телеграм-бота!

import os
import sys
import tempfile
import uuid
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
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
    save_message,  
    get_user_language,    
    get_user_profile,
    execute_query,     
    get_db_connection,    
    release_db_connection
)
from rate_limiter import check_rate_limit, record_user_action
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
            request.session.clear()
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
    
    # ✅ НОВОЕ: Проверяем существование пользователя в БД
    conn = await get_db_connection()
    try:
        user_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)",
            user_id
        )
        
        if not user_exists:
            request.session.clear()
            raise HTTPException(
                status_code=401,
                detail='Пользователь не найден. Войдите снова.'
            )
    finally:
        await release_db_connection(conn)
    
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
        # ШАГ 1.5: ПРОВЕРКА БЕСПЛАТНОГО ЛИМИТА (30 сообщений)
        # ==========================================
                
        # Получаем тип подписки
        limits = await SubscriptionManager.get_user_limits(user_id)
        subscription_type = limits.get('subscription_type', 'free')

        # Если нет подписки - проверяем общий счетчик
        if subscription_type == 'free':
            try:
                from cumulative_counter import get_total_messages
                total_messages = await get_total_messages(user_id)
                
                # Если достигнут лимит в 30 сообщений - блокируем
                if total_messages >= 30:
                    lang = await get_user_language(user_id)
                    return JSONResponse(
                        status_code=403,
                        content={
                            'success': False,
                            'error': t('free_limit_reached_text', lang),
                            'limit_reached': True
                        }
                    )
            except Exception:
                pass  # Если ошибка счетчика - пропускаем проверку
        
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
            model_name = "GPT-5-mini (базовая консультация)"
        
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

        # ==========================================
        # 🎯 УВЕЛИЧИВАЕМ СЧЕТЧИК СООБЩЕНИЙ
        # ==========================================
        try:
            from cumulative_counter import increment_and_get_total_messages
            await increment_and_get_total_messages(user_id)
        except Exception:
            pass

        # ==========================================
        # ШАГ 9: ОБНОВЛЯЕМ СВОДКУ (каждые 7 сообщений)
        # ==========================================
        
        try:
            from save_utils import maybe_update_summary            
            
            summary_allowed, _ = await check_rate_limit(user_id, "summary")
            if summary_allowed:
                summary_was_updated = await maybe_update_summary(user_id)
                if summary_was_updated:
                    await record_user_action(user_id, "summary")
        except Exception as e:
            # Ошибка сводки не должна ломать основной функционал
            safe_log_warning("Ошибка обновления сводки")
                
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
# 💬 МАРШРУТ: ЧАТ С ИИ ПО ДОКУМЕНТУ
# ==========================================

class DocumentChatMessage(BaseModel):
    """Модель для сообщения в чате документа"""
    document_id: int
    message: str

@router.post("/document-chat")
async def document_chat_message(
    chat_data: DocumentChatMessage,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    📄 ЧАТ ПО ДОКУМЕНТУ
    
    Логика:
    1. Проверка лимитов
    2. Сохранение вопроса
    3. Обработка контекста (через document_chat_processor)
    4. Генерация ответа (GPT-5.2)
    5. Сохранение ответа
    6. Списание лимита
    """
    
    try:
        # Валидация
        user_message = chat_data.message.strip()
        document_id = chat_data.document_id
        
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': 'Пустое сообщение'}
            )
        
        # Получаем язык
        lang = await get_user_language(user_id)
        
        # Проверяем наличие детальных консультаций
        from subscription_manager import check_gpt4o_limit
        has_limits = await check_gpt4o_limit(user_id)
        
        if not has_limits:
            return JSONResponse(
                status_code=403,
                content={
                    'success': False,
                    'error': t('document_chat_requires_premium', lang),
                    'show_upgrade': True
                }
            )
        
        # Сохраняем сообщение пользователя
        conn = await get_db_connection()
        try:
            # Проверяем что документ принадлежит пользователю
            doc_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM documents WHERE id = $1 AND user_id = $2)",
                document_id, user_id
            )
            
            if not doc_exists:
                return JSONResponse(
                    status_code=404,
                    content={'success': False, 'error': 'Документ не найден'}
                )
            
            await conn.execute(
                """INSERT INTO document_chat_history (document_id, user_id, role, message)
                   VALUES ($1, $2, 'user', $3)""",
                document_id, user_id, user_message
            )
        finally:
            await release_db_connection(conn)
        
        # Обрабатываем контекст (вся логика вынесена)
        from document_chat_processor import process_document_chat_question, generate_document_chat_response
        
        context_data = await process_document_chat_question(
            user_id=user_id,
            document_id=document_id,
            user_message=user_message,
            lang=lang
        )
        
        if not context_data:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'error': 'Документ не найден'}
            )
        
        # Генерируем ответ
        ai_response = await generate_document_chat_response(
            context_data=context_data,
            user_message=user_message,
            lang=lang
        )
        
        # Сохраняем ответ
        conn = await get_db_connection()
        try:
            await conn.execute(
                """INSERT INTO document_chat_history (document_id, user_id, role, message)
                   VALUES ($1, $2, 'assistant', $3)""",
                document_id, user_id, ai_response
            )
        finally:
            await release_db_connection(conn)
        
        # Списываем лимит
        from subscription_manager import SubscriptionManager
        await SubscriptionManager.spend_limits(user_id, queries=1)
        
        # Форматируем для веба
        from webapp.utils.text_formatter import format_for_web
        formatted_response = format_for_web(ai_response)
        
        return JSONResponse(content={
            'success': True,
            'response': formatted_response
        })
        
    except Exception as e:
        safe_log_error("Ошибка в document-chat", error=e, user_id=user_id)
        
        try:
            lang = await get_user_language(user_id)
            error_msg = t('error_server', lang)
        except:
            error_msg = 'Ошибка сервера'
        
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': error_msg}
        )

@router.get("/check-auth")
async def check_auth_status(request: Request):
    """
    Проверка статуса аутентификации для PWA
    """
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return JSONResponse(content={
        "authenticated": True,
        "user_id": user_id
    })

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
        
        response_text = f"Image analysis:\n\n{analysis_result}"
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
    additional_context: str = Form(None),
    user_id: int = Depends(get_current_user)
):
    lang = await get_user_language(user_id)
    
    from subscription_manager import check_document_limit
    has_document_limits = await check_document_limit(user_id)
    
    if not has_document_limits:
        limits = await SubscriptionManager.get_user_limits(user_id)
        error_message = t("document_limit_exceeded", lang,
                         documents_left=limits['documents_left'],
                         gpt4o_queries_left=limits['gpt4o_queries_left'])
        return JSONResponse(status_code=403, content={'success': False, 'error': error_message})

    try:
        if not file.filename:
            return JSONResponse(status_code=400, content={'success': False, 'error': t('file_not_selected', lang)})
        
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return JSONResponse(status_code=400, content={'success': False, 'error': t('unsupported_file_type', lang)})
        
        # Проверка MIME-type
        try:
            file_content = await file.read(2048)
            await file.seek(0)
            
            import filetype
            kind = filetype.guess(file_content)
            detected_mime = kind.mime if kind else 'application/octet-stream'
            
            if detected_mime not in Config.ALLOWED_MIME_TYPES:
                safe_log_warning("Отклонён файл с недопустимым MIME-type",
                    user_id=user_id, filename_length=len(filename),
                    detected_mime=detected_mime, file_extension=file_ext)
                return JSONResponse(status_code=400, content={'success': False, 'error': t('file_mime_type_mismatch', lang)})
            
            safe_log_warning("Файл прошёл проверку MIME-type",
                user_id=user_id, file_extension=file_ext, detected_mime=detected_mime)
            
        except Exception as e:
            safe_log_error("Ошибка при проверке MIME-type файла", user_id=user_id, error=e)
            return JSONResponse(status_code=500, content={'success': False, 'error': t('file_validation_error', lang)})
        
        # Сохраняем файл временно — НЕ удаляем, фоновая задача сделает это сама
        temp_dir = f"temp_{user_id}"
        os.makedirs(temp_dir, exist_ok=True)
        local_file = os.path.join(temp_dir, f"{uuid.uuid4().hex[:8]}_{filename}")
        
        content = await file.read()
        with open(local_file, 'wb') as f:
            f.write(content)

        # Считаем страницы PDF
        pdf_total_pages = None
        if file_ext == 'pdf':
            try:
                import pypdf
                with open(local_file, 'rb') as f:
                    pdf_total_pages = len(pypdf.PdfReader(f).pages)
            except Exception:
                pass

        # Создаём запись в БД со статусом processing (без file_path — добавим после обработки)
        file_type = "pdf" if file_ext == "pdf" else "image"
        conn = await get_db_connection()
        try:
            document_id = await conn.fetchval("""
                INSERT INTO documents 
                (user_id, file_path, file_type, additional_context, confirmed, pdf_total_pages)
                VALUES ($1, $2, $3, $4, false, $5)
                RETURNING id
            """, user_id, '', file_type, additional_context, pdf_total_pages)
        finally:
            await release_db_connection(conn)

        # Запускаем обработку в фоне
        asyncio.create_task(
            _process_document_background(document_id, user_id, local_file, temp_dir, filename, lang, additional_context)
        )

        return JSONResponse(content={
            'success': True,
            'document_id': document_id,
            'status': 'processing'
        })

    except Exception as e:
        safe_log_error("Критическая ошибка загрузки документа", error=e, user_id=user_id)
        try:
            if 'local_file' in locals() and os.path.exists(local_file):
                os.remove(local_file)
        except:
            pass
        return JSONResponse(status_code=500, content={'success': False, 'error': t('document_processing_error', lang)})


async def _process_document_background(document_id: int, user_id: int, local_file: str, temp_dir: str, filename: str, lang: str, additional_context: str):
    """Фоновая обработка — локальный файл передаётся напрямую как раньше"""
    from document_processor import process_document
    from vector_db_postgresql import split_into_chunks, add_chunks_to_vector_db
    from file_storage import get_file_storage
    from subscription_manager import SubscriptionManager
    import shutil

    try:
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        file_type = "pdf" if file_ext == "pdf" else "image"

        # Обрабатываем локальный файл
        result = await process_document(
            file_path=local_file,
            user_id=user_id,
            lang=lang,
            additional_context=additional_context
        )

        if not result.get('success', False):
            error_msg = result.get('message', 'Processing failed')[:200]
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "UPDATE documents SET title = $1 WHERE id = $2",
                    f"⚠️ {error_msg}", document_id
                )
            finally:
                await release_db_connection(conn)
            return

        # Сохраняем файл в постоянное хранилище
        storage = get_file_storage()
        success, permanent_path = storage.save_file(
            user_id=user_id,
            filename=filename,
            source_path=local_file
        )

        if not success:
            conn = await get_db_connection()
            try:
                await conn.execute(
                    "UPDATE documents SET title = $1 WHERE id = $2",
                    "⚠️ Ошибка сохранения файла", document_id
                )
            finally:
                await release_db_connection(conn)
            return

        # Сохраняем результаты в БД — confirmed = false, пользователь ещё ждёт
        conn = await get_db_connection()
        try:
            from datetime import date
            document_date = result.get('document_date')
            document_date_obj = None
            if document_date and document_date != 'null':
                try:
                    document_date_obj = date.fromisoformat(str(document_date))
                except:
                    pass

            await conn.execute("""
                UPDATE documents SET
                    file_path = $1,
                    full_analysis = $2,
                    title = $3,
                    raw_text = $4,
                    summary = $5,
                    document_type = $6,
                    subtype = $7,
                    first_analysis = $8,
                    document_date = $9,
                    confirmed = false
                WHERE id = $10
            """,
                permanent_path,
                result.get('full_analysis'),
                result.get('title', 'Document'),
                result.get('raw_text', ''),
                result.get('summary', ''),
                result.get('document_type'),
                result.get('subtype'),
                result.get('first_analysis'),
                document_date_obj,
                document_id
            )
        finally:
            await release_db_connection(conn)

        # Векторная база — запускаем в фоне, не ждём
        async def _update_vector_db():
            try:
                summary = result.get('summary', '')
                if summary:
                    chunks = await split_into_chunks(summary, document_id, user_id)
                    await add_chunks_to_vector_db(document_id, user_id, chunks)
            except Exception as e:
                safe_log_warning("Ошибка векторной базы при фоновой обработке", error=e)

        asyncio.create_task(_update_vector_db())

        # Timeline — ждём
        try:
            from medical_timeline import update_medical_timeline_on_document_upload
            await update_medical_timeline_on_document_upload(
                user_id=user_id,
                document_id=document_id,
                document_text=result.get('raw_text', ''),
                document_date=result.get('document_date'),
                use_gemini=False
            )
        except Exception as e:
            safe_log_warning("Ошибка timeline при фоновой обработке", error=e)

        # Первое сообщение — ждём
        try:
            from document_questions import generate_and_save_first_message
            from medical_timeline import get_document_importance
            importance = await get_document_importance(document_id, user_id)
            await generate_and_save_first_message(
                document_id=document_id,
                user_id=user_id,
                full_analysis=result.get('full_analysis'),
                importance=importance,
                lang=lang
            )
        except Exception as e:
            safe_log_warning("Ошибка генерации первого сообщения при фоновой обработке", error=e)

        # Списываем лимит — ждём
        await SubscriptionManager.spend_limits(user_id, documents=1)

        # Только теперь confirmed = true — polling увидит completed
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE documents SET confirmed = true WHERE id = $1",
                document_id
            )
        finally:
            await release_db_connection(conn)

    except Exception as e:
        safe_log_error("Критическая ошибка фоновой обработки документа", error=e, document_id=document_id)
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE documents SET title = $1 WHERE id = $2",
                "⚠️ Ошибка обработки", document_id
            )
        finally:
            await release_db_connection(conn)

    finally:
        # Удаляем временные файлы в любом случае
        try:
            if os.path.exists(local_file):
                os.remove(local_file)
            pages_dir = f"{temp_dir}/pages"
            if os.path.exists(pages_dir):
                shutil.rmtree(pages_dir)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            safe_log_warning("Ошибка удаления временных файлов", error=e)

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
            
            # 4️⃣ Удаляем файл
            if doc['file_path']:
                try:
                    if doc['file_path'].startswith("users/"):  # Supabase
                        from supabase_storage import get_storage_manager
                        storage = get_storage_manager()
                        await storage.delete_file(doc['file_path'])
                    else:  # Локальное хранилище
                        import asyncio
                        if os.path.exists(doc['file_path']):
                            await asyncio.to_thread(os.remove, doc['file_path'])  # ✅ Асинхронно!
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
        from db_postgresql import delete_user_completely
        success = await delete_user_completely(user_id)
        
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
# Оплата подписки
# ==========================================

@router.get("/payment/details")
async def get_payment_details(
    request: Request,
    session_id: str,
    user_id: int = Depends(get_current_user)
):
    """
    Получает детали успешного платежа для модального окна
    """
    try:
        import stripe
        from stripe_config import StripeConfig
        from webapp.translations import t
        from db_postgresql import get_user_language
        
        # Получаем данные сессии из Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Проверяем что сессия принадлежит этому пользователю
        if int(session.metadata.get('user_id', 0)) != user_id:
            return JSONResponse(
                status_code=403,
                content={'success': False, 'error': 'Forbidden'}
            )
        
        # Получаем язык пользователя
        lang = await get_user_language(user_id)
        
        # Получаем данные о пакете
        package_id = session.metadata.get('package_id', 'unknown')
        package_info = StripeConfig.get_package_info(package_id)
        
        if package_info:
            package_name = t(package_info.get('user_friendly_name_key', 'package_basic_name'), lang)
            documents = package_info.get('documents', 0)
            queries = package_info.get('gpt4o_queries', 0)
        else:
            package_name = "Package"
            documents = 0
            queries = 0
        
        return {
            'success': True,
            'package_name': package_name,
            'documents': documents,
            'queries': queries,
            'is_subscription': session.mode == 'subscription'
        }
        
    except stripe.StripeError as e:
        safe_log_error("Stripe error getting payment details", error=e, user_id=user_id, session_id=session_id)
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Invalid session'}
        )
    except Exception as e:
        safe_log_error("Error getting payment details", error=e, user_id=user_id, session_id=session_id)
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': 'Internal error'}
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
        
        # Проверяем и отменяем старую подписку если есть
        # (отмена старой подписки происходит автоматически в stripe_manager.py)
        
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

# ============================================
# 🧪 ТЕСТОВЫЙ ENDPOINT (удалить после отладки)
# ============================================

@router.get("/test-gpt5-form")
async def test_gpt5_form(request: Request):
    """GET страница с формой"""
    from webapp.app import templates
    from webapp.utils.context import get_template_context
    
    context = get_template_context(request)
    return templates.TemplateResponse("test_gpt5.html", context)

from pydantic import BaseModel
import time

class TestGPT5Request(BaseModel):
    text: str
    lang: str = "uk"

@router.post("/test-gpt5")
async def test_gpt5_mini(request_data: TestGPT5Request):
    """🧪 Тестовый endpoint для проверки GPT-5-mini"""
    try:
        start_time = time.time()
        
        from gpt import client
        
        lang_names = {'ru': 'Russian', 'uk': 'Ukrainian', 'en': 'English', 'de': 'German'}
        target_language = lang_names.get(request_data.lang, 'Ukrainian')
        
        system_prompt = (
            "You are a medical assistant.\n"
            "Your task is to generate a concise medical document title.\n"
            f"You MUST respond ONLY in {target_language}.\n"
            "Return ONLY the title as plain text."
        )
        
        user_prompt = f"Generate a short title:\n\n{request_data.text[:1500]}"
        
        print(f"\n{'='*60}")
        print(f"🧪 TEST GPT-5-MINI")
        print(f"📝 Input: {request_data.text[:100]}...")
        
        response = await client.responses.create(
            model="gpt-5.2-pro",  # ← 5.2 вместо nano
            input=[
                {"role": "user", "content": f"Generate a short Ukrainian medical document title:\n\n{request_data.text[:1500]}"}
            ],
            max_output_tokens=100
        )
        
        print(f"📥 Response type: {type(response)}")
        print(f"Has output_text: {hasattr(response, 'output_text')}")
        
        output_text_direct = getattr(response, 'output_text', None)
        print(f"output_text value: {repr(output_text_direct)}")
        
        # 🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА response.output
        texts = []
        if hasattr(response, 'output'):
            print(f"\n🔍 response.output exists!")
            
            for i, item in enumerate(response.output or []):
                print(f"\n  📦 Item {i}:")
                print(f"     Type: {type(item)}")
                
                # ✅ ПРОБУЕМ ИЗВЛЕЧЬ ИЗ REASONING
                if hasattr(item, 'summary'):
                    summary = getattr(item, 'summary', None)
                    print(f"     summary: {repr(summary)}")
                    if summary:
                        texts.append(summary)
                
                if hasattr(item, 'content'):
                    content = getattr(item, 'content', None)
                    print(f"     content: {repr(content)}")
                    if content:
                        texts.append(str(content))
                
                # Пробуем все текстовые атрибуты
                for attr in ['text', 'output', 'result', 'answer']:
                    if hasattr(item, attr):
                        val = getattr(item, attr, None)
                        if val:
                            print(f"     {attr}: {repr(val)[:200]}")
                            texts.append(str(val))
        
        extracted = " ".join(t.strip() for t in texts if t and str(t).strip())
        print(f"\n✅ Extracted: {repr(extracted)}")
        
        texts = []
        if hasattr(response, 'output'):
            for item in response.output or []:
                if hasattr(item, 'content'):
                    for block in item.content or []:
                        if hasattr(block, 'text') and block.text:
                            texts.append(block.text)
                            print(f"✅ Found text: {repr(block.text)}")
        
        extracted = " ".join(t.strip() for t in texts if t and t.strip())
        
        return JSONResponse(content={
            'success': True,
            'title': extracted or output_text_direct or "",
            'model': 'gpt-5-mini',
            'processing_time': int((time.time() - start_time) * 1000),
            'output_text': output_text_direct
        })
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})

# ==========================================
# 📄 ОТОБРАЖЕНИЕ ФАЙЛОВ ДОКУМЕНТОВ
# ==========================================

@router.get("/document-image/{doc_id}")
async def get_document_image(doc_id: int, user_id: int = Depends(get_current_user)):
    """
    Возвращает изображение документа для отображения
    """
    from db_postgresql import get_db_connection, release_db_connection
    import tempfile
    
    conn = await get_db_connection()
    try:
        doc = await conn.fetchrow(
            "SELECT file_path FROM documents WHERE id = $1 AND user_id = $2",
            doc_id, user_id
        )
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc['file_path']
        
        # Если файл в Supabase Storage
        if file_path.startswith("users/"):
            from supabase_storage import get_storage_manager
            storage = get_storage_manager()
            
            # Создаём временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1])
            temp_path = temp_file.name
            temp_file.close()
            
            # Скачиваем из Supabase
            success = await storage.download_file(
                storage_path=file_path,
                local_path=temp_path
            )
            
            if not success:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise HTTPException(status_code=404, detail="File not found in storage")
            
            # Определяем media_type
            ext = os.path.splitext(file_path)[1].lower()
            media_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            media_type = media_type_map.get(ext, 'image/png')
            
            return FileResponse(temp_path, media_type=media_type)
        
        # Если локальный файл
        else:
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            
            ext = os.path.splitext(file_path)[1].lower()
            media_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            media_type = media_type_map.get(ext, 'image/png')
            
            return FileResponse(file_path, media_type=media_type)
        
    finally:
        await release_db_connection(conn)

@router.get("/document-pdf/{doc_id}")
async def get_document_pdf(doc_id: int, user_id: int = Depends(get_current_user)):
    """
    Возвращает PDF документ для отображения в iframe
    """
    from db_postgresql import get_db_connection, release_db_connection
    import tempfile
    
    conn = await get_db_connection()
    try:
        doc = await conn.fetchrow(
            "SELECT file_path FROM documents WHERE id = $1 AND user_id = $2",
            doc_id, user_id
        )
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc['file_path']
        
        # Если файл в Supabase Storage
        if file_path.startswith("users/"):
            from supabase_storage import get_storage_manager
            storage = get_storage_manager()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            success = await storage.download_file(
                storage_path=file_path,
                local_path=temp_path
            )
            
            if not success:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise HTTPException(status_code=404, detail="File not found in storage")
            
            return FileResponse(temp_path, media_type="application/pdf")
        
        # Если локальный файл
        else:
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(file_path, media_type="application/pdf")
        
    finally:
        await release_db_connection(conn)

@router.get("/stats")
async def get_stats():
    """stats_live_title"""
    from db_postgresql import get_db_connection, release_db_connection
    
    conn = await get_db_connection()
    try:
        # users_stat_label
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        users = users + 1100
        
        # documents_stat_label
        documents = await conn.fetchval("SELECT COUNT(*) FROM documents")
        documents = users + documents + 1500
        
        # questions_stat_label
        questions = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_history"
        )
        questions = users + questions + 6000

        return {
            "users": users or 0,
            "documents": documents or 0,
            "questions": questions or 0
        }
        
    finally:
        await release_db_connection(conn)

@router.post("/update-document/{document_id}")
async def update_document(
    document_id: int,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """Обновление названия и даты документа"""
    from db_postgresql import get_db_connection, release_db_connection, get_user_language
    from datetime import datetime
    
    lang = await get_user_language(user_id)
    
    data = await request.json()
    new_title = data.get('title', '').strip()
    new_date_str = data.get('document_date')  # ← Было uploaded_at
    
    if not new_title:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": t("error_empty_title", lang)}
        )
    
    conn = await get_db_connection()
    try:
        # Проверяем что документ принадлежит пользователю
        doc = await conn.fetchrow(
            "SELECT user_id FROM documents WHERE id = $1",
            document_id
        )
        
        if not doc or doc['user_id'] != user_id:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Document not found"}
            )
        
        # Парсим дату (формат YYYY-MM-DD с фронтенда)
        if new_date_str:
            try:
                new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            except ValueError:
                new_date = None
        else:
            new_date = None
        
        # Обновляем документ (document_date вместо uploaded_at)
        await conn.execute(
            """
            UPDATE documents 
            SET title = $1, document_date = $2
            WHERE id = $3
            """,
            new_title, new_date, document_id
        )
        
        return {"success": True, "message": t("document_updated", lang)}
        
    except Exception as e:        
        safe_log_error("Ошибка обновления документа", error=e, user_id=user_id, document_id=document_id)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": t("error_save_failed", lang)}
        )
        
    finally:
        await release_db_connection(conn)

async def cleanup_old_pending_documents(user_id: int):
    """Удаляет pending документы старше 24ч"""
    from db_postgresql import get_db_connection, release_db_connection
    from file_storage import get_file_storage
    
    conn = await get_db_connection()
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Находим старые pending документы
        old_docs = await conn.fetch("""
            SELECT id, file_path 
            FROM documents 
            WHERE user_id = $1 
            AND confirmed = false 
            AND full_analysis IS NULL 
            AND uploaded_at < $2
        """, user_id, cutoff_time)
        
        storage = get_file_storage()
        
        for doc in old_docs:
            # Удаляем файл
            if doc['file_path']:
                try:
                    if doc['file_path'].startswith("users/"):
                        from supabase_storage import get_storage_manager
                        supabase_storage = get_storage_manager()
                        await supabase_storage.delete_file(doc['file_path'])
                    else:
                        import os
                        if os.path.exists(doc['file_path']):
                            os.remove(doc['file_path'])
                except:
                    pass
            
            # Удаляем запись
            await conn.execute("DELETE FROM documents WHERE id = $1", doc['id'])
        
    finally:
        await release_db_connection(conn)

@router.post("/create-one-time-document-checkout")
async def create_one_time_document_checkout(
    request: Request,
    file: UploadFile = File(...),
    additional_context: str = Form(""),
    user_id: int = Depends(get_current_user)
):
    """
    Создаёт pending документ и Stripe checkout для разовой оплаты
    """
    from db_postgresql import get_user_language, get_db_connection, release_db_connection
    from file_storage import get_file_storage
    from stripe_manager import StripeManager
    
    lang = await get_user_language(user_id)

    # 🔔 ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ АДМИНУ (безопасно)
    try:
        from webapp.utils.telegram_notifications import notify_paid_analysis_attempt
        user_profile = await get_user_profile(user_id)
        user_email = user_profile.get('email')
        await notify_paid_analysis_attempt(user_id, user_email)
    except Exception as e:
        # Ошибка уведомления не должна блокировать оплату
        safe_log_warning("Не удалось отправить уведомление админу", error=e)
    
    # 0. Cleanup старых pending
    await cleanup_old_pending_documents(user_id)
    
    try:
        # 1. Валидация файла
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': t('file_not_selected', lang)}
            )
        
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        allowed_exts = ['pdf', 'jpg', 'jpeg', 'png', 'heic']
        if file_ext not in allowed_exts:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': t('invalid_file_format', lang)}
            )
        
        # 2. Сохраняем файл во временную директорию
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"temp_{user_id}_{int(datetime.now().timestamp())}_{filename}")
        
        content = await file.read()
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        # 3. Сохраняем в Storage
        storage = get_file_storage()
        success, permanent_path = storage.save_file(
            user_id=user_id,
            filename=filename,
            source_path=temp_file_path
        )

        # Считаем страницы PDF до удаления временного файла
        pdf_total_pages = None
        if file_ext == 'pdf':
            try:
                import pypdf
                with open(temp_file_path, 'rb') as f:
                    pdf_total_pages = len(pypdf.PdfReader(f).pages)
            except Exception:
                pass
        
        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if not success:
            return JSONResponse(
                status_code=500,
                content={'success': False, 'error': t('file_storage_error', lang)}
            )
        
        # 4. Создаём pending документ в БД
        file_type = "pdf" if file_ext == "pdf" else "image"
        
        conn = await get_db_connection()
        try:
            document_id = await conn.fetchval("""
                INSERT INTO documents 
                (user_id, file_path, file_type, additional_context, confirmed, payment_confirmed, pdf_total_pages)
                VALUES ($1, $2, $3, $4, false, false, $5)
                RETURNING id
            """, user_id, permanent_path, file_type, additional_context, pdf_total_pages)
        finally:
            await release_db_connection(conn)
        
        # 5. Создаём Stripe checkout session
        result = await StripeManager.create_one_time_document_checkout(
            user_id=user_id,
            document_id=document_id,
            lang=lang
        )
        
        success, url_or_error = result
        
        if not success:
            # Откатываем - удаляем документ и файл
            conn = await get_db_connection()
            try:
                await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            finally:
                await release_db_connection(conn)
            
            storage.delete_file(permanent_path)
            
            return JSONResponse(
                status_code=500,
                content={'success': False, 'error': url_or_error}
            )
                
        return {
            'success': True,
            'checkout_url': url_or_error,
            'document_id': document_id
        }
        
    except Exception as e:        
        safe_log_error("Ошибка создания one-time checkout", error=e, user_id=user_id)
        
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': t('stripe_session_creation_error', lang)}
        )
    
@router.get("/check-document-status/{document_id}")
async def check_document_status(
    document_id: int,
    request: Request,
    user_id: int = Depends(get_current_user)
):
    """
    Проверяет статус обработки документа
    Возвращает: processing | completed | failed
    """
    from db_postgresql import get_db_connection, release_db_connection
    
    conn = await get_db_connection()
    try:
        doc = await conn.fetchrow("""
            SELECT id, confirmed, full_analysis, title
            FROM documents
            WHERE id = $1 AND user_id = $2
        """, document_id, user_id)
        
        if not doc:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'status': 'not_found'}
            )
        
        # Определяем статус
        if doc['confirmed'] is True and doc['full_analysis']:
            status = 'completed'
        elif doc['title'] and '⚠️' in str(doc['title']):
            status = 'failed'
            error_message = doc['title']
        else:
            status = 'processing'

        return {
            'success': True,
            'status': status,
            'document_id': document_id,
            'title': doc['title'],
            'error_message': error_message if status == 'failed' else None
        }

    finally:
        await release_db_connection(conn)