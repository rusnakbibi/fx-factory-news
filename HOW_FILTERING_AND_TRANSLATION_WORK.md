# How Filtering and Translation Work

This document explains the filtering and translation mechanisms in your Forex Factory Telegram bot.

---

## 🎯 Filtering System

### Overview

The bot filters economic events based on:

1. **Impact Level** (High/Medium/Low/Non-economic)
2. **Currency** (USD, EUR, GBP, JPY, etc.)
3. **Category** (Forex, Crypto, Metals) - _experimental_

### Architecture

```
User Settings (Database)
    ↓
Handler extracts filters
    ↓
filter_events() applies filters
    ↓
Filtered events sent to user
```

---

## 📁 File Structure

### `app/ui/filters.py`

Contains all filtering logic:

- **`normalize_impact()`** - Normalizes impact strings
- **`normalize_currency()`** - Normalizes currency codes
- **`categorize_event()`** - Auto-detects event category
- **`filter_events()`** - Main filtering function

### `app/handlers/callbacks.py` & `app/handlers/commands.py`

- Handle user interactions
- Load user preferences from database
- Apply filters when displaying events

### `app/core/database.py`

- Stores user filter preferences in `subscriptions` table:
  - `impact_filter` (e.g., "High,Medium")
  - `countries_filter` (e.g., "USD,EUR,GBP")

---

## 🔧 How Impact Filtering Works

### Step 1: User Settings Storage

When a user clicks an impact button (🔴 High, 🟠 Medium, 🟡 Low), the callback handler stores their choice:

```python
@router.callback_query(F.data.startswith("imp:"))
async def cb_impact(c: CallbackQuery):
    # Get current filters
    subs = get_sub(c.from_user.id, c.message.chat.id)
    impacts = set(csv_to_list(subs.get("impact_filter", "")))

    # Toggle the selected impact
    val = c.data.split(":", 1)[1]  # e.g., "High"
    if val in impacts:
        impacts.remove(val)
    else:
        impacts.add(val)

    # Save to database
    set_sub(c.from_user.id, c.message.chat.id,
            impact_filter=",".join(sorted(impacts)))
```

**Database:** `impact_filter` column stores: `"High,Medium"` or `"Low"` etc.

### Step 2: Impact Normalization

When filtering, the system normalizes impact strings to handle variations:

```python
_IMPACT_ALIASES = {
    "high": "High",
    "medium": "Medium",
    "med": "Medium",
    "low": "Low",
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
    return s
```

**Example:**

- Input: `"holiday"` → Output: `"Non-economic"`
- Input: `"HIGH"` → Output: `"High"`
- Input: `"Med"` → Output: `"Medium"`

### Step 3: Filtering Events

The main filtering function compares normalized values:

```python
def filter_events(
    events: Iterable[FFEvent],
    impacts: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
) -> List[FFEvent]:
    # Normalize all filter values
    imp_set: Set[str] = {normalize_impact(i) for i in (impacts or [])}

    out: List[FFEvent] = []
    for ev in events:
        # Check impact
        imp = normalize_impact(ev.impact)
        if imp_set and imp and imp not in imp_set:
            continue  # Skip this event

        # ... other filters ...

        out.append(ev)
    return out
```

### Step 4: Applied in Handlers

When showing events, handlers retrieve user settings and apply filters:

```python
async def _send_today(m: Message, subs: dict):
    # Get user's filter preferences
    impacts = csv_to_list(subs.get("impact_filter", ""))      # ["High", "Medium"]
    countries = csv_to_list(subs.get("countries_filter", "")) # ["USD", "EUR"]

    # Fetch all events
    events = await fetch_calendar()

    # Filter to today's time window
    in_window = [e for e in events if start_utc <= e.date < end_utc]

    # Apply user's filters
    filtered = filter_events(in_window, impacts, countries)

    # Send to user
    for ev in filtered:
        await m.answer(event_to_text(ev, LOCAL_TZ))
```

---

## 💱 How Currency Filtering Works

### Step 1: User Settings Storage

Similar to impact, but for currencies:

```python
@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(c: CallbackQuery):
    subs = get_sub(c.from_user.id, c.message.chat.id)
    curr = set(csv_to_list(subs.get("countries_filter", "")))

    # Toggle currency
    val = c.data.split(":", 1)[1]  # e.g., "USD"
    if val in curr:
        curr.remove(val)
    else:
        curr.add(val)

    # Save to database
    set_sub(c.from_user.id, c.message.chat.id,
            countries_filter=",".join(sorted(curr)))
```

**Database:** `countries_filter` column stores: `"USD,EUR,GBP"`

### Step 2: Currency Normalization

Ensures consistent format:

