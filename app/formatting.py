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

def event_to_text(ev, local_tz) -> str:
    lt = ev.date.astimezone(local_tz)
    # іконка імпакту
    impact_icon = {
        "High": "🔴",
        "Medium": "🟠",
        "Low": "🟡",
        "Non-economic": "⚪️",
    }.get((getattr(ev, "impact", "") or "").title(), "🟡")

    # заголовок
    header = f"⏰ {lt:%a %d %b %H:%M} — {impact_icon} {ev.title}"

    # підзаголовок (валюта / країна — якщо є)
    cur = getattr(ev, "currency", "") or ""
    country = getattr(ev, "country", "") or ""
    sub = " / ".join([x for x in (cur, country) if x]).strip()
    if sub:
        header += f"\n<b>{sub}</b>"

    # цифри — якщо є
    stats = []
    prev = getattr(ev, "previous", "") or ""
    fc = getattr(ev, "forecast", "") or ""
    act = getattr(ev, "actual", "") or ""
    if prev:    stats.append(f"Previous: <b>{prev}</b>")
    if fc:      stats.append(f"Forecast: <b>{fc}</b>")
    if act:     stats.append(f"Actual: <b>{act}</b>")
    if stats:
        header += "\n" + " | ".join(stats)

    return header