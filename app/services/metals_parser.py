# app/services/metals_parser.py
from __future__ import annotations

import html
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup  # pip install beautifulsoup4
from ..core.models import MMEvent
from ..config.settings import LOCAL_TZ, UTC

# ===== Утиліти часу =====
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*([ap]m)?", re.I)
_TIME_HHMM = re.compile(r"^\d{2}:\d{2}$")

def _extract_hhmm_from_time_cell(time_cell) -> tuple[str, str]:
    """
    Повертає (time_for_display, time_for_calculation).
    - time_for_display: 'HH:MM' або 'All Day'/'Tentative'/'TBA' тощо
    - time_for_calculation: 'HH:MM' (або '12:00' для non-time labels)
    
    Беремо саме ОСТАННІЙ <span> з текстом у комірці .calendar__time.
    """
    if not time_cell:
        return "", "12:00"
    spans = [s.get_text(strip=True) for s in time_cell.select("span")]
    for txt in reversed(spans):
        if not txt:
            continue
        low = txt.lower()
        # явні "не-часи" - повертаємо оригінальний текст для показу
        if any(k in low for k in ("tentative", "all day", "tba", "tbd")):
            return txt, "12:00"  # Show label, but calculate with noon
        # Day X
        if low.startswith("day "):
            return txt, "12:00"
        # 12h → 24h
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([ap]m)\s*$", txt, re.I)
        if m:
            h, mm, ap = int(m.group(1)), m.group(2), m.group(3).lower()
            if ap == "am":
                if h == 12: h = 0
            else:
                if h != 12: h += 12
            time24 = f"{h:02d}:{mm}"
            return time24, time24  # Both display and calculation use same time
        # вже у 24h?
        if _TIME_HHMM.fullmatch(txt):
            return txt, txt  # Both display and calculation use same time
    return "", "12:00"

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
def mm_event_to_text(ev: MMEvent, lang: str = "en") -> str:
    from .translator import translate_metals_title
    
    # Use time_str which may contain labels like "All Day", "Tentative", or actual time
    day_label = ev.dt_utc.astimezone(LOCAL_TZ).strftime("%a")
    time_part = ev.time_str or "12:00"  # Fallback to 12:00 if empty
    t_local = f"{day_label} {time_part}"
    
    # Translate the title
    translated_title = translate_metals_title(ev.title, lang)
    
    head = f"• {t_local} — <b>{translated_title}</b>"
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

