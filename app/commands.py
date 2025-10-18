# app/commands.py
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from .config import LOCAL_TZ, UTC
from .ff_client import get_events_thisweek_cached as fetch_calendar
from .filters import filter_events, normalize_impact
from .formatting import event_to_text
from .utils import csv_to_list, chunk
from .keyboards import (
    main_menu_kb,
    back_kb,
    settings_kb,
    subscribe_time_kb,
    alerts_presets_kb,
)
from .db import ensure_sub, get_sub, unsubscribe, set_sub

router = Router()
log = logging.getLogger(__name__)


# --------------------------- helpers ---------------------------

def _rowdict(row) -> dict:
    """Безпечно приводить sqlite3.Row -> dict (або повертає dict як є)."""
    if row is None:
        return {}
    return dict(row) if not isinstance(row, dict) else row

def _fmt_event(ev):
    lt = ev.date.astimezone(LOCAL_TZ)
    return f"[{ev.currency}|{ev.impact}] {lt:%Y-%m-%d %H:%M} local / {ev.date:%Y-%m-%d %H:%M}Z — {ev.title[:80]}"

async def _send_today(m: Message, subs: dict):
    """
    Показує ВСІ події за сьогодні (повний календарний день у LOCAL_TZ),
    включно з тими, що вже відбулися.
    """
    subs = _rowdict(subs)
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

    # межі сьогодні у локалі -> у UTC
    now_local = datetime.now(LOCAL_TZ)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)

    todays = [e for e in events if start_utc <= e.date < end_utc]
    if not todays:
        sample = "\n".join(_fmt_event(ev) for ev in events[:3])
        log.debug(f"[today] no events in window; sample fetched:\n{sample}")
        await m.answer("Today: no events (time window).")
        return

    cats = csv_to_list(subs.get("categories_filter", ""))
    filtered = filter_events(events, impacts, countries, cats)
    if not filtered:
        sample = "\n".join(_fmt_event(ev) for ev in todays[:3])
        log.debug(f"[today] filtered out; sample in-window:\n{sample}")
        await m.answer("Today: no events match your filters.")
        return

    header = "📅 <b>Today</b>\n"
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""

