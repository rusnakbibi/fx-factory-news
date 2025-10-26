# app/metals_offline_week.py
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup
from .config import LOCAL_TZ, UTC

# ===== Модель така ж, як у metals_offline.py =====
@dataclass
class MMEvent:
    dt_utc: datetime
    time_str: str           # "HH:MM" у 24h
    title: str
    impact: str | None = None
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    date_label: str = ""    # напр. "Wed Oct 22"
    source: str = "MetalsMine (offline week)"

# ===== Утиліти =====
TIME_AMPM_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*([ap]m)\s*$", re.I)

def _to_24h(txt: str) -> str:
    txt = (txt or "").strip()
    m = TIME_AMPM_RE.search(txt)
    if not m:
        return txt
    h, mm, ap = int(m.group(1)), m.group(2), m.group(3).lower()
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return f"{h:02d}:{mm}"

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

def _pick_time_from_cell(cell_html: str) -> str:
    """
    У клітинці часу перший <span> часто – іконка. Беремо останній <span> з текстом.
    """
    spans = re.findall(r"<span[^>]*>([^<]*)</span>", cell_html, re.I | re.S)
    for raw in reversed(spans):
        raw = (raw or "").strip()
        if not raw:
            continue
        t24 = _to_24h(raw)
        if t24:
            return t24
    return ""

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
            cur_time_24 = ""
            time_cell = tr.select_one(".calendar__cell.calendar__time")
            if time_cell:
                cur_time_24 = _pick_time_from_cell(str(time_cell))

            # наслідування часу для no-grid
            if not cur_time_24 and "calendar__row--no-grid" in classes and last_time_24:
                cur_time_24 = last_time_24
            if cur_time_24:
                last_time_24 = cur_time_24
            else:
                # “Day X”, “Tentative”, пусто → залишимо "00:00"
                cur_time_24 = "00:00"

            # 5) impact
            impact = ""
            img = tr.select_one('td.calendar__cell.calendar__impact img[src*="mm-impact-"]')
            if img:
                impact = _impact_from_img(img.get("src"))

            # 6) інші колонки
            actual   = _val_from_cell(tr, ".calendar__cell.calendar__actual")
            forecast = _val_from_cell(tr, ".calendar__cell.calendar__forecast")
            previous = _val_from_cell(tr, ".calendar__cell.calendar__previous")

            dt_utc = _compose_dt(current_day_local, cur_time_24)

            events.append(MMEvent(
                dt_utc=dt_utc,
                time_str=cur_time_24,
                title=title,
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