def _esc(s: str | None) -> str:
    if s is None:
        return ""
    # Мінімальна екранізація для Telegram HTML
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )

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
    • Wed 09:00 — 🔴 Title
    OR
    • Wed All Day — 🔴 Title
    Country
    Actual/Forecast/Previous ...
    """
    from .translator import translate_metals_title
    
    # Use time_str which may contain labels like "All Day", "Tentative", or actual time
    day_label = ev.dt_utc.astimezone(LOCAL_TZ).strftime("%a")
    time_part = ev.time_str or "12:00"  # Fallback to 12:00 if empty
    t_local = f"{day_label} {time_part}"

    impact_norm = (ev.impact or "").strip().title()
    if impact_norm not in _IMPACT_EMOJI:
        impact_norm = "Non-economic" if not ev.impact else impact_norm
    emoji = _IMPACT_EMOJI.get(impact_norm, "•")

    # країна з префікса
    code, clean_title = _split_country_prefix(ev.title or "")
    country_line = ""
    if code:
        name = _COUNTRY_NAMES.get(code, code)
        country_line = _esc(name)

    # Translate the title
    title_to_display = clean_title or (ev.title or '').strip()
    translated_title = translate_metals_title(title_to_display, lang)
    
    head = f"• {t_local} — {emoji} <b>{_esc(translated_title)}</b>"

    stats = []
    if ev.actual:
        stats.append(f"Actual: <b>{_esc(ev.actual)}</b>")
    if ev.forecast:
        stats.append(f"Forecast: {_esc(ev.forecast)}")
    if ev.previous:
        stats.append(f"Previous: {_esc(ev.previous)}")

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
        time_display, time_calc = _extract_hhmm_from_time_cell(time_cell)

        is_no_grid = "calendar__row--no-grid" in classes
        # Inherit time from previous row if no-grid and no time specified
        if (not time_display or not time_calc or time_calc == "12:00") and is_no_grid and last_time_24:
            time_calc = last_time_24
            time_display = last_time_24
        
        # Update last_time_24 if we have a real time (not a label)
        if time_calc and _TIME_HHMM.fullmatch(time_calc):
            last_time_24 = time_calc
        

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

        # ---- Extract country code from title (e.g., "UK CPI y/y" → "UK")
        country_code, _ = _split_country_prefix(title)
        
        # ---- datetime для сьогоднішньої дати у LOCAL_TZ → UTC
        today_local = datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        # Use time_calc for datetime calculation (always HH:MM format)
        # Use time_display for showing to user (may be "All Day", "Tentative", etc.)
        try:
            h, m = map(int, time_calc.split(":"))
        except Exception:
            h, m = 12, 0  # Default to noon if parsing fails
        dt_local = today_local.replace(hour=h, minute=m)
        dt_utc = dt_local.astimezone(UTC)

        events.append(MMEvent(
            dt_utc=dt_utc,
            date_label=today_local.strftime("%a %b %d"),
            time_str=time_display or time_calc,  # Show label if available, otherwise show time
            country=country_code or None,
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

# ===== Week parsing utilities =====
TIME_AMPM_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*([ap]m)\s*$", re.I)

def _impact_from_img(src: str | None) -> str:
    s = (src or "")
    if "mm-impact-red" in s: return "High"
    if "mm-impact-ora" in s: return "Medium"
    if "mm-impact-yel" in s: return "Low"
    if "mm-impact-gra" in s: return "Non-economic"
    return ""

def _local_day_from_label(label: str) -> datetime:
    """
    'Sun Oct 19' → локальна північ цього дня (aware, zoneinfo).
    """
    year = datetime.now(LOCAL_TZ).year
    try:
        d = datetime.strptime(f"{label.strip()} {year}", "%a %b %d %Y")
    except ValueError:
        # fallback: сьогодні 00:00
        d = datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        return d
    # zoneinfo: просто встановлюємо tzinfo
    d = d.replace(tzinfo=LOCAL_TZ)
    return d.replace(hour=0, minute=0, second=0, microsecond=0)

def _compose_dt(local_day: datetime, hhmm: str) -> datetime:
    try:
        h, m = map(int, (hhmm or "00:00").split(":"))
    except Exception:
        h, m = 0, 0
    dt_local = local_day.replace(hour=h, minute=m, second=0, microsecond=0)
    return dt_local.astimezone(UTC)

def _pick_time_from_cell(cell_html: str) -> tuple[str, str]:
    """
    У клітинці часу перший <span> часто – іконка. Беремо останній <span> з текстом.
    Повертає (time_for_display, time_for_calculation).
    """
    spans = re.findall(r"<span[^>]*>([^<]*)</span>", cell_html, re.I | re.S)
    for raw in reversed(spans):
        raw = (raw or "").strip()
        if not raw:
            continue
        low = raw.lower()
        # Check for non-time labels
        if any(k in low for k in ("tentative", "all day", "tba", "tbd")):
            return raw, "12:00"  # Show label, calculate with noon
        if low.startswith("day "):
            return raw, "12:00"
        # Try to convert to 24h time
        t24 = _to_24h(raw)
        if t24:
            return t24, t24  # Both display and calculation use same time
    return "", "12:00"

def _val_from_cell(tr: BeautifulSoup, sel: str) -> Optional[str]:
    el = tr.select_one(sel)
    if not el:
        return None
    sp = el.select_one("span")
    txt = (sp.get_text(strip=True) if sp else el.get_text(strip=True)) or ""
    return html.unescape(txt) or None

# ===== Основний парсер тижня =====
def parse_metals_week_html(page_html: str) -> List[MMEvent]:
    """
    Парсинг 'this week' HTML: у DOM кожен день у власному <tbody>.
    Скидаємо контекст дня/часу на початку кожного tbody та
    беремо дату з:
      - tr.calendar__row--day-breaker (текст вигляду 'Sun Oct 19')
      - або з td.calendar__date (там та сама строка)
    """
    soup = BeautifulSoup(page_html, "html.parser")
    tbodies = soup.select("tbody")
    if not tbodies:
        tbodies = [soup]

    events: List[MMEvent] = []

    for tbody in tbodies:
        current_day_local: Optional[datetime] = None
        last_time_24 = ""

        rows = tbody.select("tr.calendar__row")
        if not rows:
            continue

        for tr in rows:
            classes = tr.get("class", []) or []

            # 1) day-breaker: містить текст 'Sun Oct 19'
            if "calendar__row--day-breaker" in classes:
                cell = tr.select_one(".calendar__cell")
                if cell:
                    # get_text збирає і текст, і <span>, напр. "Sun Oct 19"
                    label = cell.get_text(" ", strip=True)
                    if label:
                        current_day_local = _local_day_from_label(label)
                        last_time_24 = ""
                continue

            # 2) подія — заголовок
            title_el = tr.select_one(".calendar__event-title")
            if not title_el:
                continue
            title = title_el.get_text(" ", strip=True)

            # 3) якщо дня ще нема — спробуємо витягнути з колонки дати
            if current_day_local is None:
                date_cell = tr.select_one(".calendar__cell.calendar__date")
                if date_cell:
                    label = date_cell.get_text(" ", strip=True)
                    if label:
                        current_day_local = _local_day_from_label(label)
                        last_time_24 = ""

            if current_day_local is None:
                # останній захист — сьогодні 00:00 локально
                current_day_local = datetime.now(LOCAL_TZ).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            # 4) час
            time_display = ""
            time_calc = "12:00"
            time_cell = tr.select_one(".calendar__cell.calendar__time")
            if time_cell:
                time_display, time_calc = _pick_time_from_cell(str(time_cell))

            # наслідування часу для no-grid
            if (not time_display or not time_calc or time_calc == "12:00") and "calendar__row--no-grid" in classes and last_time_24:
                time_calc = last_time_24
                time_display = last_time_24
            
            # Update last_time_24 if we have a real time (not a label)
            if time_calc and _TIME_HHMM.fullmatch(time_calc):
                last_time_24 = time_calc

            # 5) impact
            impact = ""
            img = tr.select_one('td.calendar__cell.calendar__impact img[src*="mm-impact-"]')
            if img:
                impact = _impact_from_img(img.get("src"))

            # 6) інші колонки
            actual   = _val_from_cell(tr, ".calendar__cell.calendar__actual")
            forecast = _val_from_cell(tr, ".calendar__cell.calendar__forecast")
            previous = _val_from_cell(tr, ".calendar__cell.calendar__previous")

            # Extract country code from title
            country_code, _ = _split_country_prefix(title)

            # Use time_calc for datetime, time_display for showing to user
            dt_utc = _compose_dt(current_day_local, time_calc)

            events.append(MMEvent(
                dt_utc=dt_utc,
                time_str=time_display or time_calc,  # Show label if available, otherwise show time
                title=title,
                country=country_code or None,
                impact=impact,
                actual=actual,
                forecast=forecast,
                previous=previous,
                date_label=current_day_local.strftime("%a %b %d"),
                source="MetalsMine (offline week)",
            ))

    # Сортування за datetime; при рівних — стабільне (за порядком появи)
    events.sort(key=lambda e: (e.dt_utc, e.title))
    return events

# ===== API: читання локального HTML тижня =====
def load_week_from_file(file_path: str) -> List[MMEvent]:
    """
    Зчитує локальний HTML із MetalsMine (week=this) і повертає усі події тижня.
    """
    p = Path(file_path)
    if not p.exists() or p.stat().st_size == 0:
        raise FileNotFoundError(f"Metals week HTML not found or empty: {file_path}")
    text = p.read_text(encoding="utf-8", errors="ignore")
    return parse_metals_week_html(text)
