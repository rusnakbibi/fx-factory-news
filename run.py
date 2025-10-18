import asyncio
import contextlib
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from aiogram.exceptions import TelegramConflictError
from app.config import BOT_TOKEN
from app.bot import build_bot, build_dispatcher
from app.scheduler import scheduler

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in environment")

    logging.info("Creating bot and dispatcher...")
    bot = await build_bot(BOT_TOKEN)
    dp = build_dispatcher()

    # На випадок, якщо колись був webhook
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
        # ВАЖЛИВО: у Python 3.12 CancelledError може «спливати»,
        # тому чітко приглушуємо саме asyncio.CancelledError.
        with contextlib.suppress(asyncio.CancelledError):
            await bg

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # чистий вихід без зайвого трейсбеку
        pass