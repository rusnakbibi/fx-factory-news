# app/core/metals_scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..config.settings import LOCAL_TZ

log = logging.getLogger(__name__)

# Планувальник (часова зона з конфіга)
scheduler = AsyncIOScheduler(timezone=LOCAL_TZ)

async def update_metals():
    """
    Оновлення офлайн-файлу для Metals: викликає bash-скрипт.
    """
    log.info(f"[update_metals] triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    proc = await asyncio.create_subprocess_exec(
        "bash", "scripts/update_metals.sh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        log.error(f"[update_metals] non-zero exit: {proc.returncode} {stderr.decode(errors='ignore')}")
    else:
        log.info(f"[update_metals] ok: {(stdout.decode(errors='ignore') or '').strip()}")

async def update_metals_week():
    """
    Оновлення файлу тижня (data/metals_week.html) через скрипт.
    """
    log.info(f"[update_metals_week] triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    proc = await asyncio.create_subprocess_exec(
        "bash", "scripts/update_metals_week.sh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        log.error(f"[update_metals_week] non-zero exit: {proc.returncode} {stderr.decode(errors='ignore')}")
    else:
        log.info(f"[update_metals_week] ok: {stdout.decode(errors='ignore').strip()}")

def setup_jobs() -> None:
    """
    Регіструємо cron-джобу. Стартуємо scheduler на startup.
    """
    scheduler.add_job(
        update_metals,
        trigger="cron",
        hour="6-23",       # щогодини 06..23 локального часу
        minute="0",        # every hour at 00 minutes
        id="metals_update_hourly",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.add_job(
        update_metals_week,
        trigger="cron",
        hour="0",
        minute="20",
        id="metals_week_daily_0020",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.add_job(
        update_metals_week,
        trigger="cron",
        day_of_week="sun",
        hour="23",
        minute="55",
        id="metals_week_sun_2355",
        replace_existing=True,
        misfire_grace_time=600,
    )
    log.info("[setup_jobs] Metals update jobs registered")

async def start_metals_scheduler():
    """Запуск планувальника металів."""
    setup_jobs()
    if not scheduler.running:
        scheduler.start()
        log.info(f"[scheduler] ✅ started (tz={scheduler.timezone}) at {datetime.now(LOCAL_TZ)}")

    # 🔹 разовий запуск через 5 секунд після старту (щоб побачити, що все працює)
    scheduler.add_job(
        update_metals,
        trigger="date",
        run_date=datetime.now(LOCAL_TZ) + timedelta(seconds=5),
        id="metals_update_warmup",
        replace_existing=True,
    )
    log.info("[scheduler] queued warmup job +5s")

async def stop_metals_scheduler():
    """Зупинка планувальника металів."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("[scheduler] ✅ stopped")

