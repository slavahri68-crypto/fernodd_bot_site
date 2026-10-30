# ============================================================
#  app/webapp/server.py — FastAPI Mini App
#  • HMAC-проверка Telegram initData
#  • /api/stats, /api/questions, /api/top, /api/activity
#  • отдача index.html
# ============================================================
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..config import BOT_TOKEN, is_owner
from ..database import (
    pool, init_pool, close_pool,
    stats, list_questions, top_questions, daily_activity,
)

log = logging.getLogger("webapp")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def verify_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(401, "no initData")
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop("hash", None)
        if not received_hash:
            raise HTTPException(401, "no hash")

        data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calc, received_hash):
            raise HTTPException(401, "invalid hash")

        return json.loads(pairs.get("user", "{}"))
    except HTTPException:
        raise
    except Exception as e:
        log.warning("verify_init_data: %s", e)
        raise HTTPException(401, "bad initData")


async def current_user(request: Request) -> dict:
    init_data = request.headers.get("X-Init-Data", "")
    return verify_init_data(init_data)


async def owner_only(user: dict = Depends(current_user)) -> dict:
    if not is_owner(user.get("id", 0)):
        raise HTTPException(403, "owners only")
    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    log.info("WebApp: БД подключена")
    yield
    await close_pool()
    log.info("WebApp: остановлен")


app = FastAPI(title="AnonBot MiniApp", lifespan=lifespan)


@app.get("/api/me")
async def api_me(user: dict = Depends(current_user)):
    return {
        "id": user.get("id"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "is_owner": is_owner(user.get("id", 0)),
    }


@app.get("/api/stats")
async def api_stats(user: dict = Depends(owner_only)):
    total, answered, users, today = await stats()
    return {
        "total": total, "answered": answered,
        "pending": total - answered,
        "users": users, "today": today,
    }


@app.get("/api/questions")
async def api_questions(page: int = 0, mode: str = "all",
                        user: dict = Depends(owner_only)):
    rows, total = await list_questions(page, mode == "unans")
    items = []
    for r in rows:
        items.append({
            "id": r["id"], "question": r["question"],
            "answer": r["answer"], "is_answered": r["is_answered"],
            "reactions": r["reactions"] or 0,
            "media_type": r["media_type"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "answered_at": r["answered_at"].isoformat() if r["answered_at"] else None,
        })
    return {"items": items, "total": total, "page": page}


@app.get("/api/top")
async def api_top(user: dict = Depends(owner_only)):
    rows = await top_questions(10)
    return {"items": [
        {"id": r["id"], "question": r["question"],
         "reactions": r["reactions"] or 0} for r in rows]}


@app.get("/api/activity")
async def api_activity(user: dict = Depends(owner_only)):
    from datetime import datetime, timedelta
    rows = await daily_activity(14)
    by_day = {r["day"].isoformat(): r["n"] for r in rows}
    today = datetime.now().date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(13, -1, -1)]
    counts = [by_day.get(d, 0) for d in days]
    return {"days": days, "counts": counts}


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(path):
        return HTMLResponse("<h1>Mini App не найден</h1>", status_code=500)
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    from ..config import WEBAPP_PORT
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("app.webapp.server:app", host="0.0.0.0", port=WEBAPP_PORT)