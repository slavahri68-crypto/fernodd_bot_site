# ============================================================
#  app/handlers/user.py — ЧАСТЬ 1/3
#  Импорты · FSM · /start · хелпер приёма вопроса
# ============================================================
import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..config import is_owner
from ..database import (
    upsert_user, save_question, get_setting,
    get_chat, add_chat_msg,
)
from ..i18n import t
from ..utils.send import send_question_to_owner

log = logging.getLogger("user")
router = Router()


class UserStates(StatesGroup):
    chatting = State()


# ---------- /start ----------
@router.message(CommandStart())
async def user_start(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    await upsert_user(message.from_user)
    await state.clear()
    await message.answer(
        await t(message.from_user.id, "start_user"),
        parse_mode="HTML",
    )


# ---------- Хелпер приёма вопроса ----------
async def _handle_question(message: Message, mtype=None, file_id=None):
    await upsert_user(message.from_user)
    text = message.text or message.caption or "(без текста)"
    qid = await save_question(message.from_user, text, mtype, file_id)

    try:
        await send_question_to_owner(message.bot, qid)
    except Exception as e:
        log.exception("send_question_to_owner #%s: %s", qid, e)

    await message.answer(
        await t(message.from_user.id, "sent", id=qid),
        parse_mode="HTML",
    )

    ar = await get_setting("autoreply", "")
    if ar:
        await message.answer(f"🤖 {ar}")

# ============================================================
#  app/handlers/user.py — ЧАСТЬ 2/3
#  Приём текста, медиа, стикеров
# ============================================================


@router.message(F.text)
async def user_text(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    if not message.text.strip():
        return
    await _handle_question(message)


@router.message(F.photo)
async def user_photo(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    await _handle_question(message, "photo", message.photo[-1].file_id)


@router.message(F.video)
async def user_video(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    await _handle_question(message, "video", message.video.file_id)


@router.message(F.voice)
async def user_voice(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    await _handle_question(message, "voice", message.voice.file_id)


@router.message(F.document)
async def user_document(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    await _handle_question(message, "document", message.document.file_id)


@router.message(F.sticker)
async def user_sticker(message: Message, state: FSMContext):
    if is_owner(message.from_user.id):
        return
    if await state.get_state() is not None:
        return
    await _handle_question(message, "sticker", message.sticker.file_id)

# ============================================================
#  app/handlers/user.py — ЧАСТЬ 3/3
#  Сообщения в активном анонимном чате
# ============================================================
from ..config import OWNER_IDS


@router.message(UserStates.chatting, F.text)
async def user_chat_message(message: Message, state: FSMContext, bot: Bot):
    if is_owner(message.from_user.id):
        return

    data = await state.get_data()
    chat_id = data.get("chat_id")
    qid = data.get("qid")
    if not chat_id:
        await state.clear()
        return await user_text(message, state)

    chat = await get_chat(chat_id)
    if not chat or chat["closed"]:
        await state.clear()
        await message.answer(await t(message.from_user.id, "chat_closed"))
        return

    text = message.text.strip()
    if not text:
        return

    await add_chat_msg(chat_id, "user", text)
    for oid in OWNER_IDS:
        try:
            await bot.send_message(
                oid,
                await t(oid, "chat_msg_user", id=qid, text=text),
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("chat → owner %s: %s", oid, e)

    await message.answer("✅ Отправлено")