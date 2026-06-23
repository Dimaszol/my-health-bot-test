# webapp/routes/seo.py
# 🔬 SEO страницы показателей анализов крови

import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
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
    group: str = 'blood'


# ==========================================
# 🤖 ПРОМТЫ ДЛЯ AI
# ==========================================

CORE_PROMPT = """You are a medical assistant explaining a biomarker result based on the user’s sex and age.

Input:
- Indicator: {indicator_name}
- Value: {value} {unit}
- Sex: {sex}
- Age: {age}

Explain clearly what this value means.

Guidelines:
- Start with a direct interpretation (normal / high / low)
- Explain possible meaning in simple terms
- Briefly assess importance (calm, not alarming)
- Make it clear that one marker does not give the full picture
- Emphasize that real insight comes from combining multiple markers
- Mention that without full analysis, interpretation may be incomplete

CTA:
- End with a clear, confident suggestion to upload the full test
- Show the benefit: better accuracy, context, and understanding of all markers
- No weak phrasing like “if you want”

Rules:
- No lists, headings, or markdown in the output
- Write naturally, like a doctor explaining to a patient
- Avoid complex terms, rare diagnoses, and treatment advice

Style:
- calm, clear, human
- short paragraphs (1–3 sentences)

Additional:
- If near normal range, say it’s borderline and often not significant

IMPORTANT: respond in {lang}"""

GROUP_PROMPTS = {
    'blood': """[Blood test context]
You are interpreting a marker from a complete blood count.
These markers are often related to anemia, inflammation, or overall blood condition.
They are usually more meaningful when interpreted together with other values.""",

    'biochemistry': """[Biochemistry context]
You are interpreting a biochemical blood marker.
These markers reflect organ function and metabolism.
Values may be influenced by diet, physical activity, or medications.""",

    'lipids': """[Lipid profile context]
You are interpreting a lipid marker.
Lipid values are best understood together (cholesterol, HDL, LDL, triglycerides).
A single value does not reflect full cardiovascular risk.""",

    'liver': """[Liver context]
You are interpreting a liver-related marker.
These values may temporarily change due to alcohol, medication, or physical stress.
A single abnormal result does not always indicate disease.""",

    'kidney': """[Kidney context]
You are interpreting a kidney-related marker.
These values depend on hydration, diet, and muscle mass.
Single results are less informative than trends over time.""",

    'thyroid': """[Thyroid context]
You are interpreting a thyroid-related marker.
Thyroid hormones affect metabolism, energy, and weight.
Interpretation often depends on other hormone levels and symptoms.""",

    'cardiac': """[Cardiac context]
You are interpreting a cardiac marker.
Some markers may rise with physical activity or stress.
Clinical meaning depends on symptoms and context.""",

    'hormones': """[Hormone context]
You are interpreting a hormone marker.
Hormone levels vary with time of day, stress, and (in women) cycle phase.
A single result is only a reference point.""",

    'vitamins': """[Vitamins context]
You are interpreting a vitamin or mineral level.
Deficiencies are common and often non-specific.
Interpretation depends on diet and lifestyle.""",

    'coagulation': """[Coagulation context]
You are interpreting a coagulation marker.
These values are sensitive to medications and health conditions.
Abnormal results should be interpreted carefully.""",

    'inflammation': """[Inflammation context]
You are interpreting an inflammation marker.
These markers are non-specific and can increase for many reasons.
A single value does not indicate a specific cause.""",

    'diabetes': """[Glucose metabolism context]
You are interpreting a glucose-related marker.
Values depend on timing of meals and testing conditions.
Diagnosis requires multiple measurements.""",

    'electrolytes': """[Electrolytes context]
You are interpreting an electrolyte marker.
Electrolytes depend on hydration, diet, and kidney function.
Even small changes may be clinically relevant.""",

    'iron': """[Iron metabolism context]
You are interpreting an iron-related marker.
Iron deficiency is a common cause of abnormalities.
Full interpretation usually requires multiple related markers.""",

    'tumor_markers': """[Tumor marker context]
You are interpreting a tumor marker.
These markers are not specific for cancer and may increase for many reasons.
Avoid strong conclusions and keep interpretation cautious.""",

    'urine': """[Urine test context]
You are interpreting a urine test marker.
Results may vary depending on hydration, collection conditions, and time of day.
Single abnormalities are often temporary.""",
}


# ==========================================
# 📋 СТРАНИЦА КАТАЛОГА БИОМАРКЕРОВ
# ==========================================

GROUP_ORDER = [
    'blood', 'biochemistry', 'lipids', 'liver', 'kidney',
    'thyroid', 'cardiac', 'hormones', 'vitamins', 'coagulation',
    'inflammation', 'diabetes', 'electrolytes', 'iron',
    'tumor_markers', 'urine'
]

