# ============================================================
#  app/handlers/__init__.py — регистрация роутеров
# ============================================================
from aiogram import Dispatcher

from . import user, owner, reactions, chat


def register_all(dp: Dispatcher):
    """
    Порядок важен:
    1. owner      — команды владельца (/start, /cancel, /close)
    2. reactions  — реакции (react:*)
    3. chat       — анонимный чат (userchat:*, /stop)
    4. user       — всё остальное (вопросы)
    """
    dp.include_router(owner.router)
    dp.include_router(reactions.router)
    dp.include_router(chat.router)
    dp.include_router(user.router)


__all__ = ["register_all"]