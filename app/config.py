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

BOT_TOKEN = os.getenv("BOT_TOKEN")
TZ_NAME = os.getenv("TZ", "Europe/Kyiv")
LOCAL_TZ = ZoneInfo(TZ_NAME)
DEFAULT_ALERT_MINUTES = int(os.getenv("DEFAULT_ALERT_MINUTES", "30"))
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

FF_THISWEEK = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
FF_NEXTWEEK = "https://nfs.faireconomy.media/ff_calendar_nextweek.json"
UTC = timezone.utc

# UI constants
COMMON_CURRENCIES = ["USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF","CNY"]
IMPACTS = ["High","Medium","Low","Holiday"]
ALERT_PRESETS = [5, 15, 30, 60]
LANG_MODES = ["en","uk","auto"]  # 'auto' = detect from system TZ (example) or default to en
