# app/handlers/commands.py
from __future__ import annotations

import logging
import os
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from ..config.settings import LOCAL_TZ, UTC
from ..config.topics import TOPIC_DEFS, TOPIC_EXPLAINERS
from ..services.translator import UA_DICT
from ..services.forex_client import get_events_thisweek_cached as fetch_calendar
from ..ui.filters import filter_events, normalize_impact
from ..ui.formatting import event_to_text
from ..utils.helpers import csv_to_list, chunk
from ..ui.keyboards import (
    back_kb,
    root_menu_kb, 
)
from ..core.database import ensure_sub, get_sub
from ..services.metals_parser import (
    load_today_from_file,
    load_week_from_file,
    mm_event_to_card_text
)

router = Router()
log = logging.getLogger(__name__)

IMPACT_EMOJI = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Non-economic": "⚪️",
}

METALS_TODAY_HTML = os.getenv("METALS_TODAY_HTML", "/data/metals_today.html")
METALS_WEEK_HTML_PATH = os.getenv("METALS_WEEK_HTML_PATH", "/data/metals_week.html")

# --------------------------- helpers ---------------------------

def resolve_data_path(filename: str) -> str:
    """
    Повертає коректний шлях до файлу:
    - локально: ./data/<file>
    - на Render: /data/<file>
    """
    # 1️⃣ Спочатку шукаємо env (якщо ти прописав у .env)
    env_path = os.getenv(f"METALS_{filename.upper().replace('.', '_')}")
    if env_path and Path(env_path).exists():
        return env_path

    # 2️⃣ Якщо існує /data/<file> (Render)
    path_data = Path("/data") / filename
    if path_data.exists():
        return str(path_data)

    # 3️⃣ Інакше fallback на ./data/<file> (локалка)
    path_local = Path(__file__).resolve().parents[2] / "data" / filename
    return str(path_local)

def _rowdict(row) -> dict:
    if row is None:
        return {}
    return dict(row) if not isinstance(row, dict) else row

def _lang(subs: dict) -> str:
    return (subs.get("lang_mode") or "en").lower()

def _t_en_ua(lang: str, en: str, ua: str) -> str:
    return ua if lang == "ua" else en

