# app/filters.py
from __future__ import annotations
from typing import Iterable, List, Set
import logging, re

from .models import FFEvent

log = logging.getLogger(__name__)

# ---------------- Impact normalization ----------------

_IMPACT_ALIASES = {
    "high": "High",
    "medium": "Medium",
    "med": "Medium",
    "low": "Low",
    # важливо: Holiday -> Non-economic
    "holiday": "Non-economic",
    "noneconomic": "Non-economic",
    "non-economic": "Non-economic",
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
    return s[:4]  # USD, EUR, JPY ...

# ---------------- Categories ----------------
# Прості евристики: ключові слова у назві або код валюти → категорія

FX_CODES = {
    "USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF","CNY"
}
CRYPTO_KW = {
    "crypto","cryptocurrency","bitcoin","btc","ethereum","eth","defi","stablecoin","blockchain"
}
METALS_KW = {
    "gold","xau","silver","xag","platinum","palladium","copper","metal","metals"
}

def normalize_category(raw: str | None) -> str:
    s = (raw or "").strip().lower()
    if s in ("forex","fx"): return "forex"
    if s in ("crypto","cryptocurrency"): return "crypto"
    if s in ("metals","metal"): return "metals"
    return ""

def categorize_event(ev: FFEvent) -> str:
    title = (ev.title or "").lower()
    cur = (ev.currency or "").upper()

    if any(k in title for k in CRYPTO_KW):
        return "crypto"
    if any(k in title for k in METALS_KW):
        return "metals"
    if cur in FX_CODES:
        return "forex"
    return "forex"  # дефолт, щоб не «губити» події

# ---------------- Filtering ----------------

def filter_events(
    events: Iterable[FFEvent],
    impacts: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
) -> List[FFEvent]:
    """
    Фільтрує за:
      - impact (High/Medium/Low/Non-economic)
      - currency (USD/EUR/...)
      - category (forex/crypto/metals) — евристика з назви/валюти
    Порожні множини = не фільтруємо за цим критерієм.
    """
    imp_set: Set[str] = {normalize_impact(i) for i in (impacts or []) if normalize_impact(i)}
    cur_set: Set[str] = {normalize_currency(c) for c in (countries or []) if normalize_currency(c)}
    cat_set: Set[str] = {normalize_category(x) for x in (categories or []) if normalize_category(x)}

    out: List[FFEvent] = []
    for ev in events:
        # ---------- валютний whitelist ----------
        if cur_set:
            # пробуємо взяти currency; якщо її немає — спробувати country
            cur = normalize_currency(getattr(ev, "currency", "")) or normalize_currency(getattr(ev, "country", ""))
            # якщо валюту не визначено або вона не у вибраному списку — відсіюємо
            if not cur or cur not in cur_set:
                continue

        # ---------- impact ----------
        imp = normalize_impact(getattr(ev, "impact", ""))
        if imp_set and imp and imp not in imp_set:
            continue

        # ---------- категорія (залишаємо як було) ----------
        cat = categorize_event(ev)
        if cat_set and cat not in cat_set:
            continue

        out.append(ev)
    return out