@router.get("/analysis", response_class=HTMLResponse)
@router.get("/{lang}/analysis", response_class=HTMLResponse)
async def analysis_list(request: Request, lang: str = "en"):
    
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=404)

    request.session['language'] = lang

    conn = await get_db_connection()
    try:
        rows_main = await conn.fetch("""
            SELECT s.name_localized, s.short_desc, s.slug, i.unit, i.type AS group_slug
            FROM seo_indicators s
            JOIN indicators i ON s.slug = i.slug
            WHERE s.lang = $1 AND i.is_published = TRUE
        """, lang)

        rows_extra = await conn.fetch("""
            SELECT s.name_localized, s.short_desc, s.slug, i.unit, ig.group_slug
            FROM indicator_groups ig
            JOIN indicators i ON ig.indicator_slug = i.slug
            JOIN seo_indicators s ON i.slug = s.slug
            WHERE s.lang = $1 AND i.is_published = TRUE
        """, lang)
    finally:
        await release_db_connection(conn)

    from collections import defaultdict
    groups = defaultdict(dict)

    for row in rows_main:
        slug = row['slug']
        group = row['group_slug']
        groups[group][slug] = {
            'slug': slug,
            'name': row['name_localized'],
            'short_desc': row['short_desc'] or '',
            'unit': row['unit'],
        }

    for row in rows_extra:
        slug = row['slug']
        group = row['group_slug']
        groups[group][slug] = {
            'slug': slug,
            'name': row['name_localized'],
            'short_desc': row['short_desc'] or '',
            'unit': row['unit'],
        }

    ordered_groups = {}
    for g in GROUP_ORDER:
        if g in groups:
            ordered_groups[g] = list(groups[g].values())
    for g in groups:
        if g not in ordered_groups:
            ordered_groups[g] = list(groups[g].values())

    total = sum(len(v) for v in ordered_groups.values())

    from webapp.seo_translations import st
    ctx = get_template_context(request)
    ctx.update({
        'groups': ordered_groups,
        'total': total,
        'st': st,
    })
    return templates.TemplateResponse("seo_analysis_list.html", ctx)


# ==========================================
# 🔬 СТРАНИЦА ПОКАЗАТЕЛЯ
# ==========================================

@router.get("/analysis/{slug}", response_class=HTMLResponse)
@router.get("/{lang}/analysis/{slug}", response_class=HTMLResponse)
async def indicator_page(request: Request, slug: str, lang: str = "en"):

    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=404)

    request.session['language'] = lang

    # Редиректы 301 для старых слагов из Google Search Console
    SLUG_REDIRECTS = {
        "anti-tpo": "anti_tpo",
        "bilirubin-total": "bilirubin_total",
        "reticulocytes": "reticulocyte",
        "non-hdl": "non_hdl",
    }
    if slug in SLUG_REDIRECTS:
        lang_prefix = f"/{lang}" if lang != "en" else ""
        return RedirectResponse(url=f"{lang_prefix}/analysis/{SLUG_REDIRECTS[slug]}", status_code=301)

    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT
                s.name_localized, s.meta_title, s.meta_desc, s.h1,
                s.quick_answer, s.explanation,
                s.norms, s.causes_high, s.causes_low,
                s.todo_items, s.faqs, s.related,
                s.canonical_slug,
                s.interpretation, s.combinations, s.symptoms, s.when_to_see_doctor,
                i.slug, i.unit, i.type,
                i.normal_min_m, i.normal_max_m,
                i.normal_min_f, i.normal_max_f,
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
        "type": row["type"],
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
        "canonical_slug": row["canonical_slug"],
        "interpretation": json.loads(row["interpretation"]) if isinstance(row["interpretation"], str) else (row["interpretation"] or {}),
        "combinations": json.loads(row["combinations"]) if isinstance(row["combinations"], str) else (row["combinations"] or []),
        "symptoms": json.loads(row["symptoms"]) if isinstance(row["symptoms"], str) else (row["symptoms"] or []),
        "when_to_see_doctor": row["when_to_see_doctor"] or "",
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
    from openai import AsyncOpenAI
    import os
    import time

    # Rate limit по IP
    client_ip = request.client.host
    if not hasattr(seo_check, "_requests"):
        seo_check._requests = {}

    now = time.time()
    window = 60
    max_requests = 5

    ip_data = seo_check._requests.get(client_ip, {"count": 0, "window_start": now})
    if now - ip_data["window_start"] > window:
        ip_data = {"count": 0, "window_start": now}

    if ip_data["count"] >= max_requests:
        raise HTTPException(status_code=429, detail="Too many requests")

    ip_data["count"] += 1
    seo_check._requests[client_ip] = ip_data

    # Валидация
    if len(body.prompt) > 500:
        raise HTTPException(status_code=400, detail="Prompt too long")

    if body.lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="Invalid language")

    if body.group not in GROUP_PROMPTS:
        body.group = 'blood'

    try:
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        group_context = GROUP_PROMPTS.get(body.group, '')
        system_prompt = CORE_PROMPT.format(
            indicator_name='',
            value='',
            unit='',
            sex='',
            age='',
            lang=body.lang
        )
        full_prompt = f"{group_context}\n\n{body.prompt}" if group_context else body.prompt

        response = await openai_client.responses.create(
            model="gpt-5.4-mini",
            max_output_tokens=400,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ]
        )

        result = response.output_text
        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))