# ============================================================
#  app/handlers/user.py — приём вопросов
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

async def _handle_question(message: Message, mtype=None, file_id=None):
    await upsert_user(message.from_user)
    text = message.text or message.caption or "(без текста)"
    
    try:
        qid = await save_question(message.from_user, text, mtype, file_id)
        await send_question_to_owner(message.bot, qid)
        await message.answer(
            await t(message.from_user.id, "sent", id=qid),
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception(f"Ошибка при сохранении/отправке: {e}")
        # Если база данных GitHub Actions глючит, отправляем в обход неё
        try:
            from ..utils.send import HARDCODED_OWNER_ID
            await message.bot.send_message(HARDCODED_OWNER_ID, f"⚠️ Вопрос (без БД): {text}")
        except:
            pass

    ar = await get_setting("autoreply", "")
    if ar:
        await message.answer(f"🤖 {ar}")

@router.message(F.text)
async def user_text(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    if message.text.strip():
        await _handle_question(message)

@router.message(F.photo)
async def user_photo(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    await _handle_question(message, "photo", message.photo[-1].file_id)

@router.message(F.video)
async def user_video(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    await _handle_question(message, "video", message.video.file_id)

@router.message(F.voice)
async def user_voice(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    await _handle_question(message, "voice", message.voice.file_id)

@router.message(F.document)
async def user_document(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    await _handle_question(message, "document", message.document.file_id)

@router.message(F.sticker)
async def user_sticker(message: Message, state: FSMContext):
    if is_owner(message.from_user.id) or await state.get_state() is not None:
        return
    await _handle_question(message, "sticker", message.sticker.file_id)

@router.message(UserStates.chatting, F.text)
async def user_chat_message(message: Message, state: FSMContext, bot: Bot):
    # (оставляем как было, если чат настроен)
    pass
