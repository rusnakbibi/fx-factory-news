# app/aggregator.py
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, date, time, timedelta
from typing import Any, Dict, List, Optional
import urllib.parse

import httpx
from bs4 import BeautifulSoup

from .config import UA_HEADERS, LOCAL_TZ

log = logging.getLogger(__name__)

# Куди зберігати агрегований JSON
AGG_PATH = os.getenv("FF_AGG_JSON", "/tmp/ff_agg.json")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _now_utc_iso() -> str:
    """UTC timestamp для updated_at без потреби імпорту timezone."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _proxied(url: str, render: bool = True) -> Optional[str]:
    """Побудувати ScraperAPI URL (або None, якщо ключа немає)."""
    key = os.getenv("SCRAPERAPI_KEY", "")
    if not key:
        return None
    q = {"api_key": key, "url": url}
    if render:
        q["render"] = "true"
    return "https://api.scraperapi.com/?" + urllib.parse.urlencode(q)

async def _fetch_html(url: str, timeout: float = 60.0) -> Optional[str]:
    """
    Спробувати забрати HTML напряму; якщо 403/429 — через ScraperAPI (з render=true).
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url, headers=UA_HEADERS)
            if r.status_code == 200 and r.text:
                log.info("aggregator: direct ok %s len=%s", url, len(r.text))
                return r.text
            log.info("aggregator: direct %s -> %s ; try proxy…", url, r.status_code)
        except Exception as e:
            log.info("aggregator: direct error %s -> %s ; try proxy…", url, e)

        prox = _proxied(url, render=True)
        if not prox:
            log.warning("aggregator: SCRAPERAPI_KEY not set; cannot proxy %s", url)
            return None
        try:
            pr = await client.get(prox, headers=UA_HEADERS, timeout=timeout)
            if pr.status_code == 200 and pr.text:
                log.info("aggregator: proxy ok %s len=%s", url, len(pr.text))
                return pr.text
            log.info("aggregator: proxy %s -> %s", url, pr.status_code)
        except Exception as e:
            log.info("aggregator: proxy error %s -> %s", url, e)
    return None

def _text(el) -> str:
    return (el.get_text(" ", strip=True) if el is not None else "").strip()

# ---------------------------------------------------------------------
# FOREX: як було (офіційний thisweek.json через наш ff_client)
# ---------------------------------------------------------------------

async def _load_forex_thisweek() -> List[Dict[str, Any]]:
    """
    Будь-які FF-події за поточний тиждень через кешований клієнт (thisweek.json).
    Нічого з TZ тут не чіпаємо (ff_client вже дає ISO з tz).
    """
    from .ff_client import get_events_thisweek_cached
    events = await get_events_thisweek_cached(lang="en")
    out: List[Dict[str, Any]] = []
    for ev in events:
        out.append(
            {
                "date": ev.date.isoformat(),  # як є від ff_client
                "title": ev.title,
                "currency": (ev.currency or "").upper(),
                "impact": ev.impact or "",
                "url": ev.url,
                "origin": "ff:thisweek",
                "day_label": "",
                "time_str": "",
            }
        )
    return out

# ---------------------------------------------------------------------
# METALS & CRYPTO: парсимо HTML (metalsmine.com, cryptocraft.com)
# ---------------------------------------------------------------------

_IMPACT_CLASS_MAP = {
    "impact-red": "High",
    "impact-ora": "Medium",
    "impact-yel": "Low",
}
_IMPACT_RE = re.compile(r"impact-(red|ora|yel)", re.I)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))\s*(am|pm)\b", re.I)

def _parse_ampm_time(s: str) -> time:
    """
    '12:45am' -> time(0,45); '4:00pm' -> 16:00.
    Для 'all day' / 'tba' / '' повертаємо 00:00.
    """
    if not s:
        return time(0, 0)
    s = s.strip().lower()
    if s in {"all day", "allday", "—", "-", "–", "— —", "n/a", "tba", "tbd", "tentative"}:
        return time(0, 0)
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", s)
    if not m:
        return time(0, 0)
    hh = int(m.group(1))
    mm = int(m.group(2) or "0")
    ap = m.group(3)
    if hh == 12:
        hh = 0
    if ap == "pm":
        hh += 12
    return time(hh, mm)

