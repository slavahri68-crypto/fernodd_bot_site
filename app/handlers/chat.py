# ============================================================
#  app/handlers/chat.py — анонимный чат (сторона пользователя)
#  • userchat:{qid} — начать/продолжить чат
#  • /stop           — выйти из чата
#  • восстановление FSM после перезапуска
# ============================================================
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..config import is_owner, OWNER_IDS
from ..database import (
    get_question, get_chat, close_chat,
    add_chat_msg, set_setting, get_setting, pool,
)
from ..i18n import t
from .user import UserStates

log = logging.getLogger("chat")
router = Router()


# ============================================================
#  Автор нажимает «💬 Чат» под ответом
# ============================================================
@router.callback_query(F.data.startswith("userchat:"))
async def cb_user_start_chat(c: CallbackQuery, state: FSMContext, bot: Bot):
    qid = int(c.data.split(":")[1])
    q = await get_question(qid)
    if not q:
        return await c.answer("Вопрос не найден", show_alert=True)
    if q["sender_id"] != c.from_user.id:
        return await c.answer("Это не твой вопрос 🙂", show_alert=True)

    # ищем активный чат по этому вопросу
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM chats "
            "WHERE question_id=$1 AND closed=FALSE "
            "ORDER BY id DESC LIMIT 1",
            qid,
        )

    if not row:
        return await c.answer(
            "Чат ещё не открыт владельцем. Дождись ответа 🙂",
            show_alert=True,
        )

    chat_id = row["id"]
    await state.set_state(UserStates.chatting)
    await state.update_data(chat_id=chat_id, qid=qid)
    await set_setting(f"user_chat_{c.from_user.id}", str(chat_id))

    await c.message.answer(
        await t(c.from_user.id, "chat_started"),
        parse_mode="HTML",
    )
    for oid in OWNER_IDS:
        try:
            await bot.send_message(oid, f"💬 Автор вопроса #{qid} открыл чат.")
        except Exception:
            pass
    await c.answer()


# ============================================================
#  /stop — выйти из чата
# ============================================================
@router.message(Command("stop"))
async def cmd_stop_chat(message: Message, state: FSMContext, bot: Bot):
    if is_owner(message.from_user.id):
        return
    data = await state.get_data()
    chat_id = data.get("chat_id")
    if chat_id:
        await close_chat(chat_id)
        await set_setting(f"user_chat_{message.from_user.id}", "")
        for oid in OWNER_IDS:
            try:
                await bot.send_message(oid, f"🚪 Автор закрыл чат #{chat_id}.")
            except Exception:
                pass
    await state.clear()
    await message.answer("🚪 Чат завершён.")


# ============================================================
#  Восстановление состояния после перезапуска бота
# ============================================================
@router.message(F.text)
async def restore_chat_state(message: Message, state: FSMContext, bot: Bot):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return

    chat_id_str = await get_setting(f"user_chat_{message.from_user.id}", "")
    if not chat_id_str:
        return

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return

    chat = await get_chat(chat_id)
    if not chat or chat["closed"]:
        await set_setting(f"user_chat_{message.from_user.id}", "")
        return

    await state.set_state(UserStates.chatting)
    await state.update_data(chat_id=chat_id, qid=chat["question_id"])

    text = message.text.strip()
    if not text:
        return

    await add_chat_msg(chat_id, "user", text)
    for oid in OWNER_IDS:
        try:
            await bot.send_message(
                oid,
                await t(oid, "chat_msg_user",
                        id=chat["question_id"], text=text),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("restore chat → %s: %s", oid, e)

    await message.answer("✅ Отправлено")