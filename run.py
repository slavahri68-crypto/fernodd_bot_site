#!/usr/bin/env python3
# ============================================================
#  run.py — лаунчер
#  python run.py          → только бот
#  python run.py webapp   → только Mini App
#  python run.py all      → бот + Mini App
# ============================================================
import sys
import asyncio
import logging


def run_bot():
    from app.bot import main
    asyncio.run(main())


def run_webapp():
    import uvicorn
    from app.config import WEBAPP_PORT
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "app.webapp.server:app",
        host="0.0.0.0",
        port=WEBAPP_PORT,
        log_level="info",
    )


async def run_all():
    import uvicorn
    from app.config import WEBAPP_PORT
    from app.bot import main as bot_main

    config = uvicorn.Config(
        "app.webapp.server:app",
        host="0.0.0.0",
        port=WEBAPP_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)

    await asyncio.gather(bot_main(), server.serve())


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "bot"
    if mode == "bot":
        run_bot()
    elif mode == "webapp":
        run_webapp()
    elif mode == "all":
        try:
            asyncio.run(run_all())
        except KeyboardInterrupt:
            print("\n👋 Остановлено")
    else:
        print("Использование: python run.py [bot|webapp|all]")
        sys.exit(1)