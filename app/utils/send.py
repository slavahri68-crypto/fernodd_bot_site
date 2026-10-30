# ============================================================
#  app/utils/send.py — отправка вопросов владельцам
# ============================================================
from aiogram import Bot
from ..database import get_question, set_owner_msg
from ..keyboards import question_kb
from ..config import OWNER_IDS


def fmt_question(q):
    status = "✅" if q["is_answered"] else "⏳"
    media = f"\n📎 [{q['media_type']}]" if q["media_type"] else ""
    react = f"  {q['reactions']}❤️" if q["reactions"] else ""
    return (
        f"{status} <b>Вопрос #{q['id']}</b>{react}\n"
        f"🕒 {q['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"💬 {q['question'] or '(медиа)'}{media}"
    )


async def send_question_to_owner(bot: Bot, qid):
    q = await get_question(qid)
    if not q:
        return
    text = fmt_question(q)
    kb = question_kb(qid, q["is_answered"])
    sent = None
    for oid in OWNER_IDS:
        try:
            mt = q["media_type"]
            if mt == "photo":
                s = await bot.send_photo(oid, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
            elif mt == "video":
                s = await bot.send_video(oid, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
            elif mt == "voice":
                s = await bot.send_voice(oid, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
            elif mt == "document":
                s = await bot.send_document(oid, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
            elif mt == "sticker":
                s = await bot.send_message(oid, text, reply_markup=kb, parse_mode="HTML")
                await bot.send_sticker(oid, q["media_file_id"])
            else:
                s = await bot.send_message(oid, text, reply_markup=kb, parse_mode="HTML")
            sent = s
        except Exception:
            pass
    if sent:
        await set_owner_msg(qid, sent.message_id)