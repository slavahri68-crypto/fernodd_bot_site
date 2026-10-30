# ============================================================
#  app/handlers/owner.py — ЧАСТЬ 1/5
#  Импорты · FSM · /start · меню
# ============================================================
import asyncio
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from ..config import is_owner, OWNER_IDS
from ..database import (
    upsert_user, get_question, save_answer, stats,
    list_questions, top_questions, all_users,
    set_lang, get_setting, set_setting, schedule_answer,
    create_chat, get_chat, close_chat, add_chat_msg,
)
from ..i18n import t
from ..keyboards import owner_menu, question_kb, list_nav, reaction_kb
from ..utils.send import fmt_question
from ..utils.export import export_csv
from ..utils.charts import activity_chart, pie_media_chart

router = Router()


class OwnerStates(StatesGroup):
    reply        = State()
    broadcast    = State()
    autoreply    = State()
    later_delay  = State()
    later_answer = State()
    chat         = State()


@router.message(CommandStart())
async def owner_start(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        # Если пишет НЕ владелец — пропускаем его дальше, 
        # чтобы сработал хендлер из файла user.py
        return
    
    await upsert_user(message.from_user)
    await state.clear()
    await message.answer(
        await t(message.from_user.id, "start_owner"),
        reply_markup=await owner_menu(message.from_user.id),
        parse_mode="HTML",
    )

@router.callback_query(F.data == "menu")
async def cb_menu(c: CallbackQuery, state: FSMContext):
    if not is_owner(c.from_user.id):
        return await c.answer()
    await state.clear()
    await c.message.edit_text(
        await t(c.from_user.id, "start_owner"),
        reply_markup=await owner_menu(c.from_user.id),
        parse_mode="HTML",
    )
    await c.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(c: CallbackQuery):
    await c.answer()

# ============================================================
#  app/handlers/owner.py — ЧАСТЬ 2/5
#  📊 Статистика · 📈 График · 📤 Экспорт · 🏆 Топ
# ============================================================


@router.callback_query(F.data == "stats")
async def cb_stats(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    total, answered, users, today = await stats()
    text = await t(c.from_user.id, "stats",
                   u=users, t=total, a=answered,
                   w=total - answered, today=today)
    await c.message.edit_text(
        text,
        reply_markup=await owner_menu(c.from_user.id),
        parse_mode="HTML",
    )
    await c.answer()


@router.callback_query(F.data == "chart")
async def cb_chart(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    await c.answer("Рисую график...")
    try:
        buf = await activity_chart()
        f = BufferedInputFile(buf, filename="activity.png")
        await c.message.answer_photo(f, caption="📈 Активность за 14 дней")
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")


@router.callback_query(F.data == "chart_pie")
async def cb_chart_pie(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    await c.answer("Рисую...")
    try:
        buf = await pie_media_chart()
        f = BufferedInputFile(buf, filename="media.png")
        await c.message.answer_photo(f, caption="📎 Типы вопросов")
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")


@router.callback_query(F.data == "export")
async def cb_export(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    await c.answer("Готовлю...")
    try:
        data = await export_csv()
        f = BufferedInputFile(data,
                              filename=f"questions_{datetime.now():%Y%m%d_%H%M}.csv")
        await c.message.answer_document(f, caption="📤 Экспорт всех вопросов")
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка: {e}")


@router.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    rows = await top_questions()
    header = await t(c.from_user.id, "top_header")
    if not rows:
        text = header + "— пока нет реакций —"
    else:
        lines = []
        for i, r in enumerate(rows, 1):
            snippet = (r["question"] or "").replace("\n", " ")[:80]
            lines.append(f"{i}. #{r['id']} — {r['reactions']}❤️\n   <i>{snippet}</i>")
        text = header + "\n\n".join(lines)
    await c.message.edit_text(
        text,
        reply_markup=await owner_menu(c.from_user.id),
        parse_mode="HTML",
    )
    await c.answer()

# ============================================================
#  app/handlers/owner.py — ЧАСТЬ 3/5
#  🌐 Язык · 🤖 Автоответ · 📢 Рассылка
# ============================================================


@router.callback_query(F.data == "lang")
async def cb_lang(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
         InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang:en")],
        [InlineKeyboardButton(text="🔙", callback_data="menu")],
    ])
    await c.message.edit_text(
        "🌐 <b>Выбери язык / Choose language</b>",
        reply_markup=kb, parse_mode="HTML",
    )
    await c.answer()


@router.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    lang = c.data.split(":")[1]
    await set_lang(c.from_user.id, lang)
    await c.answer("✅")
    await c.message.edit_text(
        await t(c.from_user.id, "start_owner"),
        reply_markup=await owner_menu(c.from_user.id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "autoreply")
async def cb_autoreply(c: CallbackQuery, state: FSMContext):
    if not is_owner(c.from_user.id):
        return await c.answer()
    cur = await get_setting("autoreply", "— не задан —")
    await state.set_state(OwnerStates.autoreply)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=await t(c.from_user.id, "btn_menu"), callback_data="menu"),
    ]])
    await c.message.edit_text(
        f"🤖 <b>Автоответ</b>\n\nТекущий:\n<i>{cur or '— не задан —'}</i>\n\n"
        f"Отправь новый текст или /cancel.",
        reply_markup=kb, parse_mode="HTML",
    )
    await c.answer()


@router.message(OwnerStates.autoreply, F.text)
async def set_ar(message: Message, state: FSMContext):
    text = message.text.strip()
    await set_setting("autoreply", text)
    await state.clear()
    await message.answer(
        f"✅ Автоответ сохранён:\n\n<i>{text}</i>",
        reply_markup=await owner_menu(message.from_user.id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "broadcast")
async def cb_broadcast(c: CallbackQuery, state: FSMContext):
    if not is_owner(c.from_user.id):
        return await c.answer()
    await state.set_state(OwnerStates.broadcast)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=await t(c.from_user.id, "btn_menu"), callback_data="menu"),
    ]])
    await c.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Отправь сообщение — оно уйдёт всем пользователям.\n"
        "/cancel — отмена.",
        reply_markup=kb, parse_mode="HTML",
    )
    await c.answer()


