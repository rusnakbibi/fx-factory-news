from aiogram import Bot, Dispatcher
from .commands import router as commands_router

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(commands_router)
    return dp

async def build_bot(token: str) -> Bot:
    return Bot(token)
