from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import IMPACTS, COMMON_CURRENCIES, ALERT_PRESETS, LANG_MODES

def settings_kb(selected_impacts, selected_currencies, alert_minutes, lang_mode):
    # impacts row
    imp_buttons = [InlineKeyboardButton(text=("✅ " if i in selected_impacts else "☐ ") + i, callback_data=f"imp:{i}") for i in IMPACTS]
    # currencies grid (2 rows)
    cur_buttons = [InlineKeyboardButton(text=("✅ " if c in selected_currencies else "☐ ") + c, callback_data=f"cur:{c}") for c in COMMON_CURRENCIES]
    rows = []
    rows.append(imp_buttons)
    rows.append(cur_buttons[:5])
    rows.append(cur_buttons[5:])
    # alert presets
    al_buttons = [InlineKeyboardButton(text=("● " if alert_minutes==p else "○ ") + str(p)+"m", callback_data=f"al:{p}") for p in ALERT_PRESETS]
    rows.append(al_buttons)
    # language
    lang_buttons = [InlineKeyboardButton(text=("● " if lang_mode==l else "○ ") + l, callback_data=f"lang:{l}") for l in LANG_MODES]
    rows.append(lang_buttons)
    # save/help
    rows.append([
        InlineKeyboardButton(text="⏱ /subscribe", callback_data="noop"),
        InlineKeyboardButton(text="🧹 reset filters", callback_data="reset"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
