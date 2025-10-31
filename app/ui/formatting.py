# app/ui/formatting.py
import hashlib
import html
from ..core.models import FFEvent
from ..services.translator import translate_title

IMPACT_EMOJI = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Holiday": "🟦",
}

def event_hash(ev: FFEvent) -> str:
    base = f"{ev.date.isoformat()}|{ev.title}|{ev.country}|{ev.currency}|{ev.impact}"
    return hashlib.sha1(base.encode()).hexdigest()

from ..ui.filters import normalize_impact

IMPACT_ICON = {
    "High": "🔴",
    "Medium": "🟠",
    "Low": "🟡",
    "Non-economic": "⚪️",
}

def event_to_text(ev, tz, lang: str = "en") -> str:
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

    # переклад назви події
    translated_title = translate_title(ev.title, lang)
    # екрануємо HTML спецсимволи
    translated_title = html.escape(translated_title)

    # рядок 1: час + назва
    head = f"🕒 <b>{lt:%a %d %b %H:%M}</b> — {icon} <b>{translated_title}</b>"

    # рядок 2: валюта / країна
    cur = (getattr(ev, "currency", "") or "").strip().upper()
    country = (getattr(ev, "country", "") or "").strip().upper()
    who = []
    if cur:
        # моноширинний «бейдж» — в Телеграмі читається значно краще
        who.append(f"<b><code>{html.escape(cur)}</code></b>")
    if country and country != cur:
        who.append(html.escape(country))
    meta = " ".join(who) if who else ""

    # рядок 3: метрики (лише наявні), спочатку Actual
    stats = []
    actual = getattr(ev, "actual", None)
    forecast = getattr(ev, "forecast", None)
    previous = getattr(ev, "previous", None)
    if actual:
        stats.append(f"Actual: <b>{html.escape(str(actual))}</b>")
    if forecast:
        stats.append(f"Forecast: <b>{html.escape(str(forecast))}</b>")
    if previous:
        stats.append(f"Previous: <b>{html.escape(str(previous))}</b>")
    stats_line = " | ".join(stats)

    # складання повідомлення
    lines = [head]
    if meta:
        lines.append(meta)
    if stats_line:
        lines.append(stats_line)

    return "\n".join(lines)
