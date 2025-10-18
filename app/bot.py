# app/bot.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .commands import router as commands_router


async def build_bot(token: str) -> Bot:
    # ✅ Новий синтаксис для aiogram 3.7+
    defaults = DefaultBotProperties(parse_mode="HTML")
    return Bot(token=token, default=defaults)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(commands_router)
    return dp