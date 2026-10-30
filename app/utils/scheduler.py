# ============================================================
#  app/utils/scheduler.py — фоновые задачи
#  • отложенные ответы
#  • ежедневный дайджест (09:00)
#  • напоминания о неотвеченных (>24ч)
# ============================================================
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

from ..config import OWNER_IDS
from ..database import (
    due_scheduled, get_question, save_answer,
    get_setting, set_setting, pool, stats, list_questions,
)
from ..i18n import t
from ..keyboards import reaction_kb

log = logging.getLogger("scheduler")

# ---------------- настройки ----------------
DELAYED_CHECK       = 30        # сек — проверка отложенных
DIGEST_CHECK        = 60 * 5    # сек — проверка «пора ли дайджест»
REMINDER_CHECK      = 60 * 10   # сек — проверка напоминаний
DIGEST_HOUR         = 9
DIGEST_MINUTE       = 0
REMIND_AFTER_HOURS  = 24
REMIND_COOLDOWN_HOURS = 12


# ============================================================
#  1. Отложенные ответы
# ============================================================
async def _process_delayed(bot: Bot):
    try:
        rows = await due_scheduled()
        for r in rows:
            q = await get_question(r["qid"])
            if not q:
                continue
            await save_answer(r["qid"], r["answer"])
            try:
                await bot.send_message(
                    q["sender_id"],
                    await t(q["sender_id"], "answer_user",
                            id=r["qid"], q=q["question"], a=r["answer"]),
                    parse_mode="HTML",
                    reply_markup=reaction_kb(r["qid"]),
                )
                for oid in OWNER_IDS:
                    try:
                        await bot.send_message(
                            oid,
                            f"🕒 Отложенный ответ на #{r['qid']} доставлен."
                        )
                    except Exception:
                        pass
            except Exception as e:
                log.warning("delayed deliver #%s: %s", r["qid"], e)
    except Exception as e:
        log.exception("_process_delayed: %s", e)


# ============================================================
#  2. Ежедневный дайджест (09:00 по времени сервера)
# ============================================================
async def _maybe_send_digest(bot: Bot):
    try:
        now = datetime.now()
        if now.hour != DIGEST_HOUR or now.minute > DIGEST_MINUTE + 4:
            return

        today_key = now.strftime("%Y-%m-%d")
        if await get_setting("last_digest", "") == today_key:
            return

        total, answered, users, today = await stats()
        pending_rows, pending_total = await list_questions(0, unanswered=True)

        text = (
            f"☀️ <b>Доброе утро!</b>\n"
            f"📅 {now:%d.%m.%Y}\n\n"
            f"📊 <b>Сводка</b>\n"
            f"• Всего: <b>{total}</b>\n"
            f"• Отвечено: <b>{answered}</b>\n"
            f"• Ждут: <b>{total - answered}</b>\n"
            f"• За сутки: <b>{today}</b>\n"
            f"• Пользователей: <b>{users}</b>\n"
        )
        if pending_total:
            text += "\n📥 <b>Топ-3 в ожидании:</b>\n"
            for q in pending_rows[:3]:
                snippet = (q["question"] or "(медиа)").replace("\n", " ")[:60]
                text += f"• #{q['id']}: <i>{snippet}</i>\n"

        for oid in OWNER_IDS:
            try:
                await bot.send_message(oid, text, parse_mode="HTML")
            except Exception as e:
                log.warning("digest to %s: %s", oid, e)

        await set_setting("last_digest", today_key)
        log.info("Дайджест отправлен за %s", today_key)
    except Exception as e:
        log.exception("_maybe_send_digest: %s", e)


# ============================================================
#  3. Напоминания о неотвеченных >24ч
# ============================================================
async def _maybe_remind_pending(bot: Bot):
    try:
        async with pool.acquire() as c:
            rows = await c.fetch("""
                SELECT id, question, created_at
                FROM questions
                WHERE is_answered = FALSE
                  AND created_at < NOW() - ($1 || ' hours')::interval
                ORDER BY created_at
                LIMIT 5
            """, str(REMIND_AFTER_HOURS))

        if not rows:
            return

        last = await get_setting("last_remind", "")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt > datetime.now() - timedelta(hours=REMIND_COOLDOWN_HOURS):
                    return
            except ValueError:
                pass

        text = (
            f"⏰ <b>Напоминание</b>\n\n"
            f"Ждут ответа <b>{len(rows)}</b> вопрос(ов) старше "
            f"{REMIND_AFTER_HOURS} ч:\n\n"
        )
        for r in rows:
            snippet = (r["question"] or "(медиа)").replace("\n", " ")[:70]
            text += f"• #{r['id']} — <i>{snippet}</i>\n"

        for oid in OWNER_IDS:
            try:
                await bot.send_message(oid, text, parse_mode="HTML")
            except Exception:
                pass

        await set_setting(
            "last_remind", datetime.now().isoformat(timespec="seconds"))
        log.info("Напоминание отправлено (%d вопросов)", len(rows))
    except Exception as e:
        log.exception("_maybe_remind_pending: %s", e)


# ============================================================
#  4. Циклы + запуск
# ============================================================
async def delayed_loop(bot: Bot):
    log.info("⏱ delayed_loop запущен (интервал %ss)", DELAYED_CHECK)
    while True:
        await _process_delayed(bot)
        await asyncio.sleep(DELAYED_CHECK)


async def digest_loop(bot: Bot):
    log.info("☀️ digest_loop запущен (каждые %ss)", DIGEST_CHECK)
    while True:
        await _maybe_send_digest(bot)
        await asyncio.sleep(DIGEST_CHECK)


async def reminder_loop(bot: Bot):
    log.info("⏰ reminder_loop запущен (каждые %ss)", REMINDER_CHECK)
    while True:
        await _maybe_remind_pending(bot)
        await asyncio.sleep(REMINDER_CHECK)


async def start_all(bot: Bot):
    """Запускает все фоновые задачи параллельно."""
    asyncio.create_task(delayed_loop(bot))
    asyncio.create_task(digest_loop(bot))
    asyncio.create_task(reminder_loop(bot))
    log.info("✅ Все фоновые задачи запущены")