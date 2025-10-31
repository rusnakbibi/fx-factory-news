# Metals Filtering Implementation Guide

## ✅ Implementation Status: **COMPLETE**

This document describes the independent filtering system for the Metals module in your Telegram bot.

---

## 🎯 Overview

The Metals module now has its own **independent filtering system**, completely separate from the Forex module:

| Feature | Forex | Metals |
|---------|-------|--------|
| **Impact Filter** | ✅ High/Medium/Low/Non-economic | ✅ High/Medium/Low/Non-economic |
| **Entity Filter** | Currency codes (USD, EUR, etc.) | **Country codes (US, UK, EZ, etc.)** |
| **Database Columns** | `impact_filter`, `countries_filter` | `metals_impact_filter`, `metals_countries_filter` |
| **Keyboard** | `settings_kb()` | `metals_settings_kb()` |
| **Callback Prefix** | `imp:`, `cur:` | `metals_imp:`, `metals_country:` |
| **Filter Function** | `filter_events()` | `filter_metals_events()` |

---

## 📁 File Changes

### 1. **app/core/models.py**
Added `country` field to `MMEvent`:

```python
@dataclass
class MMEvent:
    dt_utc: datetime
    time_str: str
    title: str
    country: str | None = None  # ← NEW: Country code (US, UK, EZ, etc.)
    impact: str | None = None
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    date_label: str = ""
    source: str = "MetalsMine (offline)"
```

### 2. **app/core/database.py**
Added metals-specific filter columns:

```python
DDL_SUBS = """
CREATE TABLE IF NOT EXISTS subscriptions (
  ...
  metals_impact_filter   TEXT   NOT NULL DEFAULT '',     # ← NEW
  metals_countries_filter TEXT  NOT NULL DEFAULT '',     # ← NEW
  PRIMARY KEY (user_id, chat_id)
);
"""
```

**Helper functions** for existing databases:
- `_ensure_metals_columns_pg()` - PostgreSQL
- `_ensure_metals_columns_sqlite()` - SQLite

### 3. **app/services/metals_parser.py**
Updated parsers to extract country codes:

```python
# In parse_metals_today_html():
country_code, _ = _split_country_prefix(title)

events.append(MMEvent(
    ...
    country=country_code or None,  # ← NEW
    ...
))
```

**Example:** `"UK CPI y/y"` → country = `"UK"`, title stays = `"UK CPI y/y"`

### 4. **app/ui/filters.py**
Created dedicated metals filtering function:

```python
def normalize_country(raw: str | None) -> str:
    """Normalizes country codes: 'uk' → 'UK', 'us' → 'US'"""
    ...

def filter_metals_events(
    events: Iterable[MMEvent],
    impacts: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
) -> List[MMEvent]:
    """
    Filters metals events by:
      - impact (High/Medium/Low/Non-economic)
      - country code (US/UK/EZ/etc.)
    """
    ...
```

### 5. **app/ui/keyboards.py**
Added metals-specific keyboard and constants:

```python
# Constants
METALS_COUNTRIES = ["US", "UK", "EZ", "DE", "FR", "IT", "ES", "CH", "CA", "JP", "CN", "AU"]

COUNTRY_FLAGS = {
    "US": "🇺🇸", "UK": "🇬🇧", "EZ": "🇪🇺", "DE": "🇩🇪", ...
}

# Keyboard function
def metals_settings_kb(
    selected_impacts,
    selected_countries,
    lang_mode: str = "en",
) -> InlineKeyboardMarkup:
    """
    Settings keyboard for Metals module.
    Filters by impact and country (not currency).
    """
    ...
```

**Visual Layout:**
```
┌─────────────────────────────┐
│  ✅ High      ✅ Medium      │
│  ⬜ Low       ⬜ Non-economic │
├─────────────────────────────┤
│  ✅ 🇺🇸 US    ⬜ 🇬🇧 UK   ⬜ 🇪🇺 EZ │
│  ⬜ 🇩🇪 DE    ⬜ 🇫🇷 FR   ⬜ 🇮🇹 IT │
│  ⬜ 🇪🇸 ES    ⬜ 🇨🇭 CH   ⬜ 🇨🇦 CA │
│  ⬜ 🇯🇵 JP    ⬜ 🇨🇳 CN   ⬜ 🇦🇺 AU │
├─────────────────────────────┤
│       🧹 Reset filters       │
│         ◀️ Back              │
└─────────────────────────────┘
```

### 6. **app/handlers/callbacks.py**
Added metals filter callback handlers:

