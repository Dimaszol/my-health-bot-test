# webapp/routes/faq.py
# ❓ FAQ страница

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from webapp.utils.context import get_template_context
from webapp.faq_translations import get_faq_translation

router = APIRouter()
templates = Jinja2Templates(directory="webapp/templates")

@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    """
    Страница FAQ (Часто задаваемые вопросы)
    """
    context = get_template_context(request)
    
    # Добавляем функцию переводов FAQ в контекст
    context['faq_t'] = get_faq_translation
    
    return templates.TemplateResponse('faq.html', context)

@router.get("/{lang}/faq", response_class=HTMLResponse)
async def faq_page_with_lang(request: Request, lang: str):
    """
    FAQ страница с языковым префиксом
    
    Примеры:
    /de/faq → FAQ на немецком
    /ru/faq → FAQ на русском
    """
    # Проверяем что это язык
    if lang not in ['de', 'ru', 'uk']:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    
    # Устанавливаем язык в сессию
    request.session['language'] = lang
    
    context = get_template_context(request)
    context['faq_t'] = get_faq_translation
    
    return templates.TemplateResponse('faq.html', context)