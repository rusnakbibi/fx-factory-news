# app/config/settings.py
import os
from datetime import timezone

try:
    from zoneinfo import ZoneInfo
except Exception:
    import pytz  # type: ignore
    class ZoneInfo:
        def __init__(self, name):
            import pytz
            self.tz = pytz.timezone(name)
        def utcoffset(self, dt): return self.tz.utcoffset(dt)
        def dst(self, dt): return self.tz.dst(dt)
        def tzname(self, dt): return self.tz.tzname(dt)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
TZ_NAME = os.getenv("TZ", "Europe/Kyiv")
LOCAL_TZ = ZoneInfo(TZ_NAME)
DEFAULT_ALERT_MINUTES = int(os.getenv("DEFAULT_ALERT_MINUTES", "30"))
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
DB_PATH = os.getenv("DB_PATH", "bot.db")
UTC = timezone.utc

# API endpoints
FF_THISWEEK = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
FF_NEXTWEEK = "https://nfs.faireconomy.media/ff_calendar_nextweek.json"

# UI constants
COMMON_CURRENCIES = ["USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF","CNY"]
IMPACTS = ["High","Medium","Low","Non-economic"]
ALERT_PRESETS = [5, 15, 30, 60]
LANG_MODES = ["en","uk","auto"]

# Scraping configuration
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "").strip()
METALS_WEEK_HTML_PATH = os.getenv("METALS_WEEK_HTML_PATH", "data/metals_week.html")

# User-Agent та базові заголовки для запитів HTML
UA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Куди писати агрегований JSON
AGGREGATE_JSON_PATH = os.getenv("AGGREGATE_JSON_PATH", "aggregated_calendar.json")
