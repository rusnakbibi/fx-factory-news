# app/ff_client.py
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

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

# -------------------- backoff state for 429 --------------------
_NEXT_ALLOWED_FETCH: datetime = datetime.min.replace(tzinfo=UTC)

def _now_utc() -> datetime:
    return datetime.now(UTC)

# -------------------- simple in-process cache --------------------
# Кешуємо готові FFEvent на TTL окремо по мові (lang)
_CACHE_TTL_SECONDS = int(os.getenv("FF_FX_TTL", "120"))  # дефолт 120 с (2 хв)
_TW_CACHE: Dict[Tuple[str], Tuple[float, List[FFEvent]]] = {}  # key=(lang,) -> (expires_epoch, events)
_CACHE_LOCK = asyncio.Lock()
_CACHE_EVENTS: List[FFEvent] = []
_CACHE_EXPIRES: datetime = datetime.min.replace(tzinfo=UTC)
_CACHE_TTL = timedelta(minutes=10)

# -------------------- low-level fetch: thisweek.json --------------------
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
        log.info("[ff_client] backoff until %s (sleep %.1fs)", _NEXT_ALLOWED_FETCH.isoformat(), wait)
        # не блокуємо надто довго одним сном
        await asyncio.sleep(min(wait, 30))

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
                log.info("[ff_client] JSON decode error at %s: %s", FF_THISWEEK, e)
                return []

        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            if ra and ra.isdigit():
                delay = float(ra)
            else:
                delay = backoff
            delay += random.uniform(0.2, 0.8)  # джитер
            _NEXT_ALLOWED_FETCH = _now_utc() + timedelta(seconds=delay)
            log.info("[ff_client] 429; next allowed at %s (try %d/%d)", _NEXT_ALLOWED_FETCH.isoformat(), i + 1, tries)
            await asyncio.sleep(delay)
            backoff = min(backoff * 2, 30)
            continue

        if r.status_code == 404:
            log.info("[ff_client] 404 at %s", FF_THISWEEK)
            return []

        # інші статуси — коротка пауза і повтор
        log.info("[ff_client] HTTP %s at %s", r.status_code, FF_THISWEEK)
        await asyncio.sleep(0.5 + random.uniform(0, 0.5))

    log.info("[ff_client] giving up after retries for %s", FF_THISWEEK)
    return []

# -------------------- public: cached this-week events --------------------
async def get_events_thisweek_cached(lang: str = "en") -> List[FFEvent]:
    """
    Тягне thisweek.json, будує FFEvent і кешує результат на _CACHE_TTL_SECONDS.
    Якщо кеш свіжий — повертає його без мережевого запиту.
    """
    key = (lang,)
    now_epoch = time.time()

    async with _CACHE_LOCK:
        cached = _TW_CACHE.get(key)
        if cached:
            expires_at, events = cached
            if now_epoch < expires_at:
                log.debug("[ff_client] cache HIT (lang=%s, ttl_left=%.0fs, count=%d)",
                          lang, expires_at - now_epoch, len(events))
                return events
            # прострочено — видалимо
            _TW_CACHE.pop(key, None)

    # MISS: тягнемо сирі дані
    raw = await _fetch_thisweek_json()

    events: List[FFEvent] = []
    for e in raw or []:
        date_raw = e.get("date")
        if not date_raw:
            continue

        # Нормалізуємо дату в UTC (aware)
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

    # покладемо в кеш
    async with _CACHE_LOCK:
        _TW_CACHE[key] = (time.time() + _CACHE_TTL_SECONDS, result)
    log.info("[ff_client] thisweek fetched & cached (lang=%s, ttl=%ss, count=%d)",
             lang, _CACHE_TTL_SECONDS, len(result))
    return result

# Зворотно-сумісний псевдонім (якщо десь ще використовується)
async def fetch_calendar(lang: str = "en") -> List[FFEvent]:
    return await get_events_thisweek_cached(lang=lang)

def clear_ff_cache() -> int:
    """
    Повністю очищає in-memory кеш thisweek.json.
    НЕ чіпає логіку отримання подій; наступний виклик get_events_thisweek_cached
    зробить мережевий запит і знову заповнить кеш.
    Повертає кількість очищених записів.
    """
    try:
        n = len(_TW_CACHE)
        _TW_CACHE.clear()
        return n
    except Exception:
        return 0


