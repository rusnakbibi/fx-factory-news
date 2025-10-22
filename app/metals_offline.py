# app/metals_offline.py
from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup  # pip install beautifulsoup4
from .config import LOCAL_TZ, UTC

# ===== Модель події =====
@dataclass
class MMEvent:
    dt_utc: datetime
    time_str: str          # "HH:MM" у 24h
    title: str
    impact: str | None = None
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    date_label: str = "" 
    source: str = "MetalsMine (offline)"

# ===== Утиліти часу =====
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*([ap]m)?", re.I)
_TIME_HHMM = re.compile(r"^\d{2}:\d{2}$")

def _extract_hhmm_from_time_cell(time_cell) -> str:
    """
    Повертає 'HH:MM' або '' якщо часу немає/невизначений (Tentative, All Day, TBA…).
    Беремо саме ОСТАННІЙ <span> з текстом у комірці .calendar__time.
    """
    if not time_cell:
        return ""
    spans = [s.get_text(strip=True) for s in time_cell.select("span")]
    for txt in reversed(spans):
        if not txt:
            continue
        low = txt.lower()
        # явні "не-часи"
        if any(k in low for k in ("tentative", "all day", "tba", "tbd", "—", "-")):
            return ""
        # 12h → 24h
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([ap]m)\s*$", txt, re.I)
        if m:
            h, mm, ap = int(m.group(1)), m.group(2), m.group(3).lower()
            if ap == "am":
                if h == 12: h = 0
            else:
                if h != 12: h += 12
            return f"{h:02d}:{mm}"
        # вже у 24h?
        if _TIME_HHMM.fullmatch(txt):
            return txt
    return ""

def _to_24h(txt: str) -> str:
    """ '8:00am' -> '08:00'; бере ОСТАННІЙ <span> у комірці часу. """
    txt = (txt or "").strip()
    m = _TIME_RE.search(txt)
    if not m:
        return ""
    h, mnt, ap = int(m.group(1)), m.group(2), (m.group(3) or "").lower()
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return f"{h:02d}:{mnt}"

def _compose_dt_today(local_hhmm: str) -> datetime:
    """ Склеює локальну дату сьогодні + HH:MM -> UTC datetime. """
    now_local = datetime.now(LOCAL_TZ)
    base = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        hh, mm = map(int, (local_hhmm or "00:00").split(":"))
    except Exception:
        hh, mm = 0, 0
    dt_local = base.replace(hour=hh, minute=mm)
    return dt_local.astimezone(UTC)

# ===== Рендер у текст для Telegram =====
def mm_event_to_text(ev: MMEvent) -> str:
    t_local = ev.dt_utc.astimezone(LOCAL_TZ).strftime("%a %H:%M")
    head = f"• {t_local} — <b>{ev.title}</b>"
    if ev.impact:
        head += f" ({ev.impact})"
    tail = []
    if ev.actual:   tail.append(f"Actual: <b>{ev.actual}</b>")
    if ev.forecast: tail.append(f"Forecast: {ev.forecast}")
    if ev.previous: tail.append(f"Previous: {ev.previous}")
    return head if not tail else head + "\n" + " | ".join(tail)

_IMPACT_EMOJI = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Non-economic": "⚪️",
    "": "•",
}

# короткий код → назва країни (для другого рядка)
_COUNTRY_NAMES = {
    "US": "United States",
    "UK": "United Kingdom",
    "EZ": "Eurozone",
    "EU": "Eurozone",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "CH": "Switzerland",
    "CA": "Canada",
    "JP": "Japan",
    "CN": "China",
    "AU": "Australia",
    "NZ": "New Zealand",
    "MX": "Mexico",
    "RU": "Russia",
    "SA": "South Africa",
    # доповниш за потреби
}

def _split_country_prefix(title: str) -> tuple[str, str]:
    """
    Багато подій мають префікс типу 'UK ...', 'EZ ...'.
    Повертає (country_code, clean_title).
    Якщо префікса нема — ('', title).
    """
    s = title.strip()
    parts = s.split(" ", 1)
    if len(parts) == 2 and parts[0].isupper() and 2 <= len(parts[0]) <= 3:
        return parts[0], parts[1].strip()
    return "", s

def mm_event_to_card_text(ev: MMEvent, lang: str = "ua") -> str:
    """
    Рендер у форматі як на скріні з форекса:
    • Wed 09:00 — 🔴 CPI y/y
    Country
    Forecast: ... | Previous: ... (і Actual: ... якщо є)
    """
    # час у локалі
    t_local = ev.dt_utc.astimezone(LOCAL_TZ).strftime("%a %H:%M")

    # impact → emoji
    impact_norm = (ev.impact or "").strip().title()
    if impact_norm not in _IMPACT_EMOJI:
        # інколи з парсера приходить '' — лишимо крапку або ⚪️
        impact_norm = "Non-economic" if not ev.impact else impact_norm
    emoji = _IMPACT_EMOJI.get(impact_norm, "•")

    # країна з префікса в заголовку
    code, clean_title = _split_country_prefix(ev.title or "")
    country_line = ""
    if code:
        name = _COUNTRY_NAMES.get(code, code)
        country_line = f"{name}"

    # складання рядків
    head = f"• {t_local} — {emoji} <b>{clean_title or (ev.title or '').strip()}</b>"
    stats = []
    if ev.actual:
        stats.append(f"Actual: <b>{ev.actual}</b>")
    if ev.forecast:
        stats.append(f"Forecast: {ev.forecast}")
    if ev.previous:
        stats.append(f"Previous: {ev.previous}")

    lines = [head]
    if country_line:
        lines.append(country_line)
    if stats:
        lines.append(" | ".join(stats))
    return "\n".join(lines)

