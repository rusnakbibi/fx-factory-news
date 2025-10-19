# app/commands.py
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from .config import LOCAL_TZ, UTC
from .ff_client import get_events_thisweek_cached as fetch_calendar, load_aggregated_category
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

def _selected_source_from_subs(subs: dict) -> str:
    """
    Очікуємо у subscriptions.categories_filter одне значення:
    'forex' | 'crypto' | 'metals'. За замовчуванням 'forex'.
    """
    val = (subs.get("categories_filter") or "").strip().lower()
    return val if val in {"forex", "crypto", "metals"} else "forex"


class _AggEv:
    """
    Шим для елементів з агрегатора (metals/crypto) та FF (forex).
    Поля робимо “безпечними” під наш форматтер.
    """
    __slots__ = ("date", "title", "currency", "impact", "url", "origin", "raw_time")

    def __init__(self, d: dict):
        # date може бути:
        # - ISO без таймзони (наші metals/crypto)
        # - ISO з таймзоною (forex)
        dt_raw = d.get("date")
        if isinstance(dt_raw, datetime):
            self.date = dt_raw
        else:
            try:
                # НЕ додаємо tzinfo взагалі: зберігаємо як є (naive, якщо без зони)
                self.date = datetime.fromisoformat(dt_raw) if dt_raw else datetime.now()
            except Exception:
                self.date = datetime.now()

        self.title = d.get("title") or ""
        self.currency = d.get("currency") or ""
        self.impact = d.get("impact") or ""
        self.url = d.get("url") or None
        # додаткові поля з агрегатора:
        self.origin = d.get("origin") or ""
        self.raw_time = d.get("raw_time") or ""


async def _load_source_events(selected_source: str, lang: str):
    """
    - forex  -> thisweek.json (FF), повертаємо FFEvent-об’єкти (як було)
    - crypto/metals -> локальний агрегатор (dict -> _AggEv)
    """
    if selected_source == "forex":
        events = await fetch_calendar(lang=lang)
        return events

    from .aggregator import load_agg  # щоб уникнути циклів
    agg = load_agg() or {}
    key = "crypto" if selected_source == "crypto" else "metals"
    items = agg.get(key, []) or []
    return [_AggEv(x) for x in items]