def _week_bounds_local(now_local: datetime) -> tuple[datetime, datetime]:
    """
    Межі тижня в локальній TZ: неділя 00:00 → наступна неділя 00:00.
    """
    delta_days = (now_local.weekday() + 1) % 7  # Sun=0
    sunday_local = (now_local - timedelta(days=delta_days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_sunday_local = sunday_local + timedelta(days=7)
    return sunday_local, next_sunday_local

def _fmt_local_time(dt_utc: datetime) -> str:
    """
    Короткий час події в локалі (наприклад 'Tue 09:30').
    """
    local = dt_utc.astimezone(LOCAL_TZ)
    return local.strftime("%a %H:%M")

def _compact_event_line(ev, lang: str) -> str:
    """
    Стисла стрічка для хайлайтів: emoji time CUR title (без зайвих тегів).
    """
    imp = (ev.impact or "").title()
    imp_emoji = IMPACT_EMOJI.get(imp, "•")
    t = _fmt_local_time(ev.date)
    cur = (ev.currency or "").upper()
    title = ev.title or ""
    return f"{imp_emoji} {t} {cur} — {title}"

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
            "• <b>Today</b> — shows today's events with your filters applied.\n"
            "• <b>This week</b> — events for the current week (Sun→Sun) with filters.\n"
            "• <b>Settings</b> — here you can:\n"
            "   — choose event impact levels: High / Medium / Low / Non-economic;\n"
            "   — select currencies (USD, EUR, etc.) to include;\n"
            "   — switch interface language (EN/UA);\n"
            "   — set the <u>alert lead time</u> — how many minutes <b>before each event</b> you'll get a reminder (e.g., 15 min before CPI release).\n"
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
            "currencies, language, and alert time — how many minutes before the event you'll receive a notification.\n\n"
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
            "On FF, page time may differ if 'Synchronized Time' doesn't match your device.\n\n"
            "<b>What do Settings filters do?</b>\n"
            "• Impact — importance level (High/Medium/Low/Non-eco).\n"
            "• Currencies — event currencies (USD, EUR, …).\n"
            "• Language — interface and event titles language (translated when possible).\n"
            "• Alerts — how many minutes before an event to notify.\n\n"
            "<b>Why do I see a currency I didn't select?</b>\n"
            "Re-check currencies. Some items are 'neutral' (no currency) like holidays/pressers and may still appear.\n\n"
            "<b>What are Topics?</b>\n"
            "Short explainers by category (CPI/PPI, GDP, PMI, labor, etc.).\n\n"
            "<b>How to refresh?</b>\n"
            "Auto refresh is used; on demand use <code>/ff_refresh</code>.\n\n"
            "<b>Privacy</b>\n"
            "Only your chat's filter/language prefs are stored; no personal data."
        )

def _weekly_summary_text(events, lang: str) -> list[str]:
    """
    Приймає ВЖЕ відфільтровані події за тиждень (за impact/currencies) і
    повертає список повідомлень (чантів) для Telegram.
    """
    if not events:
        return [_t_en_ua(lang,
            "📈 <b>Weekly summary</b>\nNo events match your filters for this week.",
            "📈 <b>Підсумок тижня</b>\nЗа вашим фільтром цього тижня подій немає."
        )]

    # Заголовок із датами тижня
    start_local, end_local = _week_bounds_local(datetime.now(LOCAL_TZ))
    hdr = _t_en_ua(
        lang,
        f"📈 <b>Weekly summary</b>\nWeek: <i>{start_local:%a %b %d}</i> → <i>{(end_local - timedelta(seconds=1)):%a %b %d}</i>\n",
        f"📈 <b>Підсумок тижня</b>\nТиждень: <i>{start_local:%a %b %d}</i> → <i>{(end_local - timedelta(seconds=1)):%a %b %d}</i>\n",
    )

    # Підрахунки
    total = len(events)
    by_impact = {"High": 0, "Medium": 0, "Low": 0, "Non-economic": 0}
    by_currency: dict[str, int] = {}

    for ev in events:
        imp = (ev.impact or "").title()
        if imp in by_impact:
            by_impact[imp] += 1
        cur = (ev.currency or "").upper()
        if cur:
            by_currency[cur] = by_currency.get(cur, 0) + 1

    # Топ валют (до 6)
    top_curs = sorted(by_currency.items(), key=lambda x: (-x[1], x[0]))[:6]
    top_curs_txt = ", ".join(f"{c}×{n}" for c, n in top_curs) if top_curs else _t_en_ua(lang, "n/a", "н/д")

    # Summary-блок
    summary_lines = [
        hdr,
        _t_en_ua(lang, "<b>Totals</b>:", "<b>Підсумки</b>:"),
        _t_en_ua(lang,
                 f"• Events: <b>{total}</b>",
                 f"• Подій: <b>{total}</b>"),
        f"• {IMPACT_EMOJI['High']} {_t_en_ua(lang,'High','Високий')}: <b>{by_impact['High']}</b>",
        f"• {IMPACT_EMOJI['Medium']} {_t_en_ua(lang,'Medium','Середній')}: <b>{by_impact['Medium']}</b>",
        f"• {IMPACT_EMOJI['Low']} {_t_en_ua(lang,'Low','Низький')}: <b>{by_impact['Low']}</b>",
        f"• {IMPACT_EMOJI['Non-economic']} {_t_en_ua(lang,'Non-eco','Нейтр.')}: <b>{by_impact['Non-economic']}</b>",
        _t_en_ua(lang, f"• Top currencies: {top_curs_txt}", f"• Топ валюти: {top_curs_txt}"),
        ""
    ]

    # Хайлайти (найважливіші майбутні/решта тижня події: High → потім Medium), до 10 рядків
    now_utc = datetime.now(UTC)
    upcoming = [e for e in events if e.date >= now_utc]
    upcoming.sort(key=lambda e: (e.impact != "High", e.date))  # High спершу, потім за часом
    highlights = upcoming[:10] if upcoming else events[:10]

    if highlights:
        summary_lines.append(_t_en_ua(lang, "<b>Highlights ahead</b>:", "<b>Головні попереду</b>:"))
        for ev in highlights:
            summary_lines.append(_compact_event_line(ev, lang))

    # Розбиваємо на чати по довжині ~3500 символів (з запасом до 4096)
    text = "\n".join(summary_lines)
    chunks: list[str] = []
    while len(text) > 3500:
        cut = text.rfind("\n", 0, 3500)
        if cut == -1:
            cut = 3500
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    chunks.append(text)
    return chunks

async def _send_weekly_summary(m: Message, subs: dict):
    """
    Збір weekly summary за поточний тиждень у локальній TZ з
    урахуванням фільтрів impact/currency.
    """
    subs = _rowdict(subs)
    lang = _lang(subs)

    impacts_raw = csv_to_list(subs.get("impact_filter", ""))
    impacts = [normalize_impact(x) for x in impacts_raw if normalize_impact(x)]
    countries = csv_to_list(subs.get("countries_filter", ""))

    try:
        events = await fetch_calendar(lang=lang)
    except Exception as e:
        log.exception("[weekly] load events failed: %s", e)
        await m.answer(_t_en_ua(lang, "Internal fetch error. See logs.", "Внутрішня помилка завантаження. Див. логи."))
        return

    # межі тижня
    now_local = datetime.now(LOCAL_TZ)
    sunday_local, next_sunday_local = _week_bounds_local(now_local)
    start_utc = sunday_local.astimezone(UTC)
    end_utc = next_sunday_local.astimezone(UTC)

    # вікно тижня, фільтри
    in_window = [e for e in events if start_utc <= e.date < end_utc]
    filtered = filter_events(in_window, impacts, countries)
    filtered.sort(key=lambda e: e.date)

    # віддати кілька повідомлень, якщо текст довгий
    for chunk_txt in _weekly_summary_text(filtered, lang):
        await m.answer(chunk_txt, parse_mode="HTML", disable_web_page_preview=True)

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
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ, lang) for ev in pack)
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
        body = "\n\n".join(event_to_text(ev, LOCAL_TZ, lang) for ev in pack)
        await m.answer(header + body, parse_mode="HTML", disable_web_page_preview=True)
        header = ""