def _pick_time_string(tr) -> str:
    """
    Дістає рядок часу з клітинки .calendar__time. Повертає '12:45am' / '4:00pm' /
    'all day' або '' (оригінальний текст, без конвертацій).
    """
    cell = tr.select_one(".calendar__time")
    if not cell:
        return ""
    cand: List[str] = []

    for el in cell.find_all(["span", "div", "b", "em", "a"], recursive=True):
        s = _text(el)
        if s:
            cand.append(s)
        for attr in ("title", "data-title", "data-time", "data-original-title"):
            val = el.get(attr)
            if isinstance(val, str) and val.strip():
                cand.append(val.strip())

    full = _text(cell)
    if full:
        cand.append(full)
    for attr in ("title", "data-title", "data-time", "data-original-title"):
        val = cell.get(attr)
        if isinstance(val, str) and val.strip():
            cand.append(val.strip())

    for s in cand:
        m = _TIME_RE.search(s)
        if m:
            return m.group(0).lower()

    if any("day" in s.lower() for s in cand) or any(
        t in s.lower() for t in cand for t in ["all day", "tba", "tbd", "tentative"]
    ):
        return "all day"

    return ""

def _guess_impact_from_node(row) -> str:
    icon = row.select_one(".calendar__impact [class*='impact']")
    if icon:
        cls = " ".join(icon.get("class") or [])
        m = _IMPACT_RE.search(cls)
        if m:
            key = m.group(1).lower()
            return _IMPACT_CLASS_MAP.get(f"impact-{key}", "")
    img = row.select_one(".calendar__impact img[alt]")
    if img and img.get("alt"):
        alt = img.get("alt", "").lower()
        if "high" in alt:
            return "High"
        if "medium" in alt:
            return "Medium"
        if "low" in alt:
            return "Low"
    return ""

def _norm_impact(s: str) -> str:
    s = (s or "").strip().lower()
    if "high" in s:
        return "High"
    if "medium" in s or "med" in s:
        return "Medium"
    if "low" in s:
        return "Low"
    if "holiday" in s or "bank" in s or "non" in s:
        return "Non-economic"
    return s.title() if s else ""

def _header_to_date(head_text: str, today_local: date) -> Optional[date]:
    """
    Конвертує текст заголовка дня ('Today', 'Tomorrow', 'Mon Oct 21') -> date.
    """
    if not head_text:
        return None
    t = head_text.strip()
    tl = t.lower()

    if tl.startswith("today"):
        return today_local
    if tl.startswith("tomorrow"):
        return today_local + timedelta(days=1)

    parts = t.split()
    if len(parts) >= 3:
        mon_name = parts[1].lower()[:3]
        mon = _MONTHS.get(mon_name)
        try:
            dd = int(re.sub(r"[^\d]", "", parts[2]))
        except Exception:
            dd = None
        if mon and dd and (1 <= dd <= 31):
            return date(today_local.year, mon, dd)

    return None

