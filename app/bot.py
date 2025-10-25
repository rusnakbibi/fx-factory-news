# app/bot.py
from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import BOT_TOKEN, LOCAL_TZ

# Планувальник (часова зона з конфіга)
scheduler = AsyncIOScheduler(timezone=LOCAL_TZ)

async def update_metals():
    """
    Оновлення офлайн-файлу для Metals: викликає bash-скрипт.
    """
    proc = await asyncio.create_subprocess_exec(
        "bash", "scripts/update_metals.sh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        print("[update_metals] non-zero exit:", proc.returncode, stderr.decode(errors="ignore"))
    else:
        print("[update_metals] ok:", (stdout.decode(errors="ignore") or "").strip())

def setup_jobs() -> None:
    """
    Регіструємо cron-джобу. Стартуємо scheduler на startup.
    """
    scheduler.add_job(
        update_metals,
        trigger="cron",
        hour="6-23",       # щогодини 06..23 локального часу
        minute="0",        # на нульовій хвилині
        id="metals_update_hourly",
        replace_existing=True,
        misfire_grace_time=600,
    )

async def on_startup(*_) -> None:
    setup_jobs()
    if not scheduler.running:
        scheduler.start()

async def on_shutdown(*_) -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

def build_bot() -> Bot:
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # Підключаємо основний router з командами
    from .commands import router as commands_router
    dp.include_router(commands_router)

    # Хуки життєвого циклу
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp