# app/filters.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Set
import re

from .models import FFEvent

# ---- нормалізація -------------------------------------------------

_IMPACT_ALIASES = {
    "high": "High",
    "medium": "Medium",
    "med": "Medium",
    "low": "Low",
    # важливо: Holiday -> Non-economic
    "holiday": "Non-economic",
    "non-economic": "Non-economic",
    "noneconomic": "Non-economic",
    "bankholiday": "Non-economic",
    "bank holiday": "Non-economic",
}

def normalize_impact(raw: str | None) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    k = re.sub(r"[^a-z]+", "", s.lower())
    for key, val in _IMPACT_ALIASES.items():
        if key in k:
            return val
    if s in ("High", "Medium", "Low", "Non-economic"):
        return s
    return s

def normalize_currency(raw: str | None) -> str:
    s = (raw or "").strip().upper()
    s = re.sub(r"[^A-Z]", "", s)
    return s[:4]

# ---- фільтрація ---------------------------------------------------

def filter_events(
    events: Iterable[FFEvent],
    impacts_sel: List[str] | Set[str],
    currencies_sel: List[str] | Set[str],
) -> List[FFEvent]:
    impacts_set: Set[str] = {normalize_impact(i) for i in impacts_sel if i}
    # нормалізуємо Holiday -> Non-economic уже тут
    currencies_set: Set[str] = {normalize_currency(c) for c in currencies_sel if c}

    out: List[FFEvent] = []
    for ev in events:
        # impact: якщо в події порожній — не відсікаємо
        imp = normalize_impact(ev.impact)
        if imp and impacts_set and imp not in impacts_set:
            continue

        # currency: якщо в події порожня — ПРОПУСКАЄМО
        cur = normalize_currency(ev.currency)
        if cur and currencies_set and cur not in currencies_set:
            continue

        out.append(ev)
    return out