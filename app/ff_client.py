from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
import logging

import httpx
from httpx import HTTPStatusError

from .models import FFEvent
from .utils import str_or_none
from .config import FF_THISWEEK, FF_NEXTWEEK, UTC
from .translator import translate_title

log = logging.getLogger(__name__)

async def fetch_calendar(lang: str = "en") -> List[FFEvent]:
    """
    Тягне JSON із ForexFactory. Для today достатньо THISWEEK,
    але NEXTWEEK лишаю як опцію (можеш забрати, якщо хочеш мінімум).
    """
    data_all: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=20) as client:
        for url in (FF_THISWEEK, FF_NEXTWEEK):
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, list) and data:
                    data_all.extend(data)
                    log.debug(f"[ff_client] loaded {len(data)} items from {url}")
                else:
                    log.debug(f"[ff_client] empty/invalid list at {url}")
            except HTTPStatusError as e:
                # 404 для nextweek буває — не критично
                log.info(f"[ff_client] HTTP {e.response.status_code} at {url}")
            except Exception as e:
                log.warning(f"[ff_client] error at {url}: {e}")

    events: List[FFEvent] = []
    for e in data_all:
        date_raw = e.get("date")
        if not date_raw:
            continue
        try:
            try:
                dt_utc = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00")).astimezone(UTC)
            except Exception:
                from dateutil import parser as dtparser  # type: ignore
                dt_utc = dtparser.parse(str(date_raw)).astimezone(UTC)
        except Exception:
            continue

        title = str(e.get("title") or e.get("event") or "")
        title_local = translate_title(title, lang)

        events.append(
            FFEvent(
                date=dt_utc,
                title=title_local,
                country=str(e.get("country") or e.get("countryCode") or ""),
                currency=str(e.get("currency") or ""),
                impact=str(e.get("impact") or ""),
                forecast=str_or_none(e.get("forecast")),
                previous=str_or_none(e.get("previous")),
                actual=str_or_none(e.get("actual")),
                url=str(e.get("url") or e.get("link") or "") or None,
                raw=e,
            )
        )

    # унікалізація + сортування
    uniq = {}
    for ev in events:
        key = (ev.date, ev.title, ev.country, ev.currency, ev.impact)
        uniq[key] = ev
    result = sorted(uniq.values(), key=lambda x: x.date)

    log.debug(f"[ff_client] returning events: {len(result)}")
    return result