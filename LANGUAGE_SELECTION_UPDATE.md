# Language Selection Added to Metals Settings

## ✅ Update Complete

Language selection has been successfully added to the Metals settings, matching the Forex module functionality.

---

## 🎯 What Was Requested

> "Also, I need to add an option to select a language, like in the forex settings"

---

## ✅ What Was Delivered

### 1. **Updated Keyboard** (`app/ui/keyboards.py`)

Added language selection row to `metals_settings_kb()`:

```python
# Language row
lang_buttons = [
    InlineKeyboardButton(
        text=_radio(lang == "en") + _t(lang, "lang_en"),
        callback_data="metals_lang:en"
    ),
    InlineKeyboardButton(
        text=_radio(lang == "ua") + _t(lang, "lang_ua"),
        callback_data="metals_lang:ua"
    ),
]
rows.append(lang_buttons)
```

### 2. **New Callback Handler** (`app/handlers/callbacks.py`)

Created `cb_metals_lang()` handler:

```python
@router.callback_query(F.data.startswith("metals_lang:"))
async def cb_metals_lang(c: CallbackQuery):
    """Handle language selection in metals settings"""
    val = c.data.split(":", 1)[1]
    if val != "trash":
        set_sub(c.from_user.id, c.message.chat.id, lang_mode=val)

    # Refresh keyboard with new language
    subs = _rowdict(get_sub(c.from_user.id, c.message.chat.id))
    lang = _lang(subs)
    kb = metals_settings_kb(
        csv_to_list(subs.get("metals_impact_filter", "")),
        csv_to_list(subs.get("metals_countries_filter", "")),
        lang_mode=lang,
    )
    await c.message.edit_text(
        _t_en_ua(lang, "⚙️ Metals Settings:", "⚙️ Налаштування Металів:"),
        reply_markup=kb
    )
    await c.answer(_t_en_ua(lang, "Language updated", "Мову оновлено"))
```

---

## 📊 Visual Layout

### Before:

```
┌─────────────────────────────────┐
│   ⚙️ Metals Settings            │
├─────────────────────────────────┤
│  ✅ 🔴 High    ✅ 🟠 Medium     │
│  ⬜ 🟡 Low     ⬜ ⚪️ Non-eco    │
├─────────────────────────────────┤
│  ✅ 🇺🇸 US   ⬜ 🇬🇧 UK   ⬜ 🇪🇺 EZ │
│  ⬜ 🇩🇪 DE   ⬜ 🇫🇷 FR   ⬜ 🇮🇹 IT │
│  ⬜ 🇪🇸 ES   ⬜ 🇨🇭 CH   ⬜ 🇨🇦 CA │
│  ⬜ 🇯🇵 JP   ⬜ 🇨🇳 CN   ⬜ 🇦🇺 AU │
├─────────────────────────────────┤
│       🧹 Reset filters          │
│         ◀️ Back                 │
└─────────────────────────────────┘
```

### After (NEW):

```
┌─────────────────────────────────┐
│   ⚙️ Metals Settings            │
├─────────────────────────────────┤
│  ✅ 🔴 High    ✅ 🟠 Medium     │
│  ⬜ 🟡 Low     ⬜ ⚪️ Non-eco    │
├─────────────────────────────────┤
│  ✅ 🇺🇸 US   ⬜ 🇬🇧 UK   ⬜ 🇪🇺 EZ │
│  ⬜ 🇩🇪 DE   ⬜ 🇫🇷 FR   ⬜ 🇮🇹 IT │
│  ⬜ 🇪🇸 ES   ⬜ 🇨🇭 CH   ⬜ 🇨🇦 CA │
│  ⬜ 🇯🇵 JP   ⬜ 🇨🇳 CN   ⬜ 🇦🇺 AU │
├─────────────────────────────────┤
│   ● en          ○ ua          │  ← NEW!
├─────────────────────────────────┤
│       🧹 Reset filters          │
│         ◀️ Back                 │
└─────────────────────────────────┘
```

---

## 🔄 How It Works

### User Flow:

1. **User opens Metals Settings:**

   ```
   🪙 Metals → ⚙️ Settings
   ```

2. **User sees current language (● = selected):**

   ```
   ● en    ○ ua
   ```

3. **User clicks on Ukrainian:**

   ```
   metals_lang:ua → cb_metals_lang()
   ```

4. **Handler updates database:**

   ```python
   set_sub(user_id, chat_id, lang_mode="ua")
   ```

5. **Keyboard refreshes with Ukrainian labels:**

   ```
   ○ en    ● ua
   ```

6. **All labels now in Ukrainian:**

   ```
   ⚙️ Налаштування Металів:

   ✅ Високий    ✅ Середній
   ⬜ Низький    ⬜ Нейтр.
   ...
   🧹 скинути фільтри
   ◀️ Назад
   ```

---

## 🔗 Integration with Forex

### Shared Language Setting

The language setting is **shared between Forex and Metals**:

- Both use the same `lang_mode` column in the database
- Changing language in Forex affects Metals (and vice versa)
- This is intentional - users expect consistent language across the bot

**Example:**

```
User sets language to Ukrainian in Forex →
Metals also displays in Ukrainian ✓
```

### Independent Callbacks

While the setting is shared, the callbacks are independent:

| Module     | Callback Prefix                    | Handler            |
| ---------- | ---------------------------------- | ------------------ |
| **Forex**  | `lang:en`, `lang:ua`               | `cb_lang()`        |
| **Metals** | `metals_lang:en`, `metals_lang:ua` | `cb_metals_lang()` |

This separation ensures:

- ✅ Each module can refresh its own keyboard
- ✅ Clean separation of concerns
- ✅ Easy to maintain independently

---

## 📝 Files Modified

1. ✅ `app/ui/keyboards.py` - Added language row to `metals_settings_kb()`
2. ✅ `app/handlers/callbacks.py` - Added `cb_metals_lang()` handler

---

## 🧪 Test Results

```
✅ ALL TESTS PASSED!

1️⃣ Keyboard created for both languages
2️⃣ Language buttons present in keyboard
3️⃣ Callback handler cb_metals_lang present
```

---

## 🎉 Summary

### What Changed:

- ✅ Added language selection row to Metals settings keyboard
- ✅ Created `cb_metals_lang()` callback handler
- ✅ Language updates refresh the entire keyboard with new labels

### User Benefits:

- ✅ Can switch language directly from Metals settings
- ✅ Same experience as Forex module
- ✅ Immediate visual feedback

### Technical Details:

- ✅ Uses `metals_lang:` prefix to avoid conflicts with Forex
- ✅ Updates shared `lang_mode` database field
- ✅ Refreshes keyboard with localized labels

---

## 🚀 Ready to Use!

The Metals settings now have complete language selection, matching the Forex module functionality!

**Metals Settings Features:**

1. ✅ Impact filtering (High/Medium/Low/Non-economic)
2. ✅ Country filtering (12 countries with flags)
3. ✅ Language selection (English/Ukrainian) ← **NEW!**
4. ✅ Reset filters option
5. ✅ All labels localized

**User Experience:**

- Click language button → See instant update
- All buttons, labels, and messages change language
- Consistent across Forex and Metals modules