async def _send_metals_today_offline(m: Message, lang: str) -> None:
    """
    Відправляє офлайн-події по металах за 'today' батчами по 8,
    як у Forex today. Всі тексти локалізовані через _t_en_ua.
    """
    try:
        html_path = resolve_data_path("metals_today.html")
        events = load_today_from_file(html_path)
    except FileNotFoundError:
        await m.answer(
            _t_en_ua(
                lang,
                f"Metals (offline) parse error: file not found: {html_path}",
                f"Метали (офлайн) помилка парсингу: файл не знайдено: {html_path}",
            )
        )
        return
    except Exception as e:
        await m.answer(
            _t_en_ua(
                lang,
                f"Metals (offline) parse error: {e}",
                f"Метали (офлайн) помилка парсингу: {e}",
            )
        )
        return

    # Apply metals filters
    from ..ui.filters import filter_metals_events
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    impacts = csv_to_list(subs.get("metals_impact_filter", ""))
    countries = csv_to_list(subs.get("metals_countries_filter", ""))
    filtered = filter_metals_events(events, impacts, countries)

    if not filtered:
        await m.answer(
            _t_en_ua(lang, "No metals events match your filters for today.", "Подій по металах за вашими фільтрами на сьогодні немає.")
        )
        return

    header = _t_en_ua(lang, "🪙 <b>Metals — Today</b>\n", "🪙 <b>Метали — Сьогодні</b>\n")

    # Пакуємо по 8 подій, як у Forex today
    first = True
    for pack in chunk(filtered, 8):
        body = "\n\n".join(mm_event_to_card_text(ev, lang=lang) for ev in pack)
        await m.answer(
            (header if first else "") + body,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        first = False

def mm_event_to_card_text_week(ev, lang: str = "en") -> str:
    """
    Беремо готовий текст картки (як для today) і міняємо тільки префікс часу,
    додаючи місяць і число: '• Sun 04:00 —' -> '• Sun Oct 26 04:00 —'.
    Також підтримує labels: '• Thu All Day —' -> '• Thu Oct 30 All Day —'.
    """
    import re
    base = mm_event_to_card_text(ev, lang=lang)  # існуючий форматер для today
    dt_local = ev.dt_utc.astimezone(LOCAL_TZ)
    
    # Extract time_str (may be "HH:MM" or "All Day", "Tentative", etc.)
    time_part = ev.time_str or "12:00"
    new_prefix = f"• {dt_local:%a %b %d} {time_part} —"
    
    # Match either HH:MM format OR any text (for labels like "All Day")
    # Pattern: "• Day TimeOrLabel —"
    return re.sub(r"^•\s*\w{3}\s+(.+?)\s+—", new_prefix, base, count=1)

async def _send_metals_week_offline(m: Message, lang: str):
    try:
        html_path = resolve_data_path("metals_week.html")
        events = load_week_from_file(html_path)
        
        # Apply metals filters
        from ..ui.filters import filter_metals_events
        subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
        impacts = csv_to_list(subs.get("metals_impact_filter", ""))
        countries = csv_to_list(subs.get("metals_countries_filter", ""))
        filtered = filter_metals_events(events, impacts, countries)
        
        if not filtered:
            await m.answer(
                _t_en_ua(lang, "No metals events match your filters for this week.", "Подій по металах за вашими фільтрами на цьому тижні немає.")
            )
            return

        chunk, acc = [], 0
        for ev in filtered:
            card = mm_event_to_card_text_week(ev, lang=lang)
            chunk.append(card)
            acc += len(card)

            if len(chunk) >= 12 or acc > 3500:
                await m.answer("\n\n".join(chunk), parse_mode="HTML")
                chunk, acc = [], 0

        if chunk:
            await m.answer("\n\n".join(chunk), parse_mode="HTML")

    except FileNotFoundError:
        await m.answer(
            _t_en_ua(lang, f"Metals (offline week) file not found: {html_path}", f"Метали (офлайн тиждень) файл не знайдено: {html_path}")
        )
    except Exception as e:
        await m.answer(
            _t_en_ua(lang, f"Metals (offline week) parse error: {e}", f"Метали (офлайн тиждень) помилка парсингу: {e}")
        )

# --------------------------- text commands ---------------------------

@router.message(Command("start"))
async def cmd_start(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await m.answer(
        _t_en_ua(lang, "Choose a section:", "Оберіть розділ:"),
        reply_markup=root_menu_kb(lang=lang),
    )

@router.message(Command("menu"))
async def cmd_menu(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await m.answer(
        _t_en_ua(lang, "Choose a section:", "Оберіть розділ:"),
        reply_markup=root_menu_kb(lang=lang),
    )

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
        from ..services.forex_client import clear_ff_cache
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

@router.message(Command("weekly_summary"))
async def cmd_weekly_summary(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    if not subs:
        ensure_sub(m.from_user.id, m.chat.id)
        subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    await _send_weekly_summary(m, subs)

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

@router.message(Command("metals_today"))
async def cmd_metals_today(m: Message):
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await _send_metals_today_offline(m, lang)

@router.message(Command("metals_week"))
async def cmd_metals_week(m: Message):
    ensure_sub(m.from_user.id, m.chat.id)
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    lang = _lang(subs)
    await _send_metals_week_offline(m, lang)
