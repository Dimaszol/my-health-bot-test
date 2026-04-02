# webapp/routes/legal.py
# 📜 Роуты для Privacy Policy и Terms of Service (FastAPI)

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from webapp.utils.context import get_template_context
from webapp.legal_translations import tl as legal_t  # ← Переименовываем как legal_t
from webapp.translations import get_current_language
from webapp.about_translations import about_t

# Создаём роутер
router = APIRouter()

# Подключаем шаблоны
templates = Jinja2Templates(directory="webapp/templates")

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """
    Privacy Policy страница
    
    Показывает политику конфиденциальности на языке пользователя
    """
    lang = get_current_language(request.session)
    
    # Используем готовую функцию для получения базового контекста
    context = get_template_context(request)
    
    # Добавляем специфичные для legal страниц переменные
    context['page_title'] = legal_t('privacy_title', lang)
    context['legal_t'] = legal_t  # ← Передаем функцию (без lambda!)
    
    return templates.TemplateResponse("legal/privacy.html", context)


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """
    Terms of Service страница
    
    Показывает условия использования на языке пользователя
    """
    lang = get_current_language(request.session)
    
    # Используем готовую функцию для получения базового контекста
    context = get_template_context(request)
    
    # Добавляем специфичные для legal страниц переменные
    context['page_title'] = legal_t('terms_title', lang)
    context['legal_t'] = legal_t  # ← Передаем функцию (без lambda!)
    
    return templates.TemplateResponse("legal/terms.html", context)

# ==========================================
# 🌍 МУЛЬТИЯЗЫЧНЫЕ РОУТЫ
# ==========================================

@router.get("/{lang}/privacy", response_class=HTMLResponse)
async def privacy_policy_with_lang(request: Request, lang: str):
    """
    Privacy Policy с языковым префиксом
    
    Примеры:
    /de/privacy → Privacy на немецком
    /ru/privacy → Privacy на русском
    """
    # Проверяем что это язык
    if lang not in ['de', 'ru', 'uk']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    
    # Устанавливаем язык в сессию
    request.session['language'] = lang
    
    context = get_template_context(request)
    context['page_title'] = legal_t('privacy_title', lang)
    context['legal_t'] = legal_t
    
    return templates.TemplateResponse("legal/privacy.html", context)


@router.get("/{lang}/terms", response_class=HTMLResponse)
async def terms_of_service_with_lang(request: Request, lang: str):
    """
    Terms of Service с языковым префиксом
    
    Примеры:
    /de/terms → Terms на немецком
    /ru/terms → Terms на русском
    """
    # Проверяем что это язык
    if lang not in ['de', 'ru', 'uk']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    
    # Устанавливаем язык в сессию
    request.session['language'] = lang
    
    context = get_template_context(request)
    context['page_title'] = legal_t('terms_title', lang)
    context['legal_t'] = legal_t
    
    return templates.TemplateResponse("legal/terms.html", context)

# ==========================================
# 🩺 MEDICAL DISCLAIMER
# ==========================================

@router.get("/medical-disclaimer", response_class=HTMLResponse)
async def medical_disclaimer(request: Request):
    """
    Medical Disclaimer (английская версия)
    """
    from webapp.medical_disclaimer_translations import md_t
    
    lang = get_current_language(request.session)
    context = get_template_context(request)
    context['md_t'] = md_t
    
    return templates.TemplateResponse("medical_disclaimer.html", context)


@router.get("/{lang}/medical-disclaimer", response_class=HTMLResponse)
async def medical_disclaimer_with_lang(request: Request, lang: str):
    """
    Medical Disclaimer с языковым префиксом
    """
    from webapp.medical_disclaimer_translations import md_t
    from fastapi import HTTPException
    
    if lang not in ['de', 'ru', 'uk']:
        raise HTTPException(status_code=404)
    
    request.session['language'] = lang
    context = get_template_context(request)
    context['md_t'] = md_t
    
    return templates.TemplateResponse("medical_disclaimer.html", context)

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    lang = get_current_language(request.session)
    context = get_template_context(request)
    context['about_t'] = about_t
    return templates.TemplateResponse("about.html", context)


@router.get("/{lang}/about", response_class=HTMLResponse)
async def about_page_with_lang(request: Request, lang: str):
    if lang not in ['de', 'ru', 'uk']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    request.session['language'] = lang
    context = get_template_context(request)
    context['about_t'] = about_t
    return templates.TemplateResponse("about.html", context)