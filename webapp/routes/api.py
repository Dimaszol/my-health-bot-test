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
        
        # STEP 3: 🎯 ГЛАВНОЕ! Генерируем заголовок
        if title and title.strip():
            # Пользователь указал название
            auto_title = title.strip()
            print(f"✅ Используем название от пользователя: {auto_title}")
        else:
            # Генерируем через GPT
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
        
        # STEP 8: Удаляем временные файлы
        try:
            if os.path.exists(local_file):
                os.remove(local_file)
            # Удаляем папку pages если есть
            pages_dir = f"{temp_dir}/pages"
            if os.path.exists(pages_dir):
                import shutil
                shutil.rmtree(pages_dir)
            # Удаляем временную папку если пустая
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"⚠️ Не удалось удалить временные файлы: {e}")
        
        # ✅ УСПЕХ! (с мультиязычным сообщением)
        print(f"🎉 Документ успешно обработан!")
        
        return {
            'success': True,
            'document_id': document_id,
            'title': auto_title,
            'summary': summary[:200] + '...' if len(summary) > 200 else summary,  # Краткое резюме
            'message': t('document_uploaded_successfully', lang, title=auto_title)
        }
        
    except Exception as e:
        print(f"❌ Критическая ошибка загрузки: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': t('document_processing_error', lang) if 'lang' in locals() else 'Error processing document'}
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