def _parse_calendar_today_only(html: str, origin: str) -> List[Dict[str, Any]]:
    """
    Парсимо сторінку ?day=today і повертаємо ЛИШЕ події «сьогодні».
    ВАЖЛИВО: якщо заголовок дня стоїть у тому ж <tr>, що й подія,
    ми не робимо continue — парсимо цей же рядок як подію today.
    Як тільки зустрічаємо наступний заголовок дня — зупиняємось.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr.calendar__row")
    if not rows:
        rows = soup.select("table tr")

    today_local = datetime.now(LOCAL_TZ).date()
    in_today_section = False
    current_day: Optional[date] = None
    out: List[Dict[str, Any]] = []

    for tr in rows:
        # 1) Чи це рядок із заголовком дня?
        day_cell = tr.select_one(".calendar__date .date")
        if day_cell:
            d = _header_to_date(_text(day_cell), today_local)

            if not in_today_section:
                # шукаємо саме сьогодні
                if d == today_local:
                    in_today_section = True
                    current_day = d
                    # НЕ робимо 'continue' — парсимо цей же tr як подію today
                else:
                    # ще не today — пропускаємо цей хедер і всі рядки до наступного хедера
                    continue
            else:
                # ми вже в today-секції і бачимо наступний хедер -> закінчуємо парсинг
                break

        # 2) Якщо ми ще не ввійшли в today-секцію — пропускаємо рядки
        if not in_today_section:
            continue

        # 3) Назва події
        title_el = tr.select_one(".calendar__event .calendar__event-title") or tr.select_one(".calendar__event")
        title = _text(title_el)
        if not title:
            continue

        # 4) Час як рядок "на екрані"
        tt = _pick_time_string(tr)

        # 5) Impact
        impact = _norm_impact(_guess_impact_from_node(tr))
        if not impact and re.search(r"holiday|bank holiday|non[-\s]?economic", title, re.I):
            impact = "Non-economic"

        # 6) Перетворюємо лише для сортування всередині дня (без TZ)
        t_obj = _parse_ampm_time(tt) if tt else time(0, 0)

        # 7) Гарантуємо, що маємо дату дня (це «today»)
        day = current_day or today_local
        dt_local = datetime(day.year, day.month, day.day, t_obj.hour, t_obj.minute, t_obj.second)

        # 8) Додаємо подію
        out.append({
            "date": dt_local.isoformat(timespec="seconds"),  # локальний datetime без tz, як на сайті
            "title": title,
            "currency": "",
            "impact": impact,
            "url": None,
            "origin": origin,  # 'mm:today' або 'cc:today'
            "day_label": f"{day:%a %b %d}",
            "time_str": tt or "",
        })

    return out

def _parse_calendar_like(html: str, origin: str) -> List[Dict[str, Any]]:
    """
    Загальний парсер таблиці (все, що на сторінці) — БЕЗ конвертацій TZ, БЕЗ дедупу.
    Використовується для week.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr.calendar__row")
    if not rows:
        rows = soup.select("table tr")

    today_ref = datetime.now(LOCAL_TZ).date()
    current_day: Optional[date] = None
    out: List[Dict[str, Any]] = []

    for tr in rows:
        day_cell = tr.select_one(".calendar__date .date")
        if day_cell:
            d = _header_to_date(_text(day_cell), today_ref)
            if d:
                current_day = d
            continue

        title_el = tr.select_one(".calendar__event .calendar__event-title") or tr.select_one(".calendar__event")
        title = _text(title_el)
        if not title:
            continue

        tt = _pick_time_string(tr)
        impact = _norm_impact(_guess_impact_from_node(tr))
        if not impact and re.search(r"holiday|bank holiday|non[-\s]?economic", title, re.I):
            impact = "Non-economic"

        if current_day is None:
            current_day = today_ref

        t_obj = _parse_ampm_time(tt) if tt else time(0, 0)
        dt_local = datetime(
            current_day.year, current_day.month, current_day.day,
            t_obj.hour, t_obj.minute, t_obj.second
        )

        out.append({
            "date": dt_local.isoformat(timespec="seconds"),
            "title": title,
            "currency": "",
            "impact": impact,
            "url": None,
            "origin": origin,
            "day_label": f"{current_day:%a %b %d}",
            "time_str": tt or "",
        })

    return out

# ---------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------

async def _load_metals_today() -> List[Dict[str, Any]]:
    html = await _fetch_html("https://www.metalsmine.com/calendar?day=today", timeout=60)
    return _parse_calendar_today_only(html, origin="mm:today") if html else []

async def _load_metals_week() -> List[Dict[str, Any]]:
    html = await _fetch_html("https://www.metalsmine.com/calendar?week=this", timeout=60)
    return _parse_calendar_like(html, origin="mm:week") if html else []

async def _load_crypto_today() -> List[Dict[str, Any]]:
    html = await _fetch_html("https://www.cryptocraft.com/calendar?day=today", timeout=60)
    return _parse_calendar_today_only(html, origin="cc:today") if html else []

async def _load_crypto_week() -> List[Dict[str, Any]]:
    html = await _fetch_html("https://www.cryptocraft.com/calendar?week=this", timeout=60)
    return _parse_calendar_like(html, origin="cc:week") if html else []

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

async def refresh_cache() -> Dict[str, int]:
    """
    Оновлює агрегований JSON. Для metals/crypto — today+week, але
    /today у боті використовуватиме саме origin='*:today'.
    """
    fx_items = await _load_forex_thisweek()

    mm_today = await _load_metals_today()
    # mm_week  = await _load_metals_week()

    cc_today = await _load_crypto_today()
    # cc_week  = await _load_crypto_week()

    data = {
        "updated_at": _now_utc_iso(),
        "total_raw": len(fx_items) + len(mm_today) + len(cc_today),
        "forex": fx_items,
        "crypto": cc_today,   # без дедупу
        "metals": mm_today,   # без дедупу
    }

    os.makedirs(os.path.dirname(AGG_PATH), exist_ok=True)
    with open(AGG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log.info(
        "aggregator: JSON updated at %s (fx=%d, metals_today=%d, crypto_today=%d)",
        data["updated_at"], len(fx_items), len(mm_today), len(cc_today)
    )
    return {
        "total": data["total_raw"],
        "forex": len(fx_items),
        "crypto": len(cc_today),
        "metals": len(mm_today)
    }

def load_agg() -> Dict[str, Any]:
    if not os.path.exists(AGG_PATH):
        return {}
    try:
        with open(AGG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}