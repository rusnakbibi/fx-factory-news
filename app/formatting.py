import hashlib
from .models import FFEvent

IMPACT_EMOJI = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Holiday": "🟦",
}

def event_hash(ev: FFEvent) -> str:
    base = f"{ev.date.isoformat()}|{ev.title}|{ev.country}|{ev.currency}|{ev.impact}"
    return hashlib.sha1(base.encode()).hexdigest()

# app/formatting.py

from .filters import normalize_impact

IMPACT_ICON = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Non-economic": "⚪️",
}

def event_to_text(ev, tz) -> str:
    """
    Красивий компактний формат для Telegram.
    1) Час (локальний) + іконка рівня + жирна назва події
    2) Валюта «бейджем» (моноширинний <code>USD</code>), додатково країна (якщо відрізняється)
    3) Показники: Actual | Forecast | Previous (лише ті, що є)
    """
    # локальний час
    lt = ev.date.astimezone(tz)

    # іконка імпакту
    impact_norm = normalize_impact(getattr(ev, "impact", "") or "")
    icon = IMPACT_ICON.get(impact_norm, "🔘")

    # рядок 1: час + назва
    head = f"🕒 <b>{lt:%a %d %b %H:%M}</b> — {icon} <b>{ev.title}</b>"

    # рядок 2: валюта / країна
    cur = (getattr(ev, "currency", "") or "").strip().upper()
    country = (getattr(ev, "country", "") or "").strip().upper()
    who = []
    if cur:
        # моноширинний «бейдж» — в Телеграмі читається значно краще
        who.append(f"<b><code>{cur}</code></b>")
    if country and country != cur:
        who.append(country)
    meta = " ".join(who) if who else ""

    # рядок 3: метрики (лише наявні), спочатку Actual
    stats = []
    actual = getattr(ev, "actual", None)
    forecast = getattr(ev, "forecast", None)
    previous = getattr(ev, "previous", None)
    if actual:
        stats.append(f"Actual: <b>{actual}</b>")
    if forecast:
        stats.append(f"Forecast: <b>{forecast}</b>")
    if previous:
        stats.append(f"Previous: <b>{previous}</b>")
    stats_line = " | ".join(stats)

    # складання повідомлення
    lines = [head]
    if meta:
        lines.append(meta)
    if stats_line:
        lines.append(stats_line)

    return "\n".join(lines)