def _sunday_of_week_local(d: date) -> datetime:
    """
    Повертає datetime(НЕДІЛЯ 00:00) для тижня, в якому лежить дата d, у LOCAL_TZ.
    На Python weekday(): Mon=0 ... Sun=6.
    Для неділі треба відняти (weekday+1) % 7 днів.
    """
    base = datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)
    delta_days = (base.weekday() + 1) % 7  # Sun -> 0, Mon -> 1, ..., Sat -> 6
    start = (base - timedelta(days=delta_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start

def _agg_sort_key(ev):
    """
    Стабільне сортування для подій з агрегатора (metals/crypto), де date може бути naive.
    Сортуємо по календарній даті, часу і raw_time як tie-breaker.
    """
    try:
        d = ev.date.date()
        t = ev.date.time()
    except Exception:
        d, t = None, None
    raw = getattr(ev, "raw_time", "") or ""
    return (d, t, raw)

async def _send_today(m: Message, subs: dict):
    """
    Today:
    - FOREX: як було (вікно за локаллю → UTC)
    - METALS/CRYPTO: БЕЗ будь-яких таймзон/вікон — просто origin == '*:today'
    """
    subs = _rowdict(subs)
    selected_source = _selected_source_from_subs(subs)
    lang = subs.get("lang_mode", "en")

    impacts = csv_to_list(subs.get("impact_filter", ""))
    countries = csv_to_list(subs.get("countries_filter", ""))

    log.info("🟢 [_send_today] selected_source = %s", selected_source)
    log.info("🟢 [_send_today] impacts = %s", subs.get("impact_filter"))
    log.info("🟢 [_send_today] countries = %s", subs.get("countries_filter"))

    # завантажуємо події з потрібного джерела
    try:
        events = await _load_source_events(selected_source, lang=lang)
    except Exception as e:
        log.exception("[today] load events failed: %s", e)
        await m.answer("Internal fetch error. See logs.")
        return

    if selected_source == "forex":
        # СТАРА ЛОГІКА — тільки для FOREX
        now_local = datetime.now(LOCAL_TZ)
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(UTC)
        end_utc = end_local.astimezone(UTC)

        in_window = [e for e in events if start_utc <= e.date < end_utc]
        log.debug("[today/forex] window %s..%s, all=%d, in_window=%d",
                  start_utc.isoformat(), end_utc.isoformat(), len(events), len(in_window))

        filtered = filter_events(in_window, impacts, countries)
        filtered.sort(key=lambda e: e.date)
    else:
        # METALS/CRYPTO: беремо рівно те, що прийшло з day=today (origin=* :today)
        todays = [e for e in events if getattr(e, "origin", "").endswith(":today")]
        log.debug("[today/%s] by origin ':today' -> %d", selected_source, len(todays))

        filtered = filter_events(todays, impacts, countries)
        filtered.sort(key=_agg_sort_key)

    if not filtered:
        await m.answer("Today: no events match your filters.")
        return

    header = "📅 <b>Today</b>\n"
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""


async def _send_week(m: Message, subs: dict):
    """
    Показує ВСІ події за ПОТОЧНИЙ ТИЖДЕНЬ у локальному TZ:
    Неділя 00:00 → наступна неділя 00:00 (як на ForexFactory).
    Працює для forex/crypto/metals згідно з обраним джерелом у Settings.
    """
    subs = _rowdict(subs)
    selected_source = _selected_source_from_subs(subs)
    lang = subs.get("lang_mode", "en")

    impacts_raw = csv_to_list(subs.get("impact_filter", ""))
    impacts = [normalize_impact(x) for x in impacts_raw if normalize_impact(x)]
    countries = csv_to_list(subs.get("countries_filter", ""))

    log.info("🟣 [_send_week] selected_source = %s", selected_source)
    log.info("🟣 [_send_week] impacts = %s", subs.get("impact_filter"))
    log.info("🟣 [_send_week] countries = %s", subs.get("countries_filter"))

    # завантажуємо події з потрібного джерела
    try:
        events = await _load_source_events(selected_source, lang=lang)
    except Exception as e:
        log.exception("[week] load events failed: %s", e)
        await m.answer("Internal fetch error. See logs.")
        return

    # Sunday→Sunday в LOCAL_TZ
    now_local = datetime.now(LOCAL_TZ)
    sunday_local = _sunday_of_week_local(now_local.date())
    next_sunday_local = sunday_local + timedelta(days=7)

    start_utc = sunday_local.astimezone(UTC)
    end_utc = next_sunday_local.astimezone(UTC)

    in_window = [e for e in events if start_utc <= e.date < end_utc]
    log.debug("[week] window %s..%s, all=%d, in_window=%d",
              start_utc.isoformat(), end_utc.isoformat(), len(events), len(in_window))

    if not in_window:
        await m.answer("This week: no events (time window).")
        return

    filtered = filter_events(in_window, impacts, countries)
    filtered.sort(key=lambda e: e.date)
    log.debug("[week] filtered=%d (impacts=%s, countries=%s)", len(filtered), impacts, countries)

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

@router.message(Command("agg_refresh"))
async def cmd_agg_refresh(m: Message):
    from .aggregator import refresh_cache
    try:
        counts = await refresh_cache()
        await m.answer(
            "Aggregator refreshed ✅\n"
            f"total={counts['total']} | forex={counts['forex']} | crypto={counts['crypto']} | metals={counts['metals']}"
        )
    except Exception as e:
        await m.answer(f"Aggregator error: {e}")

@router.message(Command("agg_stats"))
async def cmd_agg_stats(m: Message):
    from .aggregator import load_agg
    data = load_agg() or {}
    if not data:
        return await m.answer("No aggregator cache yet. Run /agg_refresh first.")
    await m.answer(
        "Aggregator stats:\n"
        f"updated_at: {data.get('updated_at','?')}\n"
        f"total_raw: {data.get('total_raw',0)}\n"
        f"forex: {len(data.get('forex',[]))}\n"
        f"crypto: {len(data.get('crypto',[]))}\n"
        f"metals: {len(data.get('metals',[]))}\n"
    )

@router.message(Command("agg_dump"))
async def cmd_agg_dump(m: Message):
    from .aggregator import load_agg
    data = load_agg() or {}
    if not data:
        return await m.answer("No aggregator cache yet. Run /agg_refresh first.")
    def tops(key):
        arr = data.get(key, [])[:5]
        return "\n".join(f"• {x.get('currency','')} [{x.get('impact','')}] — {x.get('title','')[:70]}" for x in arr) or "—"
    txt = (
        "<b>Aggregator dump (top 5)</b>\n\n"
        f"<b>Forex</b>\n{tops('forex')}\n\n"
        f"<b>Crypto</b>\n{tops('crypto')}\n\n"
        f"<b>Metals</b>\n{tops('metals')}\n"
    )
    await m.answer(txt, parse_mode="HTML", disable_web_page_preview=True)

@router.message(Command("crypto"))
async def cmd_crypto(m: Message):
    events = load_aggregated_category("crypto", lang="en")
    if not events:
        return await m.answer("No crypto events in aggregated cache. Run /agg_refresh first.")
    for pack in chunk(events[:30], 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer("📊 <b>Crypto</b>\n" + body, parse_mode="HTML", disable_web_page_preview=True)

@router.message(Command("metals"))
async def cmd_metals(m: Message):
    events = load_aggregated_category("metals", lang="en")
    if not events:
        return await m.answer("No metals events in aggregated cache. Run /agg_refresh first.")
    for pack in chunk(events[:30], 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer("🪙 <b>Metals</b>\n" + body, parse_mode="HTML", disable_web_page_preview=True)

@router.message(Command("forex"))
async def cmd_forex(m: Message):
    events = load_aggregated_category("forex", lang="en")
    if not events:
        return await m.answer("No forex events in aggregated cache. Run /agg_refresh first.")
    for pack in chunk(events[:30], 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer("💱 <b>Forex</b>\n" + body, parse_mode="HTML", disable_web_page_preview=True)

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


@router.callback_query(F.data == "menu:today")
async def cb_today(c: CallbackQuery):
    log.warning("UI pressed: TODAY")

@router.callback_query(F.data == "menu:week")
async def cb_week(c: CallbackQuery):
    log.warning("UI pressed: WEEK")


# --------------------------- inline: Settings ---------------------------

@router.callback_query(F.data == "menu:settings")
async def menu_settings(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
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

    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer("Settings reset")

# toggle source
@router.callback_query(F.data.startswith("src:"))
async def cb_source(c: CallbackQuery):
    val = c.data.split(":", 1)[1].strip().lower()
    if val not in ("forex", "crypto", "metals"):
        return await c.answer("Invalid source")

    # зберігаємо єдине значення (жодних списків)
    set_sub(c.from_user.id, c.message.chat.id, categories_filter=val)

    log.info("💾 [cb_source] saved categories_filter=%s", val)

    # перебудувати клавіатуру Settings
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    selected_source = _selected_source_from_subs(subs)
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        subs.get("lang_mode", "en"),
        selected_source,
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer(f"Source set to {val.capitalize()}")


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