# ============================================================
#  app/handlers/reactions.py — реакции на ответы
#  • ❤️🔥😍 реакция автора на ответ
#  • /myreactions — свои реакции
# ============================================================
import logging
import aiosqlite
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..database import get_question, add_reaction, pool
from ..config import OWNER_IDS

log = logging.getLogger("reactions")
router = Router()


# ============================================================
#  ❤️🔥😍 Реакция на ответ
# ============================================================
@router.callback_query(F.data.startswith("react:"))
async def cb_react(c: CallbackQuery, bot: Bot):
    try:
        parts = c.data.split(":")
        qid = int(parts[1])
        emoji = parts[2] if len(parts) > 2 else "❤️"
    except (IndexError, ValueError):
        return await c.answer("Ошибка", show_alert=True)

    q = await get_question(qid)
    if not q:
        return await c.answer("Вопрос не найден", show_alert=True)

    # только автор вопроса может ставить реакцию
    if c.from_user.id != q["sender_id"]:
        return await c.answer("Это не твой ответ 🙂", show_alert=True)

    # антиспам: одна реакция на вопрос от одного пользователя
    async with pool.acquire() as conn:
        already = await conn.fetchval(
            "SELECT 1 FROM reactions_log WHERE question_id=$1 AND user_id=$2",
            qid, c.from_user.id,
        )
        if already:
            return await c.answer("Ты уже реагировал 🙂", show_alert=True)

        await conn.execute(
            "INSERT INTO reactions_log (question_id, user_id, emoji) "
            "VALUES ($1,$2,$3)",
            qid, c.from_user.id, emoji,
        )

    await add_reaction(qid)

    # уведомить владельцев
    snippet = (q["question"] or "").replace("\n", " ")[:60]
    for oid in OWNER_IDS:
        try:
            await bot.send_message(
                oid,
                f"{emoji} <b>Реакция на #{qid}</b>\n\n<i>{snippet}</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass

    await c.answer(f"Спасибо! {emoji}")


# ============================================================
#  📊 /myreactions — свои реакции автора
# ============================================================
@router.message(Command("myreactions"))
async def cmd_my_reactions(message: Message):
    uid = message.from_user.id
    from ..database import DB_PATH

    async with aiosqlite.connect(DB_PATH) as c:
        c.row_factory = aiosqlite.Row
        async with c.execute("""
            SELECT q.id, q.question, q.reactions, r.emoji
            FROM questions q
            JOIN reactions_log r ON r.question_id = q.id
            WHERE r.user_id = ?
            ORDER BY q.id DESC
            LIMIT 10
        """, (uid,)) as cur:
            rows = await cur.fetchall()

    if not rows:
        return await message.answer(
            "📭 У тебя пока нет реакций.\n"
            "Когда получишь ответ на вопрос — можешь поставить ❤️ / 🔥 / 😍"
        )

    lines = ["📊 <b>Твои реакции</b>\n"]
    for r in rows:
        snippet = (r["question"] or "").replace("\n", " ")[:50]
        lines.append(
            f"{r['emoji']} <b>#{r['id']}</b> "
            f"(всего {r['reactions']}❤️)\n"
            f"<i>{snippet}</i>\n"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