# -------------------- auto-refresh loop (optional) --------------------
_FF_REFRESH_MINUTES = int(os.getenv("FF_REFRESH_MINUTES", "60"))
_AUTOREFRESH_TASK: Optional[asyncio.Task] = None
_AUTOREFRESH_LOCK = asyncio.Lock()

async def _autorefresh_loop():
    """
    Періодично освіжає in-memory кеш thisweek.json.
    Повага до 429 уже всередині _fetch_thisweek_json().
    """
    interval = max(5, _FF_REFRESH_MINUTES)  # мінімум 5 хв, щоб не зловживати
    log.info(f"[ff_client] autorefresh: started (every {interval} min)")
    try:
        while True:
            try:
                await get_events_thisweek_cached(lang="en")
            except Exception as e:
                log.warning(f"[ff_client] autorefresh tick failed: {e}")
            # спимо «м’яко», щоб можна було коректно зупинити
            for _ in range(interval * 6):  # кроками по 10 сек
                await asyncio.sleep(10)
            # по таймеру піде наступна ітерація
    except asyncio.CancelledError:
        log.info("[ff_client] autorefresh: cancelled")
        raise
    except Exception as e:
        log.exception(f"[ff_client] autorefresh crashed: {e}")

async def start_autorefresh() -> None:
    """
    Запускає фонову задачу автооновлення (одноразово).
    Викликати один раз при старті бота.
    """
    global _AUTOREFRESH_TASK
    async with _AUTOREFRESH_LOCK:
        if _AUTOREFRESH_TASK and not _AUTOREFRESH_TASK.done():
            return
        _AUTOREFRESH_TASK = asyncio.create_task(_autorefresh_loop(), name="ff_autorefresh")

async def stop_autorefresh() -> None:
    """
    Акуратно зупиняє фонову задачу (якщо потрібен graceful shutdown).
    """
    global _AUTOREFRESH_TASK
    async with _AUTOREFRESH_LOCK:
        if _AUTOREFRESH_TASK and not _AUTOREFRESH_TASK.done():
            _AUTOREFRESH_TASK.cancel()
            try:
                await _AUTOREFRESH_TASK
            except asyncio.CancelledError:
                pass
        _AUTOREFRESH_TASK = None

def get_cache_meta(lang: str = "en") -> Dict[str, Any]:
    """
    Повертає метадані поточного кешу thisweek.json:
      - count: кількість подій у кеші (0, якщо прострочено/порожньо)
      - valid_until: ISO-час в UTC, доки кеш чинний (або '—', якщо кешу немає)
      - ttl_minutes: тривалість TTL у хвилинах (з _CACHE_TTL_SECONDS)
    НЕ змінює логіку get_events_thisweek_cached.
    Очікує структуру _TW_CACHE: {(lang,): (expires_at_epoch, [FFEvent, ...])}
    """
    try:
        now = time.time()
        ttl_minutes = int((_CACHE_TTL_SECONDS or 600) // 60)

        item = _TW_CACHE.get((lang,))
        if not item and _TW_CACHE:
            # якщо для цієї мови ще нема, візьмемо найсвіжіший запис
            item = max(_TW_CACHE.values(), key=lambda x: x[0])

        if not item:
            return {"count": 0, "valid_until": "—", "ttl_minutes": ttl_minutes}

        expires_at, events = item
        valid_until_iso = datetime.fromtimestamp(expires_at, tz=UTC).replace(microsecond=0).isoformat()

        # якщо протух — рахуємо як 0 подій, але показуємо до якого часу був чинний
        if now >= expires_at:
            return {"count": 0, "valid_until": valid_until_iso, "ttl_minutes": ttl_minutes}

        return {"count": len(events or []), "valid_until": valid_until_iso, "ttl_minutes": ttl_minutes}
    except Exception:
        return {"count": 0, "valid_until": "—", "ttl_minutes": int((_CACHE_TTL_SECONDS or 600) // 60)}