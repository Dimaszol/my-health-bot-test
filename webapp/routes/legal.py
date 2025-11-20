# webapp/routes/legal.py
# 📜 Роуты для Privacy Policy и Terms of Service (FastAPI)

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from webapp.utils.context import get_template_context
from webapp.legal_translations import tl as legal_t  # ← Переименовываем как legal_t
from webapp.translations import get_current_language

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