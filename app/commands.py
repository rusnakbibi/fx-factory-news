# app/commands.py
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from .config import LOCAL_TZ, UTC, TOPIC_DEFS, TOPIC_EXPLAINERS
from .translator import UA_DICT
from .ff_client import get_events_thisweek_cached as fetch_calendar, get_cache_meta
from .filters import filter_events, normalize_impact
from .formatting import event_to_text
from .utils import csv_to_list, chunk
from .keyboards import (
    main_menu_kb,
    back_kb,
    settings_kb,
    subscribe_time_kb,
    alerts_presets_kb,
    topics_kb,
    back_to_topics_kb,
)
from .db import ensure_sub, get_sub, unsubscribe, set_sub

router = Router()
log = logging.getLogger(__name__)

# --------------------------- helpers ---------------------------

def _rowdict(row) -> dict:
    if row is None:
        return {}
    return dict(row) if not isinstance(row, dict) else row

def _lang(subs: dict) -> str:
    return (subs.get("lang_mode") or "en").lower()

def _t_en_ua(lang: str, en: str, ua: str) -> str:
    return en if lang != "ua" else ua

def _fmt_ttl(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    if m and s:
        return f"≈ {m} хв {s} с"
    if m:
        return f"≈ {m} хв"
    return f"≈ {s} с"

def _tutorial_text(lang: str = "en") -> str:
    if lang == "ua":
        return (
            "❓ <b>Довідка</b>\n"
            "Коротко про кнопки в боті:\n\n"
            "• <b>Сьогодні</b> — показує всі події за сьогодні з урахуванням ваших фільтрів.\n"
            "• <b>Цього тижня</b> — події поточного тижня (неділя→неділя) з фільтрами.\n"
            "• <b>Налаштування</b> — тут ви:\n"
            "   — обираєте рівень впливу подій: High / Medium / Low / Non-economic;\n"
            "   — обираєте валюти (USD, EUR тощо), за якими показувати події;\n"
            "   — перемикаєте мову інтерфейсу (EN/UA);\n"
            "   — задаєте час попередження — за скільки хвилин до початку <b>кожної події</b> надійде сповіщення (наприклад, 15 хв до публікації CPI).\n"
            "   (Час попередження не впливає на щоденний дайджест — він приходить у задану годину.)\n"
            "• <b>Нагадування</b> — швидкий вибір інтервалу попередження (5/10/15/30/60/120 хв) перед <b>кожною подією</b> у Today/This week.\n"
            "• <b>Щоденний дайджест</b> — оберіть час доби, коли щодня отримувати стислий список запланованих подій.\n"
            "• <b>Теми</b> — пояснення ключових макроіндикаторів (CPI, GDP, PMI тощо) простою мовою.\n"
            "• <b>Вимкнути</b> — зупиняє сповіщення для цього чату.\n\n"
            "<i>Порада:</i> якщо результат порожній — розширте фільтри (додайте валюти або рівні впливу)."
        )
    else:
        return (
            "❓ <b>Tutorial</b>\n"
            "A quick guide to the bot controls:\n\n"
            "• <b>Today</b> — shows today’s events with your filters applied.\n"
            "• <b>This week</b> — events for the current week (Sun→Sun) with filters.\n"
            "• <b>Settings</b> — here you can:\n"
            "   — choose event impact levels: High / Medium / Low / Non-economic;\n"
            "   — select currencies (USD, EUR, etc.) to include;\n"
            "   — switch interface language (EN/UA);\n"
            "   — set the <u>alert lead time</u> — how many minutes <b>before each event</b> you’ll get a reminder (e.g., 15 min before CPI release).\n"
            "   (Alert lead time does <b>not</b> affect the Daily Digest — it is sent at the scheduled time.)\n"
            "• <b>Alerts</b> — quick presets (5/10/15/30/60/120 min) for reminders <b>before each event</b> in Today/This week.\n"
            "• <b>Daily Digest</b> — pick a time of day to receive a compact summary of upcoming events.\n"
            "• <b>Topics</b> — concise explainers for key macro indicators (CPI, GDP, PMI, etc.).\n"
            "• <b>Stop</b> — disables notifications for this chat.\n\n"
            "<i>Tip:</i> If results look empty, widen filters (add currencies or impact levels)."
        )

def _about_text(lang: str = "en") -> str:
    if lang == "ua":
        return (
            "ℹ️ <b>Про бота</b>\n"
            "Цей бот — помічник для стеження за ключовими макроекономічними подіями з офіційного джерела "
            "<b>ForexFactory</b> (thisweek.json).\n\n"
            "• <b>Дані:</b> основні економічні показники (CPI, GDP, PMI, "
            "зайнятість, рішення центробанків тощо). Дані оновлюються автоматично при появі нових подій.\n"
            "• <b>Фільтри:</b> у <i>Налаштуваннях</i> можна обрати рівень впливу новин (High/Medium/Low/Non-eco), "
            "валюти, мову відображення та час попередження — за скільки хвилин до публікації події бот надішле сповіщення.\n\n"
            "<i>Застереження:</i> інформація може містити затримки або неточності джерела. "
            "Використовуйте лише як допоміжний аналітичний інструмент."
        )
    else:
        return (
            "ℹ️ <b>About</b>\n"
            "This bot helps you track key macroeconomic events, sourced from "
            "<b>ForexFactory</b> (official thisweek.json).\n\n"
            "• <b>Data:</b> core economic indicators such as CPI, GDP, PMI, "
            "labor market data, and central bank releases. Updates automatically as new events appear.\n"
            "• <b>Filters:</b> in <i>Settings</i> you can choose news impact levels (High/Medium/Low/Non-eco), "
            "currencies, language, and alert time — how many minutes before the event you’ll receive a notification.\n\n"
            "<i>Disclaimer:</i> information may include delays or inaccuracies from the source. "
            "Use it as an analytical helper, not as trading advice."
        )

def _faq_text(lang: str = "en") -> str:
    if lang == "ua":
        return (
            "<b>❓ Питання-Відповіді</b>\n\n"
            "<b>Звідки дані?</b>\n"
            "З офіційного JSON ForexFactory (thisweek.json).\n\n"
            "<b>Чому час інший, ніж на сайті?</b>\n"
            "Бот показує час у <i>вашому локальному часовому поясі</i>. "
            "FF може відображати сторінку у своїй TZ, якщо не співпадає 'Synchronized Time'.\n\n"
            "<b>Що роблять фільтри у Settings?</b>\n"
            "• Impact — рівень важливості (High/Medium/Low/Non-eco).\n"
            "• Currencies — валюти подій (USD, EUR, ...).\n"
            "• Language — мова інтерфейсу й заголовків подій (за можливості переклад).\n"
            "• Alerts — за скільки хвилин до події надсилати нагадування.\n\n"
            "<b>Чому бачу подію не зі списку моїх валют?</b>\n"
            "Перевірте вибір валют у Settings. Також частина подій може бути 'нейтральною' без валюти — "
            "вони показуються незалежно (наприклад, свята або прес-конференції).\n\n"
            "<b>Що таке Topics?</b>\n"
            "Стислі довідники по категоріях (CPI/PPI, GDP, PMI, ринок праці тощо) з поясненнями показників.\n\n"
            "<b>Як оновити дані?</b>\n"
            "Бот оновлює автоматично; за потреби — команда <code>/ff_refresh</code>.\n\n"
            "<b>Конфіденційність</b>\n"
            "Зберігаються тільки налаштування фільтрів/мови для вашого чату; особисті дані не використовуються."
        )
    else:
        return (
            "<b>❓ FAQ</b>\n\n"
            "<b>Where do data come from?</b>\n"
            "Official ForexFactory JSON (thisweek.json).\n\n"
            "<b>Why do times differ from the website?</b>\n"
            "The bot renders times in <i>your local timezone</i>. "
            "On FF, page time may differ if 'Synchronized Time' doesn’t match your device.\n\n"
            "<b>What do Settings filters do?</b>\n"
            "• Impact — importance level (High/Medium/Low/Non-eco).\n"
            "• Currencies — event currencies (USD, EUR, …).\n"
            "• Language — interface and event titles language (translated when possible).\n"
            "• Alerts — how many minutes before an event to notify.\n\n"
            "<b>Why do I see a currency I didn’t select?</b>\n"
            "Re-check currencies. Some items are ‘neutral’ (no currency) like holidays/pressers and may still appear.\n\n"
            "<b>What are Topics?</b>\n"
            "Short explainers by category (CPI/PPI, GDP, PMI, labor, etc.).\n\n"
            "<b>How to refresh?</b>\n"
            "Auto refresh is used; on demand use <code>/ff_refresh</code>.\n\n"
            "<b>Privacy</b>\n"
            "Only your chat’s filter/language prefs are stored; no personal data."
        )


# --------------------------- core actions ---------------------------

async def _send_today(m: Message, subs: dict):
    """
    TODAY: офіційний ForexFactory (thisweek.json) з вікном 00:00–24:00 локального дня.
    """
    subs = _rowdict(subs)
    lang = _lang(subs)

    impacts = csv_to_list(subs.get("impact_filter", ""))
    countries = csv_to_list(subs.get("countries_filter", ""))

    log.info("🟢 [_send_today] forex only | impacts=%s | countries=%s",
             subs.get("impact_filter"), subs.get("countries_filter"))

    try:
        events = await fetch_calendar(lang=lang)
    except Exception as e:
        log.exception("[today] load events failed: %s", e)
        await m.answer(_t_en_ua(lang, "Internal fetch error. See logs.", "Внутрішня помилка завантаження. Див. логи."))
        return

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

    if not filtered:
        await m.answer(_t_en_ua(lang, "Today: no events match your filters.", "Сьогодні: подій за вашими фільтрами немає."))
        return

    header = _t_en_ua(lang, "📅 <b>Today</b>\n", "📅 <b>Сьогодні</b>\n")
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""

async def _send_week(m: Message, subs: dict):
    """
    THIS WEEK: офіційний ForexFactory, неділя→неділя у локальній TZ.
    """
    subs = _rowdict(subs)
    lang = _lang(subs)

    impacts_raw = csv_to_list(subs.get("impact_filter", ""))
    impacts = [normalize_impact(x) for x in impacts_raw if normalize_impact(x)]
    countries = csv_to_list(subs.get("countries_filter", ""))

    log.info("🟣 [_send_week] forex only | impacts=%s | countries=%s",
             subs.get("impact_filter"), subs.get("countries_filter"))

    try:
        events = await fetch_calendar(lang=lang)
    except Exception as e:
        log.exception("[week] load events failed: %s", e)
        await m.answer(_t_en_ua(lang, "Internal fetch error. See logs.", "Внутрішня помилка завантаження. Див. логи."))
        return

    # Sunday→Sunday в LOCAL_TZ
    now_local = datetime.now(LOCAL_TZ)
    delta_days = (now_local.weekday() + 1) % 7  # Sun=0
    sunday_local = (now_local - timedelta(days=delta_days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_sunday_local = sunday_local + timedelta(days=7)

    start_utc = sunday_local.astimezone(UTC)
    end_utc = next_sunday_local.astimezone(UTC)

    in_window = [e for e in events if start_utc <= e.date < end_utc]
    log.debug("[week/forex] window %s..%s, all=%d, in_window=%d",
              start_utc.isoformat(), end_utc.isoformat(), len(events), len(in_window))

    filtered = filter_events(in_window, impacts, countries)
    filtered.sort(key=lambda e: e.date)

    if not filtered:
        await m.answer(_t_en_ua(lang, "This week: no events match your filters.", "Цього тижня подій за вашими фільтрами немає."))
        return

    header = _t_en_ua(lang, "📅 <b>This week</b>\n", "📅 <b>Цього тижня</b>\n")
    for pack in chunk(filtered, 8):
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""

# --------------------------- text commands ---------------------------

@router.message(Command("start"))
async def cmd_start(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await m.answer(
        _t_en_ua(lang, "Back to menu:", "Назад до меню:"),
        reply_markup=main_menu_kb(lang=lang),
    )

@router.message(Command("menu"))
async def cmd_menu(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await m.answer(_t_en_ua(lang, "Main menu:", "Головне меню:"), reply_markup=main_menu_kb(lang=lang))

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

@router.message(Command("ff_refresh"))
async def cmd_ff_refresh(m: Message):
    try:
        from .ff_client import clear_ff_cache
        n = clear_ff_cache()
        msg = "✅ Forex cache refreshed"
        if isinstance(n, int):
            msg += f" ({n} cleared)" if n > 0 else " (nothing cached)"
        await m.answer(msg)
    except Exception as e:
        await m.answer(f"Refresh error: {e}")

@router.message(Command("tutorial"))
async def cmd_tutorial(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = subs.get("lang_mode", "en")
    await m.answer(_tutorial_text(lang), parse_mode="HTML", reply_markup=back_kb(lang))

# ---- з меню
@router.callback_query(F.data == "menu:tutorial")
async def cb_tutorial(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = subs.get("lang_mode", "en")
    await c.message.edit_text(
        _tutorial_text(lang),
        parse_mode="HTML",
        reply_markup=back_kb(lang),
        disable_web_page_preview=True
    )
    await c.answer()

@router.message(Command("about"))
async def cmd_about(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = subs.get("lang_mode", "en")
    text = _about_text(lang)
    # back кнопка до головного меню
    await m.answer(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb() if lang != "ua" else back_kb())

@router.message(Command("faq"))
async def cmd_faq(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = subs.get("lang_mode", "en")
    await m.answer(_faq_text(lang), parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb(lang))

# --------------------------- inline: main menu ---------------------------

@router.callback_query(F.data == "menu:home")
async def cb_home(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    await c.message.edit_text(_t_en_ua(lang, "Main menu:", "Головне меню:"), reply_markup=main_menu_kb(lang=lang))
    await c.answer()

@router.callback_query(F.data == "menu:today")
async def cb_today(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    await c.answer(_t_en_ua(lang, "Fetching today…", "Завантажую «Сьогодні»…"), show_alert=False)
    try:
        await c.message.edit_text(_t_en_ua(lang, "📅 Today:", "📅 Сьогодні:"), reply_markup=back_kb(lang=lang))
    except Exception:
        pass
    await _send_today(c.message, subs)
    await c.message.answer(_t_en_ua(lang, "Back to menu:", "Назад до меню:"), reply_markup=main_menu_kb(lang=lang))

@router.callback_query(F.data == "menu:week")
async def cb_week(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = get_sub(c.from_user.id, c.message.chat.id)
    lang = _lang(_rowdict(subs))
    await c.answer(_t_en_ua(lang, "Fetching this week…", "Завантажую «Цього тижня»…"), show_alert=False)
    try:
        await c.message.edit_text(_t_en_ua(lang, "📅 This week:", "📅 Цього тижня:"), reply_markup=back_kb(lang=lang))
    except Exception:
        pass
    await _send_week(c.message, _rowdict(subs))
    await c.message.answer(_t_en_ua(lang, "Back to menu:", "Назад до меню:"), reply_markup=main_menu_kb(lang=lang))

# --------------------------- inline: Settings ---------------------------

@router.callback_query(F.data == "menu:settings")
async def menu_settings(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)

    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        lang_mode=lang,
    )
    await c.message.edit_text(_t_en_ua(lang, "⚙️ Settings:", "⚙️ Налаштування:"), reply_markup=kb)
    await c.answer()

# toggle impact
@router.callback_query(F.data.startswith("imp:"))
async def cb_impact(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
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
        lang_mode=_lang(subs),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer(_t_en_ua(lang, "Impact updated", "Вплив оновлено"))

# toggle currency
@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
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
        lang_mode=_lang(subs),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer(_t_en_ua(lang, "Currencies updated", "Валюти оновлено"))

# language
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
        lang_mode=_lang(subs),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer(_t_en_ua(_lang(subs), "Language updated", "Мову змінено"))

# alert presets
@router.callback_query(F.data.startswith("al:"))
async def cb_alert(c: CallbackQuery):
    subs0 = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs0)
    try:
        val = int(c.data.split(":", 1)[1])
    except Exception:
        return await c.answer(_t_en_ua(lang, "Invalid value", "Некоректне значення"))
    set_sub(c.from_user.id, c.message.chat.id, alert_minutes=val)

    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    kb = settings_kb(
        csv_to_list(subs.get("impact_filter", "")),
        csv_to_list(subs.get("countries_filter", "")),
        int(subs.get("alert_minutes", 30)),
        lang_mode=_lang(subs),
    )
    try:
        await c.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await c.answer(_t_en_ua(lang, "Alert preset saved", "Нагадування збережено"))

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
        lang_mode=_lang(subs),
    )
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer(_t_en_ua(_lang(subs), "Settings reset", "Налаштування скинуто"))

# source toggle — відповідаємо, що доступний лише Forex
@router.callback_query(F.data.startswith("src:"))
async def cb_source(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    await c.answer(_t_en_ua(_lang(subs), "Only Forex is available now.", "Зараз доступний лише Forex."), show_alert=True)

# --------------------------- inline: Daily Digest ---------------------------

@router.callback_query(F.data == "menu:subscribe")
async def menu_subscribe(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    cur = subs.get("daily_time", "09:00")
    presets = ["08:00", "09:00", "10:00", "12:00", "15:00", "18:00"]
    await c.message.edit_text(
        _t_en_ua(lang, f"⏱ Choose daily digest time (current {cur}):", f"⏱ Оберіть час дайджесту (зараз {cur}):"),
        reply_markup=subscribe_time_kb(presets, lang=lang),
    )
    await c.answer()

@router.callback_query(F.data.startswith("sub:set:"))
async def cb_sub_set(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    t = c.data.split(":", 2)[2]
    if not re.fullmatch(r"\d{2}:\d{2}", t):
        return await c.answer(_t_en_ua(lang, "Invalid time", "Некоректний час"))
    set_sub(c.from_user.id, c.message.chat.id, daily_time=t)
    await c.message.edit_text(_t_en_ua(lang, f"✅ Daily digest at {t}.", f"✅ Дайджест о {t}."), reply_markup=main_menu_kb(lang=lang))
    await c.answer()

# --------------------------- inline: Alerts ---------------------------

@router.callback_query(F.data == "menu:alerts")
async def menu_alerts(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    if not subs:
        ensure_sub(c.from_user.id, c.message.chat.id)
        subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    cur = int(subs.get("alert_minutes", 30))
    await c.message.edit_text(_t_en_ua(lang, "⏰ Alert before event:", "⏰ Нагадування перед подією:"),
                              reply_markup=alerts_presets_kb(cur, lang=lang))
    await c.answer()

# --------------------------- inline: Stop ---------------------------

@router.callback_query(F.data == "menu:stop")
async def menu_stop(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    unsubscribe(c.from_user.id, c.message.chat.id)
    await c.message.edit_text(_t_en_ua(lang, "Notifications disabled for this chat.", "Сповіщення для цього чату вимкнено."),
                              reply_markup=main_menu_kb(lang=lang))
    await c.answer()

# --------------------------- Topics ---------------------------

def _t(dct: dict, lang: str, fallback: str = "en") -> str:
    """Проста локалізація: беремо dct[lang] або dct[fallback]."""
    return dct.get(lang) or dct.get(fallback) or ""

@router.callback_query(F.data == "menu:topics")
async def menu_topics(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    await c.message.edit_text(
        _t_en_ua(lang, "📚 Topics:", "📚 Теми:"),
        reply_markup=topics_kb(lang=lang)
    )
    await c.answer()

@router.callback_query(F.data.startswith("topic:"))
async def show_topic(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = subs.get("lang_mode", "en")
    _, topic_key = c.data.split(":", 1)

    td = TOPIC_DEFS.get(topic_key, {})
    title = (td.get("title", {}) or {}).get("ua" if lang == "ua" else "en", "Topic")
    blurb = (td.get("blurb", {}) or {}).get("ua" if lang == "ua" else "en", "")

    # Беремо список (EN за замовчуванням, UA – якщо вибрано)
    base_lang = "ua" if lang == "ua" else "en"
    expl = TOPIC_EXPLAINERS.get(topic_key, {}).get(base_lang, [])
    if not expl:
        expl = [("—", "No explainer yet / Пояснення буде додано")]

    lines = [f"📚 <b>{title}</b>", blurb, ""]

    for name, desc in expl:
        display_name = name
        # Якщо користувач обрав UA — додаємо переклад у дужках:
        if lang == "ua":
            ua = UA_DICT.get(name)
            if ua and ua != name:
                display_name = f"{name} ({ua})"
        lines.append(f"• <b>{display_name}</b> — {desc}")

    text = "\n".join(lines)

    from .keyboards import back_to_topics_kb
    await c.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_to_topics_kb(lang=lang),
        disable_web_page_preview=True
    )
    await c.answer()


@router.callback_query(F.data == "menu:about")
async def cb_about(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = subs.get("lang_mode", "en")
    text = _about_text(lang)
    try:
        await c.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb() if lang != "ua" else back_kb())
    except Exception:
        await c.message.answer(text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb() if lang != "ua" else back_kb())
    await c.answer()

@router.callback_query(F.data == "menu:faq")
async def menu_faq(c: CallbackQuery):
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = subs.get("lang_mode", "en")
    await c.message.edit_text(_faq_text(lang), parse_mode="HTML", disable_web_page_preview=True, reply_markup=back_kb(lang))
    await c.answer()