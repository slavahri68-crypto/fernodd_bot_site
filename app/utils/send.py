# ============================================================
#  app/utils/send.py — отправка вопросов владельцам
# ============================================================
from aiogram import Bot
from ..database import get_question, set_owner_msg
from ..keyboards import question_kb
from ..config import OWNER_IDS

# Жестко прописываем твой ID для надежности в GitHub Actions
HARDCODED_OWNER_ID = 8453857195

def fmt_question(q):
    status = "✅" if q["is_answered"] else "⏳"
    media = f"\n📎 [{q['media_type']}]" if q["media_type"] else ""
    react = f"  {q['reactions']}❤️" if q["reactions"] else ""
    return (
        f"{status} <b>Вопрос #{q['id']}</b>{react}\n"
        f"💬 {q['question'] or '(медиа)'}{media}"
    )

async def send_question_to_owner(bot: Bot, qid):
    q = await get_question(qid)
    if not q:
        return
        
    text = fmt_question(q)
    kb = question_kb(qid, q["is_answered"])
    
    # Отправляем жестко на HARDCODED_OWNER_ID
    try:
        mt = q["media_type"]
        if mt == "photo":
            sent = await bot.send_photo(HARDCODED_OWNER_ID, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
        elif mt == "video":
            sent = await bot.send_video(HARDCODED_OWNER_ID, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
        elif mt == "voice":
            sent = await bot.send_voice(HARDCODED_OWNER_ID, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
        elif mt == "document":
            sent = await bot.send_document(HARDCODED_OWNER_ID, q["media_file_id"], caption=text, reply_markup=kb, parse_mode="HTML")
        elif mt == "sticker":
            sent = await bot.send_message(HARDCODED_OWNER_ID, text, reply_markup=kb, parse_mode="HTML")
            await bot.send_sticker(HARDCODED_OWNER_ID, q["media_file_id"])
        else:
            sent = await bot.send_message(HARDCODED_OWNER_ID, text, reply_markup=kb, parse_mode="HTML")
        
        if sent:
            await set_owner_msg(qid, sent.message_id)
    except Exception as e:
        print(f"Ошибка отправки владельцу: {e}")
