from datetime import datetime
from typing import Any, Dict, List
import httpx
from .models import FFEvent
from .utils import str_or_none
from .config import FF_THISWEEK, FF_NEXTWEEK, UTC
from .translator import translate_title

async def fetch_calendar(lang: str = "en") -> List[FFEvent]:
    data_all: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20) as client:
        for url in (FF_THISWEEK, FF_NEXTWEEK):
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, list):
                    data_all.extend(data)
            except Exception:
                continue

    events: List[FFEvent] = []
    for e in data_all:
        date_raw = e.get("date")
        if not date_raw:
            continue
        try:
            try:
                dt_utc = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).astimezone(UTC)
            except Exception:
                from dateutil import parser as dtparser  # type: ignore
                dt_utc = dtparser.parse(date_raw).astimezone(UTC)
        except Exception:
            continue

        title = str(e.get("title") or e.get("event") or "")
        # translate if needed
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

    # unique by (date,title,country,currency,impact)
    uniq = {}
    for ev in events:
        key = (ev.date, ev.title, ev.country, ev.currency, ev.impact)
        uniq[key] = ev
    return sorted(uniq.values(), key=lambda x: x.date)
