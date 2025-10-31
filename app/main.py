# app/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config.settings import BOT_TOKEN
from .handlers import commands, callbacks
from .core.scheduler import scheduler
from .core.metals_scheduler import start_metals_scheduler, stop_metals_scheduler
from .services.forex_client import start_autorefresh, stop_autorefresh

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def build_bot() -> Bot:
    """Створює екземпляр бота."""
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

def build_dispatcher() -> Dispatcher:
    """Створює та налаштовує диспетчер."""
    dp = Dispatcher()
    
    # Підключаємо основний router з командами
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    
    # Хуки життєвого циклу
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    return dp

async def on_startup(bot: Bot):
    """Функція запуску бота."""
    log.info("Bot starting up...")
    
    # Запускаємо автооновлення кешу ForexFactory
    await start_autorefresh()
    
    # Запускаємо планувальник подій (alerts & digest)
    asyncio.create_task(scheduler(bot))
    
    # Запускаємо планувальник оновлень металів
    await start_metals_scheduler()
    
    log.info("Bot started successfully")

async def on_shutdown(bot: Bot):
    """Функція зупинки бота."""
    log.info("Bot shutting down...")
    
    # Зупиняємо автооновлення
    await stop_autorefresh()
    
    # Зупиняємо планувальник металів
    await stop_metals_scheduler()
    
    log.info("Bot stopped")

async def main(bot: Bot = None):
    """Головна функція запуску бота."""
    if not bot:
        if not BOT_TOKEN:
            log.error("BOT_TOKEN not found in environment variables")
            return

        # Створюємо бота та диспетчер
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

    dp = Dispatcher()

    # Реєструємо роутери
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)

    # Запускаємо бота
    try:
        await on_startup(bot)
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot)

if __name__ == "__main__":
    asyncio.run(main())