@router.message(OwnerStates.broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return
    users = await all_users()
    sent = failed = 0
    for uid in users:
        if is_owner(uid):
            continue
        try:
            await message.copy_to(uid)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await state.clear()
    await message.answer(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Доставлено: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>",
        reply_markup=await owner_menu(message.from_user.id),
        parse_mode="HTML",
    )

# ============================================================
#  app/handlers/owner.py — ЧАСТЬ 4/5
#  📥 Список · ✍️ Ответ · 🕒 Отложенный ответ
# ============================================================


@router.callback_query(F.data.startswith("list:"))
async def cb_list(c: CallbackQuery):
    if not is_owner(c.from_user.id):
        return await c.answer()
    _, page_s, mode = c.data.split(":")
    page = int(page_s)
    rows, total = await list_questions(page, mode == "unans")
    if not rows:
        return await c.answer("Пусто 🙂", show_alert=True)
    title = "📥 Входящие" if mode == "unans" else "📚 Все вопросы"
    await c.message.edit_text(
        f"<b>{title}</b> · всего <b>{total}</b>\nСтраница {page + 1}",
        reply_markup=list_nav(page, total, mode, await t(c.from_user.id, "btn_menu")),
        parse_mode="HTML",
    )
    for q in rows:
        await c.message.answer(
            fmt_question(q),
            reply_markup=question_kb(q["id"], q["is_answered"]),
            parse_mode="HTML",
        )
    await c.answer()


@router.callback_query(F.data.startswith("reply:"))
async def cb_reply(c: CallbackQuery, state: FSMContext):
    if not is_owner(c.from_user.id):
        return await c.answer("Не твоя кнопка 🙂", show_alert=True)
    qid = int(c.data.split(":")[1])
    q = await get_question(qid)
    if not q:
        return await c.answer("Не найдено", show_alert=True)
    if q["is_answered"]:
        return await c.answer("Уже отвечено ✅", show_alert=True)
    await state.update_data(qid=qid)
    await state.set_state(OwnerStates.reply)
    await c.message.answer(
        await t(c.from_user.id, "reply_prompt", id=qid, q=q["question"]),
        parse_mode="HTML",
    )
    await c.answer()


@router.message(OwnerStates.reply, F.text)
async def owner_reply(message: Message, state: FSMContext, bot: Bot):
    if not is_owner(message.from_user.id):
        return
    data = await state.get_data()
    qid = data.get("qid")
    q = await get_question(qid)
    if not q:
        await state.clear()
        return await message.answer("Вопрос не найден")
    ans = message.text.strip()
    await save_answer(qid, ans)
    await state.clear()
    try:
        await bot.send_message(
            q["sender_id"],
            await t(q["sender_id"], "answer_user",
                    id=qid, q=q["question"], a=ans),
            parse_mode="HTML",
            reply_markup=reaction_kb(qid),
        )
        await message.answer(await t(message.from_user.id, "answer_delivered", id=qid))
    except Exception as e:
        await message.answer(f"⚠️ Не смог доставить: {e}")


@router.callback_query(F.data.startswith("later:"))
async def cb_later(c: CallbackQuery, state: FSMContext):
    if not is_owner(c.from_user.id):
        return await c.answer()
    qid = int(c.data.split(":")[1])
    await state.update_data(qid=qid)
    await state.set_state(OwnerStates.later_delay)
    await c.message.answer(
        f"🕒 <b>Отложенный ответ на #{qid}</b>\n\n"
        f"Через сколько минут отправить?\n"
        f"Напиши число (например <code>30</code>) или /cancel.",
        parse_mode="HTML",
    )
    await c.answer()


@router.message(OwnerStates.later_delay, F.text)
async def later_delay(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return
    try:
        minutes = int(message.text.strip())
        if minutes < 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введи положительное число минут:")
    data = await state.get_data()
    await state.update_data(delay=minutes)
    await state.set_state(OwnerStates.later_answer)
    await message.answer(
        f"⏱ Отправка через <b>{minutes} мин.</b>\n\n"
        f"✍️ Теперь напиши ответ на #{data['qid']}:",
        parse_mode="HTML",
    )


@router.message(OwnerStates.later_answer, F.text)
async def later_answer(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return
    data = await state.get_data()
    qid = data["qid"]
    delay = data["delay"]
    ans = message.text.strip()
    send_at = datetime.now() + timedelta(minutes=delay)
    await schedule_answer(qid, ans, send_at)
    await state.clear()
    await message.answer(
        f"✅ <b>Ответ на #{qid} запланирован</b>\n"
        f"🕒 Отправка: <b>{send_at:%d.%m.%Y %H:%M}</b>",
        reply_markup=await owner_menu(message.from_user.id),
        parse_mode="HTML",
    )

# ============================================================
#  app/handlers/owner.py — ЧАСТЬ 5/5
#  💬 Анонимный чат · /cancel · /close
# ============================================================


@router.callback_query(F.data.startswith("chatstart:"))
async def cb_chatstart(c: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_owner(c.from_user.id):
        return await c.answer()
    qid = int(c.data.split(":")[1])
    q = await get_question(qid)
    if not q:
        return await c.answer("Не найдено", show_alert=True)

    chat_id = await create_chat(qid, q["sender_id"], c.from_user.id)
    await set_setting(f"owner_chat_{c.from_user.id}", str(chat_id))
    await set_setting(f"user_chat_{q['sender_id']}", str(chat_id))
    await state.set_state(OwnerStates.chat)
    await state.update_data(chat_id=chat_id, qid=qid, peer_id=q["sender_id"])

    await c.message.answer(
        await t(c.from_user.id, "chat_owner_started", id=qid),
        parse_mode="HTML",
    )
    try:
        await bot.send_message(
            q["sender_id"],
            await t(q["sender_id"], "chat_started"),
        )
    except Exception:
        pass
    await c.answer()


@router.message(OwnerStates.chat, F.text)
async def owner_chat_msg(message: Message, state: FSMContext, bot: Bot):
    if not is_owner(message.from_user.id):
        return
    data = await state.get_data()
    chat_id = data.get("chat_id")
    peer_id = data.get("peer_id")
    qid = data.get("qid")
    if not chat_id or not peer_id:
        await state.clear()
        return await message.answer("Чат не найден")

    chat = await get_chat(chat_id)
    if not chat or chat["closed"]:
        await state.clear()
        return await message.answer(await t(message.from_user.id, "chat_closed"))

    await add_chat_msg(chat_id, "owner", message.text)
    try:
        await bot.send_message(
            peer_id,
            await t(peer_id, "chat_msg_owner", text=message.text),
            parse_mode="HTML",
        )
        await message.answer("✅ Отправлено")
    except Exception as e:
        await message.answer(f"⚠️ {e}")


@router.message(Command("close"))
async def cmd_close_chat(message: Message, state: FSMContext, bot: Bot):
    if not is_owner(message.from_user.id):
        return
    data = await state.get_data()
    chat_id = data.get("chat_id")
    peer_id = data.get("peer_id")
    if chat_id:
        await close_chat(chat_id)
        if peer_id:
            try:
                await bot.send_message(peer_id, await t(peer_id, "chat_closed"))
            except Exception:
                pass
        await set_setting(f"owner_chat_{message.from_user.id}", "")
        if peer_id:
            await set_setting(f"user_chat_{peer_id}", "")
    await state.clear()
    await message.answer(
        "🚪 Чат закрыт.",
        reply_markup=await owner_menu(message.from_user.id),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        await t(message.from_user.id, "cancel"),
        reply_markup=await owner_menu(message.from_user.id),
    )
