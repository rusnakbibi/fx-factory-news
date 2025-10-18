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

def event_to_text(ev: FFEvent, tz) -> str:
    local_dt = ev.date.astimezone(tz)
    emoji = IMPACT_EMOJI.get(ev.impact, "⚪️")
    lines = [
        f"{emoji} <b>{local_dt:%a, %d %b %H:%M}</b>",
        f"{ev.currency} / {ev.country}",
        f"<b>{ev.title}</b>",
    ]
    stats = []
    if ev.forecast: stats.append(f"Forecast: <b>{ev.forecast}</b>")
    if ev.previous: stats.append(f"Prev: <b>{ev.previous}</b>")
    if ev.actual:   stats.append(f"Actual: <b>{ev.actual}</b>")
    if stats:
        lines.append(" · ".join(stats))
    if ev.url:
        lines.append(f"<a href='{ev.url}'>details</a>")
    return "\n".join(lines)
