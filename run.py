# run.py — повна версія з PG advisory-lock та охайним завершенням

import os
import asyncio
import logging
import contextlib
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from aiogram.exceptions import TelegramConflictError
from app.config import BOT_TOKEN
from app.bot import build_bot, build_dispatcher
from app.scheduler import scheduler

# --- PG advisory lock (через pg_try_advisory_lock у циклі) ---
import psycopg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")
LOCK_KEY_ENV = os.getenv("POLL_LOCK_KEY")  # можна не задавати; за замовчуванням = bot_id


@asynccontextmanager
async def acquire_pg_lock(dsn: str, key: int):
    """
    Блокує старт polling до звільнення advisory-lock у БД.
    Тримає одне підключення до PG поки працює polling+scheduler.
    """
    if not dsn:
        logging.warning("[lock] DATABASE_URL is empty → lock DISABLED")
        yield
        return
    if not key:
        logging.warning("[lock] lock_key is 0 → lock DISABLED")
        yield
        return

    conn = await psycopg.AsyncConnection.connect(
        dsn,
        options="-c application_name=forex-bot-worker"
    )
    try:
        logging.warning(f"[lock] trying to acquire pg_advisory_lock(key={key}) …")
        while True:
            async with conn.cursor() as cur:
                await cur.execute("SELECT pg_try_advisory_lock(%s)", (key,))
                row = await cur.fetchone()
                ok = bool(row and row[0])
            if ok:
                logging.warning(f"[lock] acquired (key={key})")
                break
            logging.warning(f"[lock] still waiting for key={key}… retry in 2s")
            await asyncio.sleep(2)

        try:
            yield
        finally:
            # знімаємо лок перед закриттям з'єднання
            try:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT pg_advisory_unlock(%s)", (key,))
                logging.warning(f"[lock] released (key={key})")
            except Exception as e:
                logging.warning(f"[lock] unlock error: {e}")
    finally:
        with contextlib.suppress(Exception):
            await conn.close()


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in environment")

    logging.info("Creating bot and dispatcher...")
    bot = await build_bot(BOT_TOKEN)
    dp = build_dispatcher()

    # Діагностика бота та ключа локера
    me = await bot.get_me()
    token_head = (BOT_TOKEN or "").split(":", 1)[0]
    lock_key = int(LOCK_KEY_ENV) if LOCK_KEY_ENV else int(me.id)
    logging.warning(f"BOT DIAG: id={me.id} user=@{me.username} token_head={token_head}")
    logging.warning(f"[lock] DATABASE_URL set: {bool(DATABASE_URL)} | lock_key={lock_key}")

    # Скидаємо вебхук і «хвіст» апдейтів на випадок міграцій
    with contextlib.suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook deleted.")

    # ВАЖЛИВО: і scheduler, і polling — тільки всередині локера
    try:
        async with acquire_pg_lock(DATABASE_URL, lock_key):
            logging.info("Starting scheduler task (inside lock)…")
            bg = asyncio.create_task(scheduler(bot))

            try:
                logging.info("Starting polling (inside lock)…")
                await dp.start_polling(bot)
            except TelegramConflictError as e:
                logging.error(f"Polling conflict: {e}")
                raise
            finally:
                logging.info("Stopping scheduler…")
                bg.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await bg
    finally:
        # охайно закриваємо сесію бота (інакше буде "Unclosed client session")
        with contextlib.suppress(Exception):
            await bot.session.close()


if __name__ == "__main__":
    try:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, level, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # чистий вихід без зайвого трейсбеку
        pass