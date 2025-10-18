# app/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import IMPACTS, COMMON_CURRENCIES, ALERT_PRESETS, LANG_MODES

# ---------- MAIN MENU ----------
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings"),
             InlineKeyboardButton(text="⏱ Daily Digest", callback_data="menu:subscribe")],
            [InlineKeyboardButton(text="⏰ Alerts", callback_data="menu:alerts"),
             InlineKeyboardButton(text="🔕 Stop", callback_data="menu:stop")],
            [InlineKeyboardButton(text="📅 Today", callback_data="menu:today"),
            InlineKeyboardButton(text="This week", callback_data="menu:week")],
        ]
    )

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Back", callback_data="menu:home")]]
    )

# ---------- SETTINGS PANEL (toggle filters) ----------
def settings_kb(selected_impacts, selected_currencies, alert_minutes, lang_mode):
    imp_buttons = [
        InlineKeyboardButton(
            text=("✅ " if i in selected_impacts else "☐ ") + i,
            callback_data=f"imp:{i}"
        ) for i in IMPACTS
    ]
    cur_buttons = [
        InlineKeyboardButton(
            text=("✅ " if c in selected_currencies else "☐ ") + c,
            callback_data=f"cur:{c}"
        ) for c in COMMON_CURRENCIES
    ]

    rows = []
    rows.append(imp_buttons)
    rows.append(cur_buttons[:5])
    rows.append(cur_buttons[5:])

    al_buttons = [
        InlineKeyboardButton(
            text=("● " if alert_minutes == p else "○ ") + f"{p}m",
            callback_data=f"al:{p}"
        ) for p in ALERT_PRESETS
    ]
    rows.append(al_buttons)

    lang_buttons = [
        InlineKeyboardButton(
            text=("● " if lang_mode == l else "○ ") + l,
            callback_data=f"lang:{l}"
        ) for l in LANG_MODES
    ]
    rows.append(lang_buttons)

    rows.append([InlineKeyboardButton(text="⏱ /subscribe", callback_data="sub:ask"),
                 InlineKeyboardButton(text="🧹 reset filters", callback_data="reset")])

    rows.append([InlineKeyboardButton(text="◀️ Back", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- SUBSCRIBE TIME PRESETS ----------
def subscribe_time_kb(presets: list[str]) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for p in presets:
        row.append(InlineKeyboardButton(text=p, callback_data=f"sub:set:{p}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Back", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- ALERTS PRESETS ----------
def alerts_presets_kb(current_minutes: int | None = None) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(
            text=("● " if current_minutes == p else "○ ") + f"{p}m",
            callback_data=f"al:{p}"
        ) for p in ALERT_PRESETS
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row, [InlineKeyboardButton(text="◀️ Back", callback_data="menu:home")]])