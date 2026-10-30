# ============================================================
#  app/keyboards.py — все клавиатуры
# ============================================================
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from .i18n import t
from .config import WEBAPP_URL


async def owner_menu(uid):
    rows = [
        [InlineKeyboardButton(text=await t(uid, "btn_inbox"), callback_data="list:0:unans")],
        [InlineKeyboardButton(text=await t(uid, "btn_all"), callback_data="list:0:all"),
         InlineKeyboardButton(text=await t(uid, "btn_top"), callback_data="top")],
        [InlineKeyboardButton(text=await t(uid, "btn_stats"), callback_data="stats"),
         InlineKeyboardButton(text=await t(uid, "btn_chart"), callback_data="chart")],
        [InlineKeyboardButton(text=await t(uid, "btn_export"), callback_data="export"),
         InlineKeyboardButton(text=await t(uid, "btn_broadcast"), callback_data="broadcast")],
        [InlineKeyboardButton(text=await t(uid, "btn_lang"), callback_data="lang"),
         InlineKeyboardButton(text=await t(uid, "btn_autoreply"), callback_data="autoreply")],
    ]
    if WEBAPP_URL:
        rows.append([InlineKeyboardButton(
            text=await t(uid, "btn_webapp"),
            web_app=WebAppInfo(url=WEBAPP_URL)
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_kb(qid, answered=False):
    if answered:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Отвечено", callback_data="noop")
        ]])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"reply:{qid}")],
        [InlineKeyboardButton(text="🕒 Позже", callback_data=f"later:{qid}"),
         InlineKeyboardButton(text="💬 Чат", callback_data=f"chatstart:{qid}")],
    ])


def reaction_kb(qid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️", callback_data=f"react:{qid}:❤️"),
            InlineKeyboardButton(text="🔥", callback_data=f"react:{qid}:🔥"),
            InlineKeyboardButton(text="😍", callback_data=f"react:{qid}:😍"),
        ],
        [InlineKeyboardButton(text="💬 Чат с автором", callback_data=f"userchat:{qid}")],
    ])


def list_nav(page, total, mode, menu_label="🔙"):
    pages = max(1, (total + 5 - 1) // 5)
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"list:{page-1}:{mode}"))
    row.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"list:{page+1}:{mode}"))
    return InlineKeyboardMarkup(inline_keyboard=[
        row, [InlineKeyboardButton(text=menu_label, callback_data="menu")]
    ])