```python
def normalize_currency(raw: str | None) -> str:
    s = (raw or "").strip().upper()
    s = re.sub(r"[^A-Z]", "", s)  # Remove non-letters
    return s[:4]  # Max 4 chars: USD, EUR, JPY
```

**Example:**

- Input: `"usd"` → Output: `"USD"`
- Input: `"eur.."` → Output: `"EUR"`

### Step 3: Filtering Logic

The filter checks both `currency` and `country` fields:

```python
# In filter_events():
if cur_set:
    # Try currency field first, fallback to country
    cur = normalize_currency(ev.currency) or normalize_currency(ev.country)

    # Skip if not in user's selected currencies
    if not cur or cur not in cur_set:
        continue
```

**Why check both fields?**

- ForexFactory uses `currency` field (e.g., "USD")
- Some events might use `country` field (e.g., "US")

---

## 🔄 Category Filtering (Experimental)

Auto-detects event type based on keywords:

```python
FX_CODES = {"USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF","CNY"}
CRYPTO_KW = {"crypto","cryptocurrency","bitcoin","btc","ethereum",...}
METALS_KW = {"gold","xau","silver","xag","platinum","palladium",...}

def categorize_event(ev: FFEvent) -> str:
    title = (ev.title or "").lower()
    cur = (ev.currency or "").upper()

    # Check title keywords
    if any(k in title for k in CRYPTO_KW):
        return "crypto"
    if any(k in title for k in METALS_KW):
        return "metals"

    # Check currency code
    if cur in FX_CODES:
        return "forex"

    return "forex"  # Default
```

**Example:**

- Event: "Bitcoin Price Index" → `"crypto"`
- Event: "Gold Futures" → `"metals"`
- Event: "USD CPI y/y" → `"forex"`

---

## 🌐 Translation System

### Overview

The bot translates economic event titles from English to Ukrainian using a local dictionary.

### Architecture

```
Event Title (English)
    ↓
translate_title(text, "ua")
    ↓
Dictionary Lookup (UA_DICT)
    ↓
Translated Title (Ukrainian)
```

---

## 📁 Translation Files

### `app/services/translator.py`

Contains:

- **`UA_DICT`** - English → Ukrainian dictionary
- **`translate_title()`** - Translation function

---

## 🔧 How Translation Works

### Step 1: Dictionary Definition

A comprehensive dictionary maps English economic terms to Ukrainian:

```python
UA_DICT = {
    # Price indices
    "CPI y/y": "Індекс споживчих цін (р/р)",
    "CPI m/m": "Індекс споживчих цін (м/м)",
    "Core CPI": "Базовий ІСЦ",

    # GDP
    "GDP q/q": "Валовий внутрішній продукт (к/к)",
    "GDP y/y": "Валовий внутрішній продукт (р/р)",

    # PMI
    "Manufacturing PMI": "Індекс виробничої активності (PMI)",
    "Services PMI": "Індекс ділової активності у сфері послуг (PMI)",

    # Labor market
    "Unemployment Rate": "Рівень безробіття",
    "Employment Change": "Зміна кількості зайнятих",

    # ... 80+ more terms ...
}
```

### Step 2: Translation Function

Simple substring matching:

```python
def translate_title(text: str, target_lang: str) -> str:
    """
    Translates economic event titles.
    Supports 'en' (no translation) and 'ua' (dictionary lookup).
    """
    if not text or target_lang == "en":
        return text  # No translation needed

    if target_lang == "ua":
        lowered = text.lower()
        for key, value in UA_DICT.items():
            if key.lower() in lowered:
                return value  # Return translation
        return text  # Fallback if not found

    return text  # Unknown language
```

**How it works:**

1. Convert input to lowercase
2. Check if any dictionary key appears in the text
3. Return the first matching translation
4. If no match, return original text

**Example:**

```python
translate_title("US CPI y/y", "ua")
# → "Індекс споживчих цін (р/р)"

translate_title("Flash Manufacturing PMI", "ua")
# → "Попередній виробничий PMI"

translate_title("Some Unknown Event", "ua")
# → "Some Unknown Event" (no translation)
```

### Step 3: Applied in Event Formatting

The `event_to_text()` function uses translation:

```python
def event_to_text(ev: FFEvent, tz) -> str:
    # Get user's language preference
    lang = get_user_lang()

    # Translate title if Ukrainian
    title = translate_title(ev.title, lang)

    # Format the event
    return f"{impact_emoji} {time} {currency} — {title}"
```

---

## 🔗 How They Work Together

### Complete Flow Example

1. **User sets preferences:**

   - Impact: 🔴 High, 🟠 Medium
   - Currency: USD, EUR
   - Language: 🇺🇦 Ukrainian

