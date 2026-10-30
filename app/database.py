# ============================================================
#  app/database.py (SQLite версия)
# ============================================================
import aiosqlite
from datetime import datetime
from typing import Optional
from .config import DEFAULT_LANG

DB_PATH = "questions.db"
pool = True # заглушка, чтобы бот не ругался

async def init_pool():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, username TEXT, full_name TEXT, lang TEXT DEFAULT 'ru', first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, msg_count INT DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id BIGINT NOT NULL, sender_name TEXT, sender_username TEXT, question TEXT, answer TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, answered_at TIMESTAMP, is_answered BOOLEAN DEFAULT FALSE, media_type TEXT, media_file_id TEXT, owner_msg_id BIGINT, reactions INT DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS scheduled (id INTEGER PRIMARY KEY AUTOINCREMENT, qid INT, answer TEXT, send_at TIMESTAMP)")
        await db.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INT, user_id BIGINT, owner_id BIGINT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, closed BOOLEAN DEFAULT FALSE)")
        await db.execute("CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INT, sender_role TEXT, text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        await db.execute("CREATE TABLE IF NOT EXISTS reactions_log (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INT, user_id BIGINT, emoji TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(question_id, user_id))")
        
        await db.commit()

async def close_pool():
    pass

async def upsert_user(u):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name, last_seen=CURRENT_TIMESTAMP, msg_count=msg_count+1
        """, (u.id, u.username, u.full_name))
        await db.commit()

async def get_lang(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT lang FROM users WHERE user_id=?", (uid,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else DEFAULT_LANG

async def set_lang(uid, lang):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
        await db.commit()

async def get_setting(k, d=None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (k,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else d

async def set_setting(k, v):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        await db.commit()

async def save_question(sender, text, mtype=None, fid=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO questions (sender_id, sender_name, sender_username, question, media_type, media_file_id)
            VALUES (?,?,?,?,?,?)
        """, (sender.id, sender.full_name, sender.username, text, mtype, fid))
        await db.commit()
        return cur.lastrowid

async def set_owner_msg(qid, mid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE questions SET owner_msg_id=? WHERE id=?", (mid, qid))
        await db.commit()

async def save_answer(qid, ans):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE questions SET answer=?, answered_at=CURRENT_TIMESTAMP, is_answered=TRUE WHERE id=?", (ans, qid))
        await db.commit()

async def get_question(qid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM questions WHERE id=?", (qid,)) as cur:
            return await cur.fetchone()

async def add_reaction(qid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE questions SET reactions=reactions+1 WHERE id=?", (qid,))
        await db.commit()

async def stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM questions") as cur: t = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM questions WHERE is_answered") as cur: a = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users") as cur: u = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM questions WHERE created_at > datetime('now', '-1 day')") as cur: today = (await cur.fetchone())[0]
        return t, a, u, today

async def list_questions(page=0, unanswered=False):
    offset = page * 5
    where = "WHERE is_answered=FALSE" if unanswered else ""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(f"SELECT * FROM questions {where} ORDER BY id DESC LIMIT 5 OFFSET ?", (offset,)) as cur:
            rows = await cur.fetchall()
        async with db.execute(f"SELECT COUNT(*) FROM questions {where}") as cur:
            total = (await cur.fetchone())[0]
        return rows, total

async def top_questions(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM questions WHERE reactions>0 ORDER BY reactions DESC LIMIT ?", (limit,)) as cur:
            return await cur.fetchall()

async def all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            return [r[0] for r in await cur.fetchall()]

async def daily_activity(days=14):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT DATE(created_at) as day, COUNT(*) as n FROM questions WHERE created_at > datetime('now', '-14 days') GROUP BY day ORDER BY day") as cur:
            return await cur.fetchall()

async def schedule_answer(qid, ans, send_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO scheduled (qid, answer, send_at) VALUES (?,?,?)", (qid, ans, send_at.strftime('%Y-%m-%d %H:%M:%S')))
        await db.commit()

async def due_scheduled():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM scheduled WHERE send_at <= datetime('now')") as cur:
            rows = await cur.fetchall()
        for r in rows:
            await db.execute("DELETE FROM scheduled WHERE id=?", (r["id"],))
        await db.commit()
        return rows

async def create_chat(qid, uid, oid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("INSERT INTO chats (question_id, user_id, owner_id) VALUES (?,?,?)", (qid, uid, oid))
        await db.commit()
        return cur.lastrowid

async def get_chat(cid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM chats WHERE id=?", (cid,)) as cur:
            return await cur.fetchone()

async def close_chat(cid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE chats SET closed=TRUE WHERE id=?", (cid,))
        await db.commit()

async def add_chat_msg(cid, role, text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO chat_messages (chat_id, sender_role, text) VALUES (?,?,?)", (cid, role, text))
        await db.commit()

async def chat_history(cid, limit=50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM chat_messages WHERE chat_id=? ORDER BY id DESC LIMIT ?", (cid, limit)) as cur:
            return await cur.fetchall()
