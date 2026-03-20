# webapp/email_scheduler.py
# ⏰ Cron-планировщик для отправки писем из email_queue

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db_postgresql import get_db_connection, release_db_connection
from webapp.email_service import send_email
from webapp.email_templates import get_email_content

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def process_email_queue():
    """Обрабатывает pending письма из email_queue"""
    conn = await get_db_connection()
    try:
        # Берём до 50 писем которые уже можно отправить
        rows = await conn.fetch("""
            SELECT eq.id, eq.user_id, eq.email_type,
                   u.email, u.language
            FROM email_queue eq
            JOIN users u ON u.user_id = eq.user_id
            WHERE eq.status = 'pending'
              AND eq.send_after <= now()
            ORDER BY eq.send_after
            LIMIT 50
        """)

        if not rows:
            return

        logger.info(f"Email queue: processing {len(rows)} items")

        for row in rows:
            queue_id = row["id"]
            user_id = row["user_id"]
            email_type = row["email_type"]
            to_email = row["email"]
            lang = row["language"] or "en"

            # Пользователь без email — отменяем
            if not to_email:
                await _set_status(conn, queue_id, "cancelled")
                continue

            # Для reminder писем: проверяем загрузил ли уже документ
            if email_type in ("reminder_24h", "reminder_4d"):
                doc_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM documents WHERE user_id = $1 AND confirmed = true",
                    user_id
                )
                if doc_count > 0:
                    await _set_status(conn, queue_id, "cancelled")
                    continue

            # Получаем контент письма
            content = get_email_content(email_type, lang)
            if not content:
                await _set_status(conn, queue_id, "cancelled")
                continue

            # Отправляем
            ok = await send_email(to_email, content["subject"], content["html"])
            await _set_status(conn, queue_id, "sent" if ok else "pending")

    except Exception as e:
        logger.error(f"Email queue processing error: {type(e).__name__}")
    finally:
        await release_db_connection(conn)


async def _set_status(conn, queue_id: int, status: str):
    await conn.execute(
        "UPDATE email_queue SET status = $1 WHERE id = $2",
        status, queue_id
    )


def start_email_scheduler():
    """Запускает планировщик. Вызывать из lifespan app.py"""
    scheduler.add_job(
        process_email_queue,
        trigger=IntervalTrigger(hours=12),
        id="email_queue_job",
        replace_existing=True,
        max_instances=1,  # Не запускать параллельно
    )
    scheduler.start()
    logger.info("Email scheduler started (every 12 hours)")


def stop_email_scheduler():
    """Останавливает планировщик. Вызывать из lifespan при shutdown"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Email scheduler stopped")