async def _send_week(m: Message, subs: dict):
    """
    Показує ВСІ події за поточний тиждень (понеділок 00:00 → наступний понеділок 00:00)
    у локальному часовому поясі.
    """
    # нормалізуємо рядок sqlite3.Row -> dict
    subs = dict(subs) if not isinstance(subs, dict) else subs

    lang = subs.get("lang_mode", "en")

    # нормалізуємо impacts (Holiday -> Non-economic, med -> Medium ...)
    impacts_raw = csv_to_list(subs.get("impact_filter", ""))
    impacts = [normalize_impact(x) for x in impacts_raw if normalize_impact(x)]

    countries = csv_to_list(subs.get("countries_filter", ""))

    try:
        events = await fetch_calendar(lang=lang)  # thisweek.json (кеш) під капотом
    except Exception as e:
        log.exception(f"[week] fetch_calendar failed: {e}")
        await m.answer("Internal fetch error. See logs.")
        return

    # межі тижня у ЛОКАЛІ
    now_local = datetime.now(LOCAL_TZ)
    # weekday(): Mon=0 ... Sun=6
    monday_local = (now_local - timedelta(days=now_local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_monday_local = monday_local + timedelta(days=7)

    start_utc = monday_local.astimezone(UTC)
    end_utc = next_monday_local.astimezone(UTC)

    # фільтр за часом (UTC)
    weeks = [e for e in events if start_utc <= e.date < end_utc]
    if not weeks:
        await m.answer("This week: no events (time window).")
        return

    # застосовуємо фільтри користувача
    cats = csv_to_list(subs.get("categories_filter", ""))
    filtered = filter_events(weeks, impacts, countries, cats)
    if not filtered:
        await m.answer("This week: no events match your filters.")
        return

    header = "📅 <b>This week</b>\n"
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""


# --------------------------- text commands ---------------------------

@router.message(Command("start"))
async def cmd_start(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    await m.answer("Choose an action:", reply_markup=main_menu_kb())

@router.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Main menu:", reply_markup=main_menu_kb())

@router.message(Command("today"))
async def cmd_today(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    if not subs:
        ensure_sub(m.from_user.id, m.chat.id)
        subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    await _send_today(m, subs)

@router.message(Command("week"))
async def cmd_week(m: Message):
    subs = get_sub(m.from_user.id, m.chat.id)
    if not subs:
        ensure_sub(m.from_user.id, m.chat.id)
        subs = get_sub(m.from_user.id, m.chat.id)
    await _send_week(m, subs)


# --------------------------- inline: main menu ---------------------------

@router.callback_query(F.data == "menu:home")
async def cb_home(c: CallbackQuery):
    await c.message.edit_text("Main menu:", reply_markup=main_menu_kb())
    await c.answer()

@router.callback_query(F.data == "menu:today")
async def cb_today(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))

    await c.answer("Fetching today…", show_alert=False)
    try:
        await c.message.edit_text("📅 Today:", reply_markup=back_kb())
    except Exception:
        pass

    await _send_today(c.message, subs)
    await c.message.answer("Back to menu:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:week")
async def cb_week(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)

    await c.answer("Fetching this week…", show_alert=False)

    try:
        await c.message.edit_text("📅 This week:", reply_markup=back_kb())
    except Exception:
        pass

    await _send_week(c.message, subs)
    await c.message.answer("Back to menu:", reply_markup=main_menu_kb())


# --------------------------- inline: Settings ---------------------------

@router.callback_query(F.data == "menu:settings")
async def menu_settings(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))

    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_text("⚙️ Settings:", reply_markup=kb)
    await c.answer()

# toggle impact
@router.callback_query(F.data.startswith("imp:"))
async def cb_impact(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    impacts = set(csv_to_list(subs.get("impact_filter", "")))
    val = c.data.split(":", 1)[1]
    if val in impacts:
        impacts.remove(val)
    else:
        impacts.add(val)
    set_sub(c.from_user.id, c.message.chat.id, impact_filter=",".join(sorted(impacts)))

    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Impact updated")

# toggle category
@router.callback_query(F.data.startswith("cat:"))
async def cb_category(c: CallbackQuery):
    subs = dict(get_sub(c.from_user.id, c.message.chat.id))
    cats = set(csv_to_list(subs.get("categories_filter", "")))
    val = c.data.split(":", 1)[1].lower()

    if val in cats:
        cats.remove(val)
    else:
        cats.add(val)

    set_sub(c.from_user.id, c.message.chat.id, categories_filter=",".join(sorted(cats)))

    subs = dict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Categories updated ✅")

# toggle currency
@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    curr = set(csv_to_list(subs.get("countries_filter", "")))
    val = c.data.split(":", 1)[1]
    if val in curr:
        curr.remove(val)
    else:
        curr.add(val)
    set_sub(c.from_user.id, c.message.chat.id, countries_filter=",".join(sorted(curr)))

    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Currencies updated")

# language (radio)
@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(c: CallbackQuery):
    val = c.data.split(":", 1)[1]
    if val != "trash":
        set_sub(c.from_user.id, c.message.chat.id, lang_mode=val)

    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Language updated")

# alert presets (з Settings або з Alerts — однаковий callback data `al:<mins>`)
@router.callback_query(F.data.startswith("al:"))
async def cb_alert(c: CallbackQuery):
    try:
        val = int(c.data.split(":", 1)[1])
    except Exception:
        return await c.answer("Invalid value")
    set_sub(c.from_user.id, c.message.chat.id, alert_minutes=val)

    # якщо ми всередині Settings — просто оновимо клавіатуру Settings;
    # якщо у розділі Alerts — нижче є окремий handler меню (menu:alerts).
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    try:
        await c.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        # якщо не вийшло (бо ми в іншому екрані) — просто відпишемось
        pass
    await c.answer("Alert preset saved")

# reset
@router.callback_query(F.data == "reset")
async def cb_reset(c: CallbackQuery):
    set_sub(
        c.from_user.id,
        c.message.chat.id,
        impact_filter="High,Medium",
        countries_filter="",
        alert_minutes=30,
        lang_mode="en",
    )
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        csv_to_list(subs.get("categories_filter", "")),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Settings reset")


# --------------------------- inline: Daily Digest ---------------------------

@router.callback_query(F.data == "menu:subscribe")
async def menu_subscribe(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    cur = subs.get("daily_time", "09:00")
    presets = ["08:00", "09:00", "10:00", "12:00", "15:00", "18:00"]
    await c.message.edit_text(
        f"⏱ Choose daily digest time (current {cur}):",
        reply_markup=subscribe_time_kb(presets),
    )
    await c.answer()

@router.callback_query(F.data.startswith("sub:set:"))
async def cb_sub_set(c: CallbackQuery):
    t = c.data.split(":", 2)[2]
    if not re.fullmatch(r"\d{2}:\d{2}", t):
        return await c.answer("Invalid time")
    set_sub(c.from_user.id, c.message.chat.id, daily_time=t)
    await c.message.edit_text(f"✅ Daily digest at {t}.", reply_markup=main_menu_kb())
    await c.answer("Saved")


# --------------------------- inline: Alerts (екран) ---------------------------

@router.callback_query(F.data == "menu:alerts")
async def menu_alerts(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    cur = int(subs.get("alert_minutes", 30))
    await c.message.edit_text("⏰ Alert before event:", reply_markup=alerts_presets_kb(cur))
    await c.answer()


# --------------------------- inline: Stop ---------------------------

@router.callback_query(F.data == "menu:stop")
async def menu_stop(c: CallbackQuery):
    unsubscribe(c.from_user.id, c.message.chat.id)
    await c.message.edit_text("Notifications disabled for this chat.", reply_markup=main_menu_kb())
    await c.answer()