```python
@router.callback_query(F.data.startswith("metals_imp:"))
async def cb_metals_impact(c: CallbackQuery):
    """Toggle metals impact filter"""
    ...

@router.callback_query(F.data.startswith("metals_country:"))
async def cb_metals_country(c: CallbackQuery):
    """Toggle metals country filter"""
    ...

@router.callback_query(F.data == "metals_reset")
async def cb_metals_reset(c: CallbackQuery):
    """Reset all metals filters"""
    ...
```

**Updated existing handler:**
```python
@router.callback_query(F.data == "metals:settings")
async def cb_metals_settings(c: CallbackQuery):
    """Show metals settings with filters"""
    kb = metals_settings_kb(
        csv_to_list(subs.get("metals_impact_filter", "")),
        csv_to_list(subs.get("metals_countries_filter", "")),
        lang_mode=lang,
    )
    ...
```

### 7. **app/handlers/commands.py**
Updated display functions to apply filters:

```python
async def _send_metals_today_offline(m: Message, lang: str) -> None:
    """Sends metals events for today with filters"""
    events = load_today_from_file(html_path)
    
    # Apply metals filters
    from ..ui.filters import filter_metals_events
    subs = _rowdict(get_sub(m.from_user.id, m.chat.id))
    impacts = csv_to_list(subs.get("metals_impact_filter", ""))
    countries = csv_to_list(subs.get("metals_countries_filter", ""))
    filtered = filter_metals_events(events, impacts, countries)
    
    if not filtered:
        await m.answer("No metals events match your filters for today.")
        return
    
    # Display filtered events
    for pack in chunk(filtered, 8):
        ...
```

Same pattern applied to `_send_metals_week_offline()` and `cb_metals_today()`.

---

## 🔄 Data Flow

### User Interaction Flow

```
1. User Opens Metals Settings
   ↓
   /metals → "Settings" button → cb_metals_settings()
   ↓
   Displays metals_settings_kb() with current filters

2. User Toggles Filters
   ↓
   Click "🇺🇸 US" → cb_metals_country("metals_country:US")
   ↓
   Update database: metals_countries_filter = "US"
   ↓
   Refresh keyboard with updated checkmarks

3. User Requests Metals Events
   ↓
   Click "Today" → cb_metals_today()
   ↓
   Load events from HTML file
   ↓
   Apply filter_metals_events(events, impacts, countries)
   ↓
   Display filtered results
```

### Filtering Logic Flow

```python
# Step 1: Load all events
events = parse_metals_today_html(html_content)
# → 50 events total

# Step 2: Get user's filter preferences from database
impacts = ["High", "Medium"]      # User selected
countries = ["US", "UK"]          # User selected

# Step 3: Apply filters
filtered = filter_metals_events(events, impacts, countries)

# Filtering process:
for event in events:
    # Check impact
    if impacts and event.impact not in impacts:
        skip  # Impact doesn't match
    
    # Check country
    if countries and event.country not in countries:
        skip  # Country doesn't match
    
    include  # Event matches all filters

# → 8 events match filters

# Step 4: Display filtered events
for event in filtered:
    send_to_user(event)
```

---

## 🎮 User Experience

### Example Scenario

**User wants to see only high-impact US economic events in metals:**

1. **Open Metals Module:**
   ```
   /start → 🪙 Metals
   ```

2. **Go to Settings:**
   ```
   🪙 Metals → ⚙️ Settings
   ```

3. **Configure Filters:**
   - Click **🔴 High** (impact filter)
   - Click **🇺🇸 US** (country filter)
   - Keyboard updates with checkmarks: ✅

4. **View Events:**
   ```
   ◀️ Back → 📅 Today
   ```

5. **Result:**
   ```
   🪙 Metals — Today
   
   • Mon 14:30 — 🔴 US CPI y/y
   United States
   Actual: 3.2% | Forecast: 3.1% | Previous: 3.0%
   
   • Mon 16:00 — 🔴 US Fed Chair Speech
   United States
   ```

---

## 🔍 Key Differences: Forex vs Metals

### Database Storage

| Module | Columns | Example Values |
|--------|---------|----------------|
| **Forex** | `impact_filter`<br>`countries_filter` | `"High,Medium"`<br>`"USD,EUR,GBP"` |
| **Metals** | `metals_impact_filter`<br>`metals_countries_filter` | `"High"`<br>`"US,UK,EZ"` |

### Callback Data Prefixes

