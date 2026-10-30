# ============================================================
#  app/bot.py — ЧАСТЬ 1/3
#  Импорты · логирование · валидация конфига
# ============================================================
import asyncio
import logging
import os
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from .config import BOT_TOKEN, OWNER_IDS, DEFAULT_LANG
from .database import init_pool, close_pool, get_setting, set_setting
from .handlers import register_all
from .utils.scheduler import start_all as start_scheduler


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)-12s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


log = logging.getLogger("bot")


def validate_config():
    errors = []
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        errors.append("BOT_TOKEN не задан или неверного формата")
    if not OWNER_IDS:
        errors.append("OWNER_IDS не задан (пример: 111111111,222222222)")
    if errors:
        print("\n❌ Ошибки конфигурации:")
        for e in errors:
            print(f"   • {e}")
        print("\nПроверь файл .env\n")
        sys.exit(1)
    log.info("✅ Конфигурация валидна")
    log.info("   Владельцев: %d", len(OWNER_IDS))
    log.info("   Язык: %s", DEFAULT_LANG)

# ============================================================
#  app/bot.py — ЧАСТЬ 2/3
#  Dispatcher · startup · shutdown
# ============================================================


def build_dispatcher() -> Dispatcher:
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(redis_url)
            log.info("🧠 FSM: Redis (%s)", redis_url.split("@")[-1])
        except Exception as e:
            log.warning("Redis недоступен (%s) → MemoryStorage", e)
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
        log.info("🧠 FSM: MemoryStorage")

    dp = Dispatcher(storage=storage)
    register_all(dp)
    log.info("🔌 Роутеры зарегистрированы (owner → reactions → chat → user)")
    return dp


async def on_startup(bot: Bot):
    log.info("🚀 Запуск бота...")

    await init_pool()
    log.info("🗄️  PostgreSQL подключён")

    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🏠 Главное меню"),
            BotCommand(command="stop", description="🚪 Закрыть чат"),
            BotCommand(command="cancel", description="❌ Отменить действие"),
            BotCommand(command="myreactions", description="❤️ Мои реакции"),
        ])
        log.info("📋 Команды установлены")
    except Exception as e:
        log.warning("set_my_commands: %s", e)

    if not await get_setting("autoreply"):
        await set_setting("autoreply", "")

    try:
        me = await bot.get_me()
        log.info("🤖 Бот: @%s (id=%s)", me.username, me.id)
    except Exception as e:
        log.warning("get_me: %s", e)

    start_scheduler(bot)
    log.info("⏱  Планировщик запущен")

    for oid in OWNER_IDS:
        try:
            await bot.send_message(
                oid,
                "✅ <b>Бот запущен</b>\n\nВсе системы в норме 🟢",
                parse_mode="HTML",
            )
        except Exception:
            pass

    log.info("✅ Бот готов к работе")


async def on_shutdown(bot: Bot):
    log.info("🛑 Остановка бота...")
    for oid in OWNER_IDS:
        try:
            await bot.send_message(oid, "🛑 <b>Бот остановлен</b>", parse_mode="HTML")
        except Exception:
            pass
    await close_pool()
    log.info("🗄️  БД отключена")
    try:
        await bot.session.close()
    except Exception:
        pass
    log.info("👋 Пока!")

# ============================================================
#  app/bot.py — ЧАСТЬ 3/3
#  main() · polling · запуск
# ============================================================


async def run_polling(bot: Bot, dp: Dispatcher):
    stop_event = asyncio.Event()

    def _stop(*_):
        log.info("Получен сигнал остановки")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            signal.signal(sig, _stop)

    polling = asyncio.create_task(
        dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
    )

    await stop_event.wait()
    log.info("Останавливаю polling...")
    await dp.stop_polling()
    polling.cancel()
    try:
        await polling
    except (asyncio.CancelledError, Exception):
        pass


async def main():
    setup_logging()
    log.info("=" * 60)
    log.info("  🤖 AnonBot ULTIMATE — старт")
    log.info("=" * 60)

    validate_config()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    try:
        await on_startup(bot)
        await run_polling(bot, dp)
    except Exception as e:
        log.exception("Критическая ошибка: %s", e)
        raise
    finally:
        await on_shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Прервано")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        sys.exit(1)
