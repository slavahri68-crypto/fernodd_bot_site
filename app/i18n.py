# ============================================================
#  app/i18n.py — локализация RU / EN
# ============================================================
STRINGS = {
    "ru": {
        "start_user": "👋 <b>Привет!</b>\n\nНапиши вопрос — я передам хозяину анонимно.\nОтвет придёт сюда 📩",
        "start_owner": "👑 <b>Панель владельца</b>\nВыбирай действие 👇",
        "sent": "✅ <b>Вопрос #{id}</b> отправлен. Ответ придёт сюда.",
        "answer_delivered": "✅ Ответ на #{id} доставлен.",
        "reply_prompt": "✍️ <b>Ответ на #{id}</b>\n\n❓ {q}\n\nПиши ответ. /cancel — отмена.",
        "stats": "📊 <b>Статистика</b>\n\n👥 Пользователей: {u}\n💬 Вопросов: {t}\n✅ Отвечено: {a}\n⏳ Ждут: {w}\n🔥 Сегодня: {today}",
        "top_header": "🏆 <b>Топ по реакциям</b>\n\n",
        "cancel": "❌ Отменено.",
        "answer_user": "📬 <b>Ответ на #{id}</b>\n\n❓ {q}\n\n💌 <b>{a}</b>",
        "chat_started": "💬 Анонимный чат с хозяином начат! Пиши сообщения.",
        "chat_owner_started": "💬 Ты начал чат с автором #{id}. Всё, что напишешь — уйдёт ему анонимно.",
        "chat_msg_user": "💬 <b>От автора #{id}:</b>\n{text}",
        "chat_msg_owner": "💬 <b>От хозяина:</b>\n{text}",
        "chat_closed": "🚪 Чат закрыт.",
        "btn_menu": "🔙 В меню",
        "btn_inbox": "📥 Входящие",
        "btn_all": "📚 Все",
        "btn_top": "🏆 Топ",
        "btn_stats": "📊 Статистика",
        "btn_chart": "📈 График",
        "btn_export": "📤 CSV",
        "btn_broadcast": "📢 Рассылка",
        "btn_lang": "🌐 Язык",
        "btn_autoreply": "🤖 Автоответ",
        "btn_webapp": "🌐 Mini App",
        "btn_reply": "✍️ Ответить",
        "btn_later": "🕒 Позже",
        "btn_chat": "💬 Чат",
    },
    "en": {
        "start_user": "👋 <b>Hi!</b>\n\nSend a question — I'll pass it to the owner.\nAnswer will come here 📩",
        "start_owner": "👑 <b>Owner panel</b>\nPick an action 👇",
        "sent": "✅ <b>Question #{id}</b> sent. Answer will arrive here.",
        "answer_delivered": "✅ Answer #{id} delivered.",
        "reply_prompt": "✍️ <b>Reply to #{id}</b>\n\n❓ {q}\n\nType your answer. /cancel — abort.",
        "stats": "📊 <b>Stats</b>\n\n👥 Users: {u}\n💬 Questions: {t}\n✅ Answered: {a}\n⏳ Pending: {w}\n🔥 Today: {today}",
        "top_header": "🏆 <b>Top by reactions</b>\n\n",
        "cancel": "❌ Canceled.",
        "answer_user": "📬 <b>Answer #{id}</b>\n\n❓ {q}\n\n💌 <b>{a}</b>",
        "chat_started": "💬 Anonymous chat with owner started!",
        "chat_owner_started": "💬 You started a chat with sender #{id}.",
        "chat_msg_user": "💬 <b>From sender #{id}:</b>\n{text}",
        "chat_msg_owner": "💬 <b>From owner:</b>\n{text}",
        "chat_closed": "🚪 Chat closed.",
        "btn_menu": "🔙 Menu",
        "btn_inbox": "📥 Inbox",
        "btn_all": "📚 All",
        "btn_top": "🏆 Top",
        "btn_stats": "📊 Stats",
        "btn_chart": "📈 Chart",
        "btn_export": "📤 CSV",
        "btn_broadcast": "📢 Broadcast",
        "btn_lang": "🌐 Language",
        "btn_autoreply": "🤖 Auto-reply",
        "btn_webapp": "🌐 Mini App",
        "btn_reply": "✍️ Reply",
        "btn_later": "🕒 Later",
        "btn_chat": "💬 Chat",
    },
}


async def t(uid, key, **kw):
    from .database import get_lang
    lang = await get_lang(uid)
    s = STRINGS.get(lang, STRINGS["ru"]).get(key) or STRINGS["ru"].get(key, key)
    return s.format(**kw) if kw else s