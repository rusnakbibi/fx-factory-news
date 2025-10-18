# run.py — фрагмент

import os, asyncio, logging
import contextlib
from dotenv import load_dotenv
load_dotenv()

from aiogram.exceptions import TelegramConflictError
from app.config import BOT_TOKEN
from app.bot import build_bot, build_dispatcher
from app.scheduler import scheduler

# --- NEW: PG advisory lock ---
import psycopg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")
POLL_LOCK_KEY = int(os.getenv("POLL_LOCK_KEY", "0"))  # краще = bot_id

@asynccontextmanager
async def acquire_pg_lock(dsn: str, key: int):
    if not dsn or not key:
        # без БД або ключа — не блокуємо (працює як раніше)
        yield
        return
    async with await psycopg.AsyncConnection.connect(dsn) as conn:
        while True:
            async with conn.cursor() as cur:
                await cur.execute("SELECT pg_try_advisory_lock(%s)", (key,))
                ok = (await cur.fetchone())[0]
            if ok:
                try:
                    yield
                finally:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT pg_advisory_unlock(%s)", (key,))
                return
            logging.warning("Another instance holds the polling lock; retry in 2s…")
            await asyncio.sleep(2)

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in environment")

    logging.info("Creating bot and dispatcher...")
    bot = await build_bot(BOT_TOKEN)
    dp = build_dispatcher()

    # Діагностика
    try:
        me = await bot.get_me()
        logging.warning(f"BOT DIAG: id={me.id} username=@{me.username}")
    except Exception as e:
        logging.error(f"BOT DIAG failed: {e}")

    # Скидаємо вебхук (на випадок міграцій)
    with contextlib.suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook deleted.")

    logging.info("Starting scheduler task...")
    bg = asyncio.create_task(scheduler(bot))

    # --- ВАЖЛИВО: монополізуємо polling через PG-замок ---
    try:
        async with acquire_pg_lock(DATABASE_URL, int(me.id)):  # ключ = bot_id
            logging.info("Polling lock acquired — starting polling.")
            await dp.start_polling(bot)
    except TelegramConflictError as e:
        logging.error(f"Polling conflict: {e}")
        raise
    finally:
        logging.info("Stopping scheduler...")
        bg.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await bg

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass