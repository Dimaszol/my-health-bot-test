# webapp/routes/ops.py
# 🔐 Панель операционной аналитики

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from db_postgresql import get_db_connection, release_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="webapp/templates")

ADMIN_SECRET = "1090805"  # ← замени на свой пароль

def check_auth(request: Request) -> bool:
    secret = request.query_params.get("secret") or request.session.get("admin_secret")
    return secret == ADMIN_SECRET


@router.get("/ops", response_class=HTMLResponse)
async def ops_page(request: Request):
    if not check_auth(request):
        return HTMLResponse("<h2>403 Forbidden</h2>", status_code=403)

    # Сохраняем секрет в сессии чтобы не вводить каждый раз
    request.session["admin_secret"] = request.query_params.get("secret", request.session.get("admin_secret"))

    conn = await get_db_connection()
    try:
        # Последние 50 пользователей
        users = await conn.fetch("""
            SELECT 
                u.user_id,
                u.name,
                u.email,
                u.registration_source,
                u.created_at,
                u.language,
                (SELECT MAX(timestamp) FROM analytics_events WHERE user_id = u.user_id) as last_active,
                (SELECT COUNT(*) FROM documents WHERE user_id = u.user_id AND confirmed = true) as doc_count,
                (SELECT COUNT(*) FROM analytics_events WHERE user_id = u.user_id) as event_count
            FROM users u
            ORDER BY u.created_at DESC
            LIMIT 50
        """)
    finally:
        await release_db_connection(conn)

    context = {
        "request": request,
        "users": [dict(u) for u in users],
        "secret": request.session.get("admin_secret", "")
    }
    return templates.TemplateResponse("ops.html", context)


@router.get("/ops/user/{user_id}", response_class=HTMLResponse)
async def ops_user_detail(request: Request, user_id: int):
    if not check_auth(request):
        return HTMLResponse("<h2>403 Forbidden</h2>", status_code=403)

    conn = await get_db_connection()
    try:
        # Профиль пользователя
        user = await conn.fetchrow("""
            SELECT user_id, name, email, registration_source, created_at, language
            FROM users WHERE user_id = $1
        """, user_id)

        if not user:
            return HTMLResponse("<h2>Пользователь не найден</h2>", status_code=404)

        # Все события пользователя
        events = await conn.fetch("""
            SELECT event, timestamp, properties
            FROM analytics_events
            WHERE user_id = $1
            ORDER BY timestamp ASC
        """, user_id)

        # Документы пользователя
        docs = await conn.fetch("""
            SELECT id, title, uploaded_at, confirmed, document_type
            FROM documents
            WHERE user_id = $1
            ORDER BY uploaded_at ASC
        """, user_id)

        # Лимиты
        limits = await conn.fetchrow("""
            SELECT subscription_type, documents_left, gpt4o_queries_left, subscription_expires_at
            FROM user_limits WHERE user_id = $1
        """, user_id)

    finally:
        await release_db_connection(conn)

    # Строим воронку автоматически
    events_list = [dict(e) for e in events]
    event_names = [e["event"] for e in events_list]

    funnel = [
        {"key": "dashboard_open",         "label": "Открыл кабинет", "icon": "🏠"},
        {"key": "documents_page_opened", "label": "Открыл страницу документов", "icon": "📂"},
        {"key": "upload_success",         "label": "Загрузил документ", "icon": "📄"},
        {"key": "summary_viewed",         "label": "Открыл подробный разбор", "icon": "👁"},
        {"key": "summary_scrolled",       "label": "Пролистал сводку", "icon": "📜"},
        {"key": "chat_doc_opened",        "label": "Чат по документу", "icon": "💬"},
        {"key": "general_chat_message_sent", "label": "Написал в чат", "icon": "🤖"},
        {"key": "subscription_opened",    "label": "Смотрел подписки", "icon": "💳"},
    ]

    for step in funnel:
        step["done"] = step["key"] in event_names

    # Статус пользователя
    if "upload_success" not in event_names:
        status = ("❌", "Не загрузил документ", "red")
    elif "summary_viewed" not in event_names:
        status = ("⚠️", "Загрузил, но не открыл сводку", "orange")
    elif "chat_doc_opened" not in event_names and "general_chat_message_sent" not in event_names:
        status = ("⚠️", "Читал сводку, но не сделал следующий шаг", "orange")
    else:
        status = ("✅", "Активный пользователь", "green")

    # Тайминги между ключевыми событиями
    timings = {}
    ts_map = {}
    for e in events_list:
        if e["event"] not in ts_map:
            ts_map[e["event"]] = e["timestamp"]

    def diff_seconds(a, b):
        if a in ts_map and b in ts_map:
            delta = (ts_map[b] - ts_map[a]).total_seconds()
            if delta >= 0:
                return int(delta)
        return None

    timings["reg_to_upload"] = diff_seconds("registration_completed", "upload_success")
    timings["upload_to_summary"] = diff_seconds("upload_success", "summary_viewed")
    timings["summary_to_chat"] = diff_seconds("summary_viewed", "chat_doc_opened")

    def fmt_seconds(s):
        if s is None:
            return "—"
        if s < 60:
            return f"{s} сек"
        if s < 3600:
            return f"{s // 60} мин {s % 60} сек"
        return f"{s // 3600} ч {(s % 3600) // 60} мин"

    context = {
        "request": request,
        "user": dict(user),
        "events": events_list,
        "docs": [dict(d) for d in docs],
        "limits": dict(limits) if limits else {},
        "funnel": funnel,
        "status": status,
        "timings": timings,
        "fmt_seconds": fmt_seconds,
        "secret": request.session.get("admin_secret", "")
    }
    return templates.TemplateResponse("ops_user.html", context)