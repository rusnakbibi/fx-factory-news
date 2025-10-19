# app/ff_client.py
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

import os, json

from .models import FFEvent
from .utils import str_or_none
from .config import FF_THISWEEK, UTC
from .translator import translate_title

log = logging.getLogger(__name__)

# -------------------- shared http client --------------------
_CLIENT: Optional[httpx.AsyncClient] = None
_CLIENT_LOCK = asyncio.Lock()

async def _client() -> httpx.AsyncClient:
    global _CLIENT
    async with _CLIENT_LOCK:
        if _CLIENT is None:
            _CLIENT = httpx.AsyncClient(
                timeout=20,
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
                # http2=True,  # за бажанням
            )
        return _CLIENT

# -------------------- simple in-process cache --------------------
_CACHE_EVENTS: List[FFEvent] = []
_CACHE_EXPIRES: datetime = datetime.min.replace(tzinfo=UTC)
_CACHE_LOCK = asyncio.Lock()
_CACHE_TTL = timedelta(minutes=10)  # сміливо збільш до 15–30 хв

# Якщо попали на 429 з Retry-After — сюди запишемо «коли можна знову»
_NEXT_ALLOWED_FETCH: datetime = datetime.min.replace(tzinfo=UTC)

AGG_JSON_PATH = os.getenv("AGGREGATE_JSON_PATH", "aggregated_calendar.json")

def _now_utc() -> datetime:
    return datetime.now(UTC)

# -------------------- backoff-aware JSON fetch --------------------
async def _fetch_thisweek_json() -> List[Dict[str, Any]]:
    """
    Тягнемо ТІЛЬКИ thisweek.json з урахуванням 429 (Retry-After).
    Повертаємо список словників (сира відповідь).
    """
    global _NEXT_ALLOWED_FETCH
    now = _now_utc()

    # повага до попереднього Retry-After
    if now < _NEXT_ALLOWED_FETCH:
        wait = (_NEXT_ALLOWED_FETCH - now).total_seconds()
        log.info(f"[ff_client] backoff until {_NEXT_ALLOWED_FETCH.isoformat()} (sleep {wait:.1f}s)")
        await asyncio.sleep(min(wait, 30))  # не блокуємо надто довго
        # після сну не змушуємо одразу робити рекурсію — просто підемо далі

    cli = await _client()
    tries = 4
    backoff = 1.0

    for i in range(tries):
        r = await cli.get(FF_THISWEEK)
        if r.status_code == 200:
            try:
                data = r.json()
                return data if isinstance(data, list) else []
            except Exception as e:
                log.info(f"[ff_client] JSON decode error at {FF_THISWEEK}: {e}")
                return []

        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            # якщо Retry-After присутній — збережемо «коли можна»
            if ra and ra.isdigit():
                delay = float(ra)
            else:
                delay = backoff
            # джитер + експоненційний бекоф
            delay += random.uniform(0.2, 0.8)
            _NEXT_ALLOWED_FETCH = _now_utc() + timedelta(seconds=delay)
            log.info(f"[ff_client] 429 Too Many Requests; next allowed at {_NEXT_ALLOWED_FETCH.isoformat()} (try {i+1}/{tries})")
            await asyncio.sleep(delay)
            backoff = min(backoff * 2, 30)
            continue

        if r.status_code == 404:
            log.info(f"[ff_client] 404 at {FF_THISWEEK}")
            return []

        # інші статусы — коротка пауза і повтор
        log.info(f"[ff_client] HTTP {r.status_code} at {FF_THISWEEK}")
        await asyncio.sleep(0.5 + random.uniform(0, 0.5))

    log.info(f"[ff_client] giving up after retries for {FF_THISWEEK}")
    return []

# -------------------- public: cached this-week events --------------------
async def get_events_thisweek_cached(lang: str = "en") -> List[FFEvent]:
    """
    Тягне ТІЛЬКИ thisweek.json, будує FFEvent і кешує результат на _CACHE_TTL.
    - Якщо кеш свіжий — повертаємо його (cache: HIT).
    - Якщо ні — on-demand refresh (cache: MISS) з повагою до 429.
    """
    global _CACHE_EVENTS, _CACHE_EXPIRES
    now = _now_utc()

    async with _CACHE_LOCK:
        if now < _CACHE_EXPIRES and _CACHE_EVENTS:
            log.debug(f"[ff_client] cache: HIT ({len(_CACHE_EVENTS)} events) valid until {_CACHE_EXPIRES.isoformat()}")
            return _CACHE_EVENTS

        log.debug("[ff_client] cache: MISS — fetching thisweek.json")
        raw = await _fetch_thisweek_json()

        events: List[FFEvent] = []
        for e in raw or []:
            date_raw = e.get("date")
            if not date_raw:
                continue

            # Дата в UTC
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
        uniq: Dict[tuple, FFEvent] = {}
        for ev in events:
            uniq[(ev.date, ev.title, ev.country, ev.currency, ev.impact)] = ev
        result = sorted(uniq.values(), key=lambda x: x.date)

        _CACHE_EVENTS = result
        _CACHE_EXPIRES = now + _CACHE_TTL
        log.debug(f"[ff_client] cached {len(result)} events until {_CACHE_EXPIRES.isoformat()}")
        return result

# -------------------- compatibility wrapper --------------------
async def fetch_calendar(lang: str = "en") -> List[FFEvent]:
    """
    Зворотно-сумісна назва: тепер під капотом — кешований thisweek.
    Якщо далі додаватимеш інші діапазони (week/month) — розшириш тут.
    """
    return await get_events_thisweek_cached(lang=lang)

def load_aggregated_category(category: str, lang: str = "en") -> List[FFEvent]:
    if not os.path.exists(AGG_JSON_PATH):
        return []
    try:
        with open(AGG_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    items = data.get(category.lower(), []) or []
    out: List[FFEvent] = []
    for e in items:
        date_raw = str(e.get("date") or "")
        if not date_raw:
            continue
        try:
            try:
                dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).astimezone(UTC)
            except Exception:
                from dateutil import parser as dtp
                dt = dtp.parse(date_raw).astimezone(UTC)
        except Exception:
            continue

        title = str(e.get("title") or "")
        title_local = translate_title(title, lang)
        out.append(
            FFEvent(
                date=dt,
                title=title_local,
                country=str(e.get("country") or ""),
                currency=str(e.get("currency") or ""),
                impact=str(e.get("impact") or ""),
                forecast=None,
                previous=None,
                actual=None,
                url=e.get("url"),
                raw=e,
            )
        )
    return sorted(out, key=lambda x: x.date)