# app/commands.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from .config import LOCAL_TZ, UTC
from .ff_client import fetch_calendar
from .filters import filter_events
from .formatting import event_to_text
from .utils import csv_to_list, chunk
from .keyboards import main_menu_kb, back_kb, settings_kb, subscribe_time_kb, alerts_presets_kb
from .db import ensure_sub, get_sub, unsubscribe, set_sub

router = Router()
log = logging.getLogger(__name__)


def _fmt_event(ev):
    # зручно проглядати в логах
    lt = ev.date.astimezone(LOCAL_TZ)
    return f"[{ev.currency}|{ev.impact}] {lt:%Y-%m-%d %H:%M} (local) / {ev.date:%Y-%m-%d %H:%M}Z — {ev.title[:80]}"

# ---------- внутрішній хелпер: надіслати події за сьогодні ----------
async def _send_today(m: Message, subs: dict):
    """
    Показує всі події за СЬОГОДНІ (повний календарний день у LOCAL_TZ),
    включно з тими, що вже відбулися.
    """
    lang = subs.get("lang_mode", "en")
    impacts = csv_to_list(subs.get("impact_filter", ""))
    countries = csv_to_list(subs.get("countries_filter", ""))

    log.debug(f"[today] filters: impacts={impacts} countries={countries} lang={lang}")

    try:
        events = await fetch_calendar(lang=lang)
    except Exception as e:
        log.exception(f"[today] fetch_calendar failed: {e}")
        await m.answer("Internal fetch error. See logs.")
        return

    log.debug(f"[today] fetched total events: {len(events)}")

    # 1) Межі сьогодні у локальному часі
    now_local = datetime.now(LOCAL_TZ)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)

    log.debug(
        f"[today] window local: {start_local:%Y-%m-%d %H:%M} .. {end_local:%Y-%m-%d %H:%M} | "
        f"utc: {start_utc:%Y-%m-%d %H:%M}Z .. {end_utc:%Y-%m-%d %H:%M}Z"
    )

    # 2) Фільтр за часом (у UTC)
    todays = [e for e in events if start_utc <= e.date < end_utc]
    log.debug(f"[today] in-window (time) count: {len(todays)}")

    if not todays:
        # Підказка: покажемо перші 3 «поза вікном», щоб зрозуміти зсув
        sample = "\n".join(_fmt_event(ev) for ev in events[:3])
        log.debug(f"[today] sample of fetched (first 3):\n{sample}")
        await m.answer("Today: no events (time window). See logs for details.")
        return

    # 3) Застосовуємо user-фільтри
    filtered = filter_events(todays, impacts, countries)
    log.debug(f"[today] after filters count: {len(filtered)}")

    if not filtered:
        # Допоміжний лог: покажемо 3 події, що були у вікні, але відсіклися фільтрами
        sample = "\n".join(_fmt_event(ev) for ev in todays[:3])
        log.debug(f"[today] sample in-window (first 3):\n{sample}")
        await m.answer("Today: no events match your filters.")
        return

    # 4) Надсилаємо
    header = "📅 <b>Today</b>\n"
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""

# ---------- команди ----------
@router.message(Command("start"))
async def cmd_start(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    await m.answer("Choose an action:", reply_markup=main_menu_kb())

@router.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Main menu:", reply_markup=main_menu_kb())

@router.message(Command("today"))
async def cmd_today(m: Message):
    subs = get_sub(m.from_user.id, m.chat.id)
    if not subs:
        ensure_sub(m.from_user.id, m.chat.id)
        subs = get_sub(m.from_user.id, m.chat.id)
    await _send_today(m, subs)

# ---------- інлайн-меню (кнопки) ----------
@router.callback_query(F.data == "menu:home")
async def cb_home(c: CallbackQuery):
    # Повертаємось до головного меню, редагуємо поточне повідомлення.
    await c.message.edit_text("Main menu:", reply_markup=main_menu_kb())
    await c.answer()

@router.callback_query(F.data == "menu:today")
async def cb_today(c: CallbackQuery):
    # Забираємо підписку користувача, відправляємо сьогоднішні події
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)

    await c.answer("Fetching today…", show_alert=False)

    # Зручно: редагуємо «контейнерне» повідомлення на статус і Back
    try:
        await c.message.edit_text("📅 Today:", reply_markup=back_kb())
    except Exception:
        pass

    # Відправляємо список подій окремими повідомленнями
    await _send_today(c.message, subs)

    # І ще раз показуємо головне меню окремим повідомленням
    await c.message.answer("Back to menu:", reply_markup=main_menu_kb())

# ----- SETTINGS -----
@router.callback_query(F.data == "menu:settings")
async def menu_settings(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)
    kb = settings_kb(
        csv_to_list(subs["impact_filter"]),
        csv_to_list(subs["countries_filter"]),
        int(subs["alert_minutes"]),
        subs["lang_mode"],
    )
    await c.message.edit_text("⚙️ Settings:", reply_markup=kb)
    await c.answer()

# ----- DAILY DIGEST -----
@router.callback_query(F.data == "menu:subscribe")
async def menu_subscribe(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)
    cur = subs.get("daily_time", "09:00")
    presets = ["08:00","09:00","10:00","12:00","15:00","18:00"]
    await c.message.edit_text(
        f"⏱ Choose daily digest time (current {cur}):",
        reply_markup=subscribe_time_kb(presets),
    )
    await c.answer()

@router.callback_query(F.data.startswith("sub:set:"))
async def cb_sub_set(c: CallbackQuery):
    t = c.data.split(":", 2)[2]
    import re
    if not re.fullmatch(r"\d{2}:\d{2}", t):
        return await c.answer("Invalid time")
    set_sub(c.from_user.id, c.message.chat.id, daily_time=t)
    await c.message.edit_text(f"✅ Daily digest at {t}.", reply_markup=main_menu_kb())
    await c.answer("Saved")

# ----- ALERTS -----
@router.callback_query(F.data == "menu:alerts")
async def menu_alerts(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)
    cur = int(subs.get("alert_minutes", 30))
    await c.message.edit_text("⏰ Alert before event:", reply_markup=alerts_presets_kb(cur))
    await c.answer()

@router.callback_query(F.data.startswith("al:"))
async def cb_alert(c: CallbackQuery):
    try:
        val = int(c.data.split(":", 1)[1])
    except Exception:
        return await c.answer("Invalid value")
    set_sub(c.from_user.id, c.message.chat.id, alert_minutes=val)
    await c.message.edit_text(f"Saved: alert {val}m before.", reply_markup=main_menu_kb())
    await c.answer("Saved")

# ----- STOP -----
@router.callback_query(F.data == "menu:stop")
async def menu_stop(c: CallbackQuery):
    unsubscribe(c.from_user.id, c.message.chat.id)
    await c.message.edit_text("Notifications disabled for this chat.", reply_markup=main_menu_kb())
    await c.answer()