2. **User requests /today:**

3. **Handler loads preferences:**

   ```python
   subs = get_sub(user_id, chat_id)
   impacts = ["High", "Medium"]
   countries = ["USD", "EUR"]
   lang = "ua"
   ```

4. **Fetch all events:**

   ```python
   events = await fetch_calendar()
   # Returns 100+ events from ForexFactory
   ```

5. **Apply time window:**

   ```python
   in_window = [e for e in events if start_utc <= e.date < end_utc]
   # Reduces to 20 events today
   ```

6. **Apply filters:**

   ```python
   filtered = filter_events(in_window, ["High", "Medium"], ["USD", "EUR"])
   # Reduces to 5 events matching criteria
   ```

7. **Format and translate:**
   ```python
   for ev in filtered:
       title_ua = translate_title(ev.title, "ua")
       # "CPI y/y" → "Індекс споживчих цін (р/р)"

       text = event_to_text(ev, LOCAL_TZ)
       # "🔴 14:30 USD — Індекс споживчих цін (р/р)"

       await m.answer(text)
   ```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interaction                     │
├─────────────────────────────────────────────────────────┤
│  User clicks: 🔴 High, 💵 USD, 🇺🇦 Ukrainian            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Database Storage                       │
├─────────────────────────────────────────────────────────┤
│  impact_filter = "High,Medium"                          │
│  countries_filter = "USD,EUR"                           │
│  lang_mode = "ua"                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ForexFactory API Fetch                     │
├─────────────────────────────────────────────────────────┤
│  fetch_calendar() → 100+ raw events                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Time Window Filter                     │
├─────────────────────────────────────────────────────────┤
│  Filter to today: start_utc <= date < end_utc          │
│  100+ events → 20 events                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Impact & Currency Filter                   │
├─────────────────────────────────────────────────────────┤
│  filter_events(events, ["High","Medium"], ["USD","EUR"])│
│  • normalize_impact("HIGH") → "High" ✓                  │
│  • normalize_impact("Low") → skip ✗                     │
│  • normalize_currency("usd") → "USD" ✓                  │
│  • normalize_currency("JPY") → skip ✗                   │
│  20 events → 5 events                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Translation                           │
├─────────────────────────────────────────────────────────┤
│  For each event:                                        │
│  • translate_title("CPI y/y", "ua")                     │
│    → "Індекс споживчих цін (р/р)"                       │
│  • translate_title("GDP q/q", "ua")                     │
│    → "Валовий внутрішній продукт (к/к)"                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Format & Display                       │
├─────────────────────────────────────────────────────────┤
│  🔴 14:30 USD — Індекс споживчих цін (р/р)              │
│  🟠 15:00 EUR — Валовий внутрішній продукт (к/к)        │
│  🔴 16:45 USD — Індекс виробничої активності (PMI)      │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Key Design Decisions

### 1. **Normalization Before Comparison**

- Handles case sensitivity: `"USD"` vs `"usd"`
- Handles variations: `"Med"` vs `"Medium"`
- Handles holidays: `"Bank Holiday"` → `"Non-economic"`

### 2. **Toggle-Based UI**

- Users click buttons to add/remove filters
- Visual feedback with checkmarks
- Persisted to database immediately

### 3. **Substring Translation**

- Simple and fast
- Works with partial matches
- "US CPI y/y" matches "CPI y/y" key
- No need for exact string matching

### 4. **Empty Filter = Show All**

- If no impacts selected → show all impacts
- If no currencies selected → show all currencies
- User-friendly default behavior

### 5. **Fallback Behavior**

- Unknown impact → keep original
- Unknown currency → keep original
- No translation found → keep English
- Prevents data loss

---

## 📝 Summary

### Filtering

1. User selects filters via inline keyboard
2. Filters stored in database (CSV format)
3. When fetching events, filters are applied via `filter_events()`
4. Normalization ensures consistent comparison
5. Empty filters mean "show all"

### Translation

1. Dictionary-based approach (English → Ukrainian)
2. Substring matching for flexibility
3. Applied during event formatting
4. Graceful fallback to original text

### Benefits

- ✅ User-controlled filtering
- ✅ Persistent preferences
- ✅ Multilingual support
- ✅ Efficient and fast
- ✅ Easy to extend (add more languages/terms)

---

## 🔮 Future Enhancements

### Filtering

- [ ] Add date range filters
- [ ] Add multiple category selection
- [ ] Add search by event name
- [ ] Add "favorites" feature

### Translation

- [ ] Add more languages (Russian, Spanish, etc.)
- [ ] Use external translation API for unknown terms
- [ ] Add user-contributed translations
- [ ] Cache translations for performance
