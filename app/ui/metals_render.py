# app/ui/metals_render.py
from __future__ import annotations
from typing import List
from ..core.models import MMEvent
from ..utils.helpers import chunk
from ..config.settings import LOCAL_TZ

def build_grouped_blocks(events: List[MMEvent], prefix: str = "", lang: str = "en") -> List[str]:
    """
    Групує події по днях і повертає список блоків тексту для відправки.
    Кожен блок — це окреме повідомлення в Telegram.
    """
    if not events:
        return []

    # Групуємо події по днях (в локальному часі)
    by_day = {}
    for ev in events:
        # Convert UTC to local timezone for grouping
        local_dt = ev.dt_utc.astimezone(LOCAL_TZ)
        day_key = local_dt.strftime("%Y-%m-%d")
        if day_key not in by_day:
            by_day[day_key] = []
        by_day[day_key].append(ev)

    # Сортуємо дні
    sorted_days = sorted(by_day.keys())

    blocks = []
    for day_key in sorted_days:
        day_events = by_day[day_key]
        day_events.sort(key=lambda e: e.dt_utc)

        # Заголовок дня (в локальному часі)
        first_event = day_events[0]
        local_dt = first_event.dt_utc.astimezone(LOCAL_TZ)
        day_header = local_dt.strftime("%A, %B %d")
        
        if prefix:
            header = f"🪙 <b>{prefix} — {day_header}</b>\n"
        else:
            header = f"🪙 <b>{day_header}</b>\n"

        # Розбиваємо події на чанки по 8
        for pack in chunk(day_events, 8):
            body = "\n\n".join(mm_event_to_card_text(ev, lang) for ev in pack)
            blocks.append(header + body)
            header = ""  # Тільки перший чанк має заголовок

    return blocks

def mm_event_to_card_text(ev: MMEvent, lang: str = "en") -> str:
    """
    Форматує подію металу в картку для відображення.
    """
    from ..services.metals_parser import mm_event_to_card_text as _mm_event_to_card_text
    return _mm_event_to_card_text(ev, lang)
