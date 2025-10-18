import os
import asyncio
import contextlib
import logging
from dotenv import load_dotenv

load_dotenv()

from aiogram.exceptions import TelegramConflictError
from app.bot import build_bot, build_dispatcher
from app.scheduler import scheduler
from app.config import BOT_TOKEN

# ---- PG advisory lock (blocking) ----
import psycopg
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")
LOCK_KEY_ENV = os.getenv("POLL_LOCK_KEY")  # можеш задати явно в ENV
# fallback: якщо не задано, ми візьмемо bot_id нижче після get_me()

@asynccontextmanager
async def pg_advisory_lock(dsn: str, lock_key: int):
    if not dsn:
        logging.warning("[lock] DATABASE_URL is empty → lock DISABLED!")
        yield
        return
    if not lock_key:
        logging.warning("[lock] lock_key is 0 → lock DISABLED!")
        yield
        return

    logging.warning(f"[lock] trying to acquire pg_advisory_lock({lock_key}) on DSN host…")
    # Блокувальна версія: чекаємо, доки замок звільнять
    async with await psycopg.AsyncConnection.connect(dsn) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT pg_advisory_lock(%s)", (lock_key,))
            got = (await cur.fetchone())[0] if await cur.fetchone() else True
        logging.warning(f"[lock] acquired (key={lock_key})")
        try:
            yield
        finally:
            async with conn.cursor() as cur:
                await cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
            logging.warning(f"[lock] released (key={lock_key})")

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in environment")

    # базове логування
    logging.info("Creating bot and dispatcher...")
    bot = await build_bot(BOT_TOKEN)
    dp = build_dispatcher()

    # Діагностика бота і ключа локера
    me = await bot.get_me()
    token_head = (BOT_TOKEN or "").split(":", 1)[0]
    logging.warning(f"BOT DIAG: id={me.id} user=@{me.username} token_head={token_head}")
    lock_key = int(LOCK_KEY_ENV) if LOCK_KEY_ENV else int(me.id)  # ключ = bot_id за замовчуванням
    logging.warning(f"[lock] DATABASE_URL set: {bool(DATABASE_URL)} | lock_key={lock_key}")

    # На всяк: знімаємо webhook і чистимо хвіст
    with contextlib.suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook deleted.")

    # ---- ВАЖЛИВО: ВСЕ, що може почати взаємодію з Telegram (scheduler + polling),
    # запускаємо ТІЛЬКИ В СЕРЕДИНІ ЛОКЕРА ----
    try:
        async with pg_advisory_lock(DATABASE_URL, lock_key):
            logging.info("Starting scheduler task (inside lock)...")
            bg = asyncio.create_task(scheduler(bot))
            try:
                logging.info("Starting polling (inside lock)...")
                await dp.start_polling(bot)
            except TelegramConflictError as e:
                logging.error(f"Polling conflict: {e}")
                raise
            finally:
                logging.info("Stopping scheduler...")
                bg.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await bg
    except Exception as e:
        logging.exception(f"Fatal in main: {e}")
        raise

if __name__ == "__main__":
    try:
        # можна підняти рівень логів через ENV: LOG_LEVEL=DEBUG
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, level, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass