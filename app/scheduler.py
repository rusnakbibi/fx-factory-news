# app/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot

from .config import LOCAL_TZ, DEFAULT_ALERT_MINUTES, POLL_INTERVAL_SECONDS, UTC
from .db import get_all_subs, mark_sent, was_sent
from .ff_client import fetch_calendar
from .filters import filter_events
from .formatting import event_to_text, event_hash
from .utils import csv_to_list, chunk

log = logging.getLogger(__name__)

async def scheduler(bot: Bot):
    """
    Періодичний планувальник:
    - оновлює кеш подій раз на 10 хв;
    - шле алерти за N хв до події;
    - щоденний дайджест у вказаний час.
    Акуратно завершується при скасуванні (Ctrl+C / SIGTERM) без трейсбеку.
    """
    # Невелика затримка, щоб не стартувати одночасно з полінгом
    await asyncio.sleep(2)

    cached = []
    last_fetch = datetime.min.replace(tzinfo=UTC)

    log.info("scheduler: started")
    try:
        while True:
            try:
                now_utc = datetime.now(UTC)

                # refresh cache every 10 min
                if (now_utc - last_fetch) > timedelta(minutes=10):
                    # Базово тягнемо 'en' (переклад робиться в інших місцях, якщо треба)
                    cached = await fetch_calendar(lang="en")
                    last_fetch = now_utc

                for sub in get_all_subs():
                    impacts = csv_to_list(sub["impact_filter"]) or ["High", "Medium"]
                    countries = csv_to_list(sub["countries_filter"]) or []
                    alert_minutes = int(sub["alert_minutes"]) or DEFAULT_ALERT_MINUTES
                    out_chat = sub["out_chat_id"] or sub["chat_id"]
                    lang_mode = sub["lang_mode"] if "lang_mode" in sub.keys() else "en"

                    # ------- Alerts N хв до події -------
                    ahead = now_utc + timedelta(minutes=alert_minutes)
                    for ev in filter_events(cached, impacts, countries):
                        # ±120 секунд, щоб не пропускати через тік сну
                        if abs((ev.date - ahead).total_seconds()) <= 120:
                            evh = event_hash(ev)
                            if not was_sent(out_chat, evh, "alert"):
                                try:
                                    await bot.send_message(
                                        out_chat,
                                        event_to_text(ev, LOCAL_TZ),
                                        parse_mode="HTML",
                                        disable_web_page_preview=True,
                                    )
                                    mark_sent(out_chat, evh, "alert")
                                except Exception:
                                    # не валимо цикл розсилки, якщо чат недоступний тощо
                                    pass

                    # ------- Daily digest у локальний час користувача -------
                    try:
                        hh, mm = map(int, str(sub["daily_time"]).split(":"))
                    except Exception:
                        hh, mm = 9, 0
                    now_local = datetime.now(LOCAL_TZ)
                    digest_key = f"digest-{now_local:%Y-%m-%d}"
                    if now_local.hour == hh and now_local.minute == mm:
                        if not was_sent(out_chat, "__digest__", digest_key):
                            start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
                            end = start + timedelta(days=1)
                            todays = [e for e in cached if start <= e.date < end]
                            filtered = filter_events(todays, impacts, countries)
                            if filtered:
                                for ch in chunk(filtered, 8):
                                    try:
                                        await bot.send_message(
                                            out_chat,
                                            "\n\n".join(event_to_text(e, LOCAL_TZ) for e in ch),
                                            parse_mode="HTML",
                                            disable_web_page_preview=True,
                                        )
                                    except Exception:
                                        pass
                            else:
                                try:
                                    await bot.send_message(out_chat, "Сьогодні подій за вашими фільтрами немає.")
                                except Exception:
                                    pass
                            mark_sent(out_chat, "__digest__", digest_key)

            except Exception as e:
                # Логуємо, але не падаємо з планувальника
                log.exception(f"scheduler: unexpected error: {e}")

            # Основний інтервал опитування
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    except asyncio.CancelledError:
        # М’який вихід при Ctrl+C / SIGTERM
        log.info("scheduler: cancellation received, exiting loop gracefully.")
        return
    finally:
        log.info("scheduler: stopped")