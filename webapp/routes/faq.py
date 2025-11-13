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