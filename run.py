import asyncio
import contextlib
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# --- 🟡 DEBUG LOGGING CONFIG ---
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Розширюємо логування для наших модулів
logging.getLogger("app").setLevel(getattr(logging, log_level, logging.INFO))
logging.getLogger("aiogram").setLevel(getattr(logging, log_level, logging.INFO))
logging.getLogger("httpx").setLevel(getattr(logging, log_level, logging.INFO))

# --- імпорти після логів ---
from aiogram.exceptions import TelegramConflictError
from app.config import BOT_TOKEN
from app.bot import build_bot, build_dispatcher
from app.scheduler import scheduler

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in environment")

    logging.info("Creating bot and dispatcher...")
    bot = await build_bot(BOT_TOKEN)
    me = await bot.get_me()
    token_head = (BOT_TOKEN or "").split(":", 1)[0]
    token_tail = (BOT_TOKEN or "")[-10:]
    logging.warning(f"BOT DIAG → id={me.id} user=@{me.username} token_head={token_head} token_tail=...{token_tail}")
    dp = build_dispatcher()

    # --- очистка webhook ---
    with contextlib.suppress(Exception):
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook deleted.")

    logging.info("Starting scheduler task...")
    bg = asyncio.create_task(scheduler(bot))

    try:
        logging.info("Bot polling started. Press Ctrl+C to stop.")
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
        # чистий вихід без трейсбеків
        pass