| Module | Impact Filter | Entity Filter | Reset |
|--------|---------------|---------------|-------|
| **Forex** | `imp:High` | `cur:USD` | `reset` |
| **Metals** | `metals_imp:High` | `metals_country:US` | `metals_reset` |

### Filter Functions

| Module | Function | Parameters |
|--------|----------|------------|
| **Forex** | `filter_events()` | `events`, `impacts`, `currencies`, `categories` |
| **Metals** | `filter_metals_events()` | `events`, `impacts`, `countries` |

---

## 🧪 Testing

All components have been tested:

```bash
✅ MMEvent model has country field
✅ Database has metals filter columns  
✅ Parser extracts country codes
✅ filter_metals_events() works correctly
✅ metals_settings_kb() creates proper keyboard
✅ All callback handlers present
✅ All command handlers present
```

**Test Results:**
- ✅ Impact filtering: Works
- ✅ Country filtering: Works
- ✅ Combined filtering: Works
- ✅ Empty filters (show all): Works
- ✅ No matches message: Works

---

## 🔧 Configuration

### Supported Countries

Currently configured countries (can be extended):

```python
METALS_COUNTRIES = [
    "US",   # United States
    "UK",   # United Kingdom
    "EZ",   # Eurozone
    "DE",   # Germany
    "FR",   # France
    "IT",   # Italy
    "ES",   # Spain
    "CH",   # Switzerland
    "CA",   # Canada
    "JP",   # Japan
    "CN",   # China
    "AU",   # Australia
]
```

**To add more countries:**
1. Add to `METALS_COUNTRIES` in `app/ui/keyboards.py`
2. Add flag emoji to `COUNTRY_FLAGS`
3. Add full name to `_COUNTRY_NAMES` in `app/services/metals_parser.py`

### Supported Impacts

Same as Forex:
- 🔴 High
- 🟠 Medium
- 🟡 Low
- ⚪️ Non-economic

---

## 📊 Database Migration

For existing databases, the columns are added automatically on startup:

**PostgreSQL:**
```sql
ALTER TABLE subscriptions ADD COLUMN metals_impact_filter TEXT DEFAULT '';
ALTER TABLE subscriptions ADD COLUMN metals_countries_filter TEXT DEFAULT '';
```

**SQLite:**
```sql
ALTER TABLE subscriptions ADD COLUMN metals_impact_filter TEXT DEFAULT '';
ALTER TABLE subscriptions ADD COLUMN metals_countries_filter TEXT DEFAULT '';
```

Migration is handled by:
- `_ensure_metals_columns_pg()` (PostgreSQL)
- `_ensure_metals_columns_sqlite()` (SQLite)

Called automatically in `_init_pg()` and `_init_sqlite()`.

---

## 🚀 Future Enhancements

Possible improvements:

1. **Regional Groups:**
   - Add "All EU", "All Asia", "All Americas" quick filters

2. **Smart Defaults:**
   - Pre-select user's country based on timezone/language

3. **Search:**
   - Add text search by event title

4. **Favorites:**
   - Let users save favorite country combinations

5. **Analytics:**
   - Show most filtered countries for the user

---

## 📝 Summary

### What Was Built

✅ **Independent filtering system for Metals module**
- Separate from Forex filtering
- Filters by impact and country (not currency)
- Own database columns
- Own keyboard layout
- Own callback handlers

### Key Benefits

1. **Modularity:** Forex and Metals are completely independent
2. **User Control:** Fine-grained filtering by country
3. **Clarity:** Clear separation of concerns
4. **Extensibility:** Easy to add more countries
5. **Maintainability:** Clean, testable code

### Architecture

```
app/
├── core/
│   ├── models.py          # MMEvent with country field
│   └── database.py        # metals_* columns
├── services/
│   └── metals_parser.py   # Extract country codes
├── ui/
│   ├── filters.py         # filter_metals_events()
│   └── keyboards.py       # metals_settings_kb()
└── handlers/
    ├── callbacks.py       # metals_imp:, metals_country:
    └── commands.py        # Apply filters in display
```

---

## ✨ Done!

The Metals module now has a complete, independent filtering system that works exactly like Forex but filters by **countries** instead of **currencies**.

**Users can now:**
- ✅ Filter metals events by impact (High/Medium/Low)
- ✅ Filter metals events by country (US/UK/EZ/etc.)
- ✅ See only events that match their filters
- ✅ Reset filters anytime
- ✅ Have different filter settings for Forex and Metals

**Developers can:**
- ✅ Add new countries easily
- ✅ Maintain Forex and Metals independently
- ✅ Extend filtering logic without affecting Forex
- ✅ Test each module separately

