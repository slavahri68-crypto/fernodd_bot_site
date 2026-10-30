# ============================================================
#  app/utils/export.py — CSV-экспорт
# ============================================================
import csv
import io
from datetime import datetime

from ..database import pool


async def export_csv() -> bytes:
    async with pool.acquire() as c:
        rows = await c.fetch("""
            SELECT id, question, answer, created_at, answered_at,
                   is_answered, reactions, media_type
            FROM questions ORDER BY id
        """)

    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    w.writerow(["ID", "Вопрос", "Ответ", "Задан", "Отвечен", "Статус", "Реакции", "Медиа"])

    for r in rows:
        w.writerow([
            r["id"],
            (r["question"] or "").replace("\n", " ").strip(),
            (r["answer"] or "").replace("\n", " ").strip(),
            _fmt(r["created_at"]),
            _fmt(r["answered_at"]),
            "✅" if r["is_answered"] else "⏳",
            r["reactions"] or 0,
            r["media_type"] or "",
        ])

    return buf.getvalue().encode("utf-8-sig")


def _fmt(dt):
    if not dt:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)