# ===== Основний парсер =====
def parse_metals_today_html(page_html: str) -> List[MMEvent]:
    """
    Парсить таблицю MetalsMine (сторінка 'today', що ти кидаєш файлом).
    Враховано:
      1) .calendar__row і .calendar__row--no-grid — другі успадковують час
      2) у комірці часу перший <span> може бути іконкою → беремо останній <span> з текстом
      3) визначення impact за <img src*="mm-impact-...png">:
         yel → Low, ora → Medium, red → High, gra → Non-economic
    """
    soup = BeautifulSoup(page_html, "html.parser")

    rows = soup.select("tr.calendar__row")
    events: List[MMEvent] = []
    last_time_24 = ""

    for tr in rows:
        classes = tr.get("class", []) or []
        if "calendar__row--day-breaker" in classes:
            last_time_24 = ""
            continue

        title_el = tr.select_one(".calendar__event-title")
        if not title_el:
            continue
        title = title_el.get_text(" ", strip=True)

        # ---- TIME ---- (останній span із текстом)
        time_cell = tr.select_one(".calendar__cell.calendar__time")
        cur_time_24 = _extract_hhmm_from_time_cell(time_cell)
        if time_cell:
            spans = [s.get_text(strip=True) for s in time_cell.select("span")]
            for txt in reversed(spans):
                if txt:
                    # txt типу "8:00am" → "08:00"
                    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([ap]m)\s*$", txt, re.I)
                    if m:
                        h, mm, ap = int(m.group(1)), m.group(2), m.group(3).lower()
                        if ap == "am":
                            if h == 12: h = 0
                        else:
                            if h != 12: h += 12
                        cur_time_24 = f"{h:02d}:{mm}"
                    else:
                        # якщо вже у 24h
                        cur_time_24 = txt
                    if cur_time_24:
                        break

        is_no_grid = "calendar__row--no-grid" in classes
        if not cur_time_24 and is_no_grid and _TIME_HHMM.fullmatch(last_time_24 or ""):
            cur_time_24 = last_time_24
        if _TIME_HHMM.fullmatch(cur_time_24 or ""):
            last_time_24 = cur_time_24
        if cur_time_24:
            last_time_24 = cur_time_24
        

        # ---- IMPACT ---- (mm-impact-*)
        impact = None
        img = tr.select_one('td.calendar__cell.calendar__impact img[src*="mm-impact-"]')
        if img:
            src = img.get("src", "")
            if "mm-impact-yel" in src:
                impact = "Low"
            elif "mm-impact-ora" in src:
                impact = "Medium"
            elif "mm-impact-red" in src:
                impact = "High"
            elif "mm-impact-gra" in src:
                impact = "Non-economic"

        # ---- OTHER COLUMNS ----
        def _val(sel: str) -> Optional[str]:
            el = tr.select_one(sel)
            if not el:
                return None
            sp = el.select_one("span")
            txt = (sp.get_text(strip=True) if sp else el.get_text(strip=True)) or ""
            return html.unescape(txt) or None

        actual   = _val(".calendar__cell.calendar__actual")
        forecast = _val(".calendar__cell.calendar__forecast")
        previous = _val(".calendar__cell.calendar__previous")

        # ---- datetime для сьогоднішньої дати у LOCAL_TZ → UTC
        today_local = datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        hhmm = cur_time_24 if _TIME_HHMM.fullmatch(cur_time_24 or "") else "00:00"
        try:
            h, m = map(int, hhmm.split(":"))
        except Exception:
            h, m = 0, 0
        dt_local = today_local.replace(hour=h, minute=m)
        dt_utc = dt_local.astimezone(UTC)

        events.append(MMEvent(
            dt_utc=dt_utc,
            date_label=today_local.strftime("%a %b %d"),
            time_str=hhmm,
            impact=impact or "",
            title=title,
            actual=actual,
            forecast=forecast,
            previous=previous,
        ))

    events.sort(key=lambda e: e.dt_utc)
    return events

# ===== API офлайн: зчитати файл і спарсити =====
def load_today_from_file(file_path: str) -> List[MMEvent]:
    """
    Зчитує локальний HTML-файл і повертає події за 'today' (у файлі вже тільки сьогодні).
    """
    p = Path(file_path)
    if not p.exists() or p.stat().st_size == 0:
        raise FileNotFoundError(f"Metals HTML not found or empty: {file_path}")
    text = p.read_text(encoding="utf-8", errors="ignore")
    return parse_metals_today_html(text)