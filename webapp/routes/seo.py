# webapp/routes/seo.py
# 🔬 SEO страницы показателей анализов крови

import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from webapp.utils.context import get_template_context
from db_postgresql import get_db_connection, release_db_connection


router = APIRouter()
templates = Jinja2Templates(directory="webapp/templates")

SUPPORTED_LANGS = ['ru', 'uk', 'en', 'de']


# ==========================================
# 📋 PYDANTIC MODEL
# ==========================================

class SeoCheckRequest(BaseModel):
    prompt: str
    lang: str


# ==========================================
# 🔬 СТРАНИЦА ПОКАЗАТЕЛЯ
# ==========================================

@router.get("/analysis/{slug}", response_class=HTMLResponse)
@router.get("/{lang}/analysis/{slug}", response_class=HTMLResponse)
async def indicator_page(request: Request, slug: str, lang: str = "en"):

    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=404)

    request.session['language'] = lang

    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT 
                s.name_localized, s.meta_title, s.meta_desc, s.h1,
                s.quick_answer, s.explanation,
                s.norms, s.causes_high, s.causes_low,
                s.todo_items, s.faqs, s.related,
                s.canonical_slug,
                i.slug, i.unit, i.type,
                i.normal_min_m, i.normal_max_m,
                i.normal_min_f, i.normal_max_f,
                i.ai_prompt,
                i.value_min, i.value_max, i.example_value
            FROM seo_indicators s
            JOIN indicators i ON s.slug = i.slug
            WHERE s.slug = $1 AND s.lang = $2 AND i.is_published = TRUE
        """, slug, lang)
    finally:
        await release_db_connection(conn)

    if not row:
        raise HTTPException(status_code=404)

    page = {
        "slug": row["slug"],
        "unit": row["unit"],
        "indicator_name": row["name_localized"],
        "meta_title": row["meta_title"],
        "meta_desc": row["meta_desc"],
        "h1": row["h1"],
        "quick_answer": row["quick_answer"],
        "explanation": row["explanation"],
        "norms": json.loads(row["norms"]) if isinstance(row["norms"], str) else row["norms"],
        "causes_high": json.loads(row["causes_high"]) if isinstance(row["causes_high"], str) else row["causes_high"],
        "causes_low": json.loads(row["causes_low"]) if isinstance(row["causes_low"], str) else row["causes_low"],
        "todo_items": json.loads(row["todo_items"]) if isinstance(row["todo_items"], str) else row["todo_items"],
        "faqs": json.loads(row["faqs"]) if isinstance(row["faqs"], str) else row["faqs"],
        "related": json.loads(row["related"]) if isinstance(row["related"], str) else row["related"],
        "normal_min_m": row["normal_min_m"],
        "normal_max_m": row["normal_max_m"],
        "normal_min_f": row["normal_min_f"],
        "normal_max_f": row["normal_max_f"],
        "ai_prompt": row["ai_prompt"],
        "canonical_slug": row["canonical_slug"],
        "value_min": row["value_min"],
        "value_max": row["value_max"],
        "example_value": row["example_value"],
    }

    from webapp.seo_translations import st
    context = get_template_context(request)
    context["page"] = page
    context["st"] = st

    return templates.TemplateResponse("seo_indicator.html", context)


# ==========================================
# 🤖 AI ЭНДПОИНТ (публичный, без логина)
# ==========================================

@router.post("/api/seo-check")
async def seo_check(request: Request, body: SeoCheckRequest):
    """
    Публичный AI эндпоинт для расшифровки показателя.
    Rate limiting по IP — защита от злоупотреблений.
    """
    from openai import AsyncOpenAI
    import os

    # Rate limit по IP
    client_ip = request.client.host
    # Используем простой in-memory счётчик (достаточно для старта)
    if not hasattr(seo_check, "_requests"):
        seo_check._requests = {}

    import time
    now = time.time()
    window = 60  # 1 минута
    max_requests = 5  # 5 запросов в минуту с одного IP

    ip_data = seo_check._requests.get(client_ip, {"count": 0, "window_start": now})
    if now - ip_data["window_start"] > window:
        ip_data = {"count": 0, "window_start": now}

    if ip_data["count"] >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests")

    ip_data["count"] += 1
    seo_check._requests[client_ip] = ip_data

    # Валидация промта
    if len(body.prompt) > 500:
        raise HTTPException(status_code=400, detail="Prompt too long")

    if body.lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="Invalid language")

    try:
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты медицинский ассистент. Даёшь краткую общую информацию об анализах. "
                        "Никогда не ставишь диагнозы. Всегда рекомендуешь обратиться к врачу. "
                        "Отвечаешь строго на языке пользователя."
                    )
                },
                {
                    "role": "user",
                    "content": body.prompt
                }
            ]
        )

        result = response.choices[0].message.content
        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail="AI service error")