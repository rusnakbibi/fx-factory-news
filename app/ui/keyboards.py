# app/ui/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---- base dictionaries ----
IMPACTS = ["High", "Medium", "Low", "Non-economic"]
COMMON_CURRENCIES = ["USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD","CNY"]
ALERT_PRESETS = [5, 10, 15, 30, 60, 120]
LANG_MODES = ["en", "ua"]

# ---- Metals-specific constants ----
METALS_COUNTRIES = ["US", "UK", "EZ", "DE", "FR", "IT", "ES", "CH", "CA", "JP", "CN", "AU"]

# flags for currencies (emoji)
CURR_FLAGS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "JPY": "🇯🇵", "CHF": "🇨🇭",
    "CAD": "🇨🇦", "AUD": "🇦🇺", "NZD": "🇳🇿", "CNY": "🇨🇳",
}

# flags for countries (emoji)
COUNTRY_FLAGS = {
    "US": "🇺🇸", "UK": "🇬🇧", "EZ": "🇪🇺", "DE": "🇩🇪", "FR": "🇫🇷", 
    "IT": "🇮🇹", "ES": "🇪🇸", "CH": "🇨🇭", "CA": "🇨🇦", "JP": "🇯🇵", 
    "CN": "🇨🇳", "AU": "🇦🇺",
}

# localized labels
L = {
    "en": {
        "menu_title": "Main menu:",
        "back_to_menu": "Back to menu:",
        "settings": "Settings",
        "digest": "Daily Digest",
        "alerts": "Alerts",
        "stop": "Stop",
        "today": "Today",
        "week": "This week",
        "back": "Back",
        "reset_filters": "reset filters",
        "subscribe": "/subscribe",
        "settings_title": "⚙️ Settings:",
        "imp_high": "High",
        "imp_med": "Medium",
        "imp_low": "Low",
        "imp_noneco": "Non-eco",
        "lang_en": "en",
        "lang_ua": "ua",
        "topics": "Topics:",
        "back_topics": "◀️ Back",
        "choose_time": "Choose time",
    },
    "ua": {
        "menu_title": "Головне меню:",
        "back_to_menu": "Назад до меню:",
        "settings": "Налаштування",
        "digest": "Щоденний дайджест",
        "alerts": "Нагадування",
        "stop": "Стоп",
        "today": "Сьогодні",
        "week": "Цього тижня",
        "back": "Назад",
        "reset_filters": "скинути фільтри",
        "subscribe": "/subscribe",
        "settings_title": "⚙️ Налаштування:",
        "imp_high": "Високий",
        "imp_med": "Середній",
        "imp_low": "Низький",
        "imp_noneco": "Нейтр.",
        "lang_en": "en",
        "lang_ua": "ua",
        "topics": "Теми:",
        "back_topics": "◀️ Назад",
        "choose_time": "Оберіть час",
    },
}

TOPIC_ORDER = ["prices","gdp","pmi","labor","rates","trade","cbanks","misc"]

TOPIC_LABELS = {
    "en": {
        "prices": "Price Indexes (CPI/PPI)",
        "gdp":    "GDP",
        "pmi":    "PMI",
        "labor":  "Labor Market",
        "rates":  "Rates / Inflation",
        "trade":  "Trade / Production",
        "cbanks": "Central Banks",
        "misc":   "Other Indicators",
        "use_as_filter": "🎯 Use as filter",
        "clear": "Clear",
    },
    "ua": {
        "prices": "Індекси цін (CPI/PPI)",
        "gdp":    "ВВП (GDP)",
        "pmi":    "PMI",
        "labor":  "Ринок праці",
        "rates":  "Ставки/Інфляція",
        "trade":  "Торгівля/Виробн.",
        "cbanks": "Центробанки",
        "misc":   "Інші показники",
        "use_as_filter": "🎯 Використовувати як фільтр",
        "clear": "Очистити",
    }
}

def _t(lang: str, key: str) -> str:
    return L["ua" if lang == "ua" else "en"][key]

def _onoff(active: bool) -> str:
    return "✅" if active else "☐"

def _radio(active: bool) -> str:
    return "● " if active else "○ "

def _fmt_minutes(lang: str, m: int) -> str:
    return f"{m}m" if lang != "ua" else f"{m}хв"

# ---------- MAIN MENU ----------
def main_menu_kb(lang: str = "en", back_to_root: bool = False) -> InlineKeyboardMarkup:

    t_settings   = "⚙️ Settings" if lang != "ua" else "⚙️ Налаштування"
    t_digest     = "⏱ Daily Digest" if lang != "ua" else "⏱ Щоденний дайджест"
    t_alerts     = "⏰ Alerts" if lang != "ua" else "⏰ Нагадування"
    t_stop       = "🔕 Stop" if lang != "ua" else "🔕 Вимкнути"
    t_today      = "📅 Today" if lang != "ua" else "📅 Сьогодні"
    t_week       = "🗓 This week" if lang != "ua" else "🗓 Цього тижня"
    t_weekly_summary  = "📈 Weekly summary" if lang != "ua" else "📈 Підсумок тижня"
    t_tutorial   = "❓ Tutorial" if lang != "ua" else "❓ Довідка"
    t_topics     = "📚 Topics" if lang != "ua" else "📚 Теми"
    t_about      = "ℹ️ About" if lang != "ua" else "ℹ️ Про бота"
    t_faq        = "❓ FAQ" if lang != "ua" else "❓ FAQ"

    back_cb = "root:home" if back_to_root else "menu:home"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t_settings, callback_data="menu:settings")],
            [InlineKeyboardButton(text=t_digest,   callback_data="menu:subscribe")],
            [
                InlineKeyboardButton(text=t_alerts,   callback_data="menu:alerts"),
                InlineKeyboardButton(text=t_stop,     callback_data="menu:stop")
            ],
            [
                InlineKeyboardButton(text=t_today,    callback_data="menu:today"),
                InlineKeyboardButton(text=t_week,     callback_data="menu:week")
            ],
            [InlineKeyboardButton(text=t_weekly_summary, callback_data="menu:weekly")],
            [
                InlineKeyboardButton(text=t_topics,   callback_data="menu:topics"),
                InlineKeyboardButton(text=t_faq,      callback_data="menu:faq")
            ],
            [
                InlineKeyboardButton(text=t_tutorial, callback_data="menu:tutorial"),
                InlineKeyboardButton(text=t_about, callback_data="menu:about")
            ],
             [InlineKeyboardButton(text="⬅️ Back",  callback_data=back_cb)]
        ]
    )

def root_menu_kb(lang: str = "en") -> InlineKeyboardMarkup:
    t_forex  = "💱 Forex" if lang != "ua" else "💱 Форекс"
    t_metals = "🪙 Metals" if lang != "ua" else "🪙 Метали"
    
    kb = [
        [InlineKeyboardButton(text=t_forex, callback_data="root:forex")],
        [InlineKeyboardButton(text=t_metals, callback_data="root:metals")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def metals_main_menu_kb(lang: str = "en", back_to_root: bool = True) -> InlineKeyboardMarkup:
    t_settings = "⚙️ Settings" if lang != "ua" else "⚙️ Налаштування"
    t_alerts   = "⏰ Alerts" if lang != "ua" else "⏰ Нагадування"
    t_daily    = "🕰 Daily Digest" if lang != "ua" else "🕰 Щоденний дайджест"
    t_today    = "🗓 Today" if lang != "ua" else "🗓 Сьогодні"
    t_week     = "📅 This week" if lang != "ua" else "📅 Цього тижня"
    t_topics   = "📚 Topics" if lang != "ua" else "📚 Теми"
    
    back_cb = "root:home" if back_to_root else "menu:home"

    kb = [
        [InlineKeyboardButton(text=t_settings, callback_data="metals:settings"),
         InlineKeyboardButton(text=t_alerts,   callback_data="metals:alerts")],
        [InlineKeyboardButton(text=t_daily,    callback_data="metals:daily")],
        [InlineKeyboardButton(text=t_today,    callback_data="metals:today"),
         InlineKeyboardButton(text=t_week,     callback_data="metals:week")],
        [InlineKeyboardButton(text=t_topics,   callback_data="metals:topics")],
         [InlineKeyboardButton(text="⬅️ Back",  callback_data=back_cb)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_kb(lang: str = "en") -> InlineKeyboardMarkup:
    t_back = "◀️ Back" if lang != "ua" else "◀️ Назад"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t_back, callback_data="menu:home")]]
    )

# ---------- SETTINGS PANEL ----------
def settings_kb(
    selected_impacts,
    selected_currencies,
    alert_minutes,
    lang_mode: str = "en",
) -> InlineKeyboardMarkup:
    lang = lang_mode

    # --- Impacts (2x2 layout) ---
    imp_map = [
        ("High", _t(lang, "imp_high")),
        ("Medium", _t(lang, "imp_med")),
        ("Low", _t(lang, "imp_low")),
        ("Non-economic", _t(lang, "imp_noneco")),
    ]
    imp_btns = [
        InlineKeyboardButton(
            text=f"{_onoff(src in selected_impacts)} {label}",
            callback_data=f"imp:{src}"
        )
        for src, label in imp_map
    ]

    # --- Currencies 3x3 ---
    def label_curr(code: str) -> str:
        return f"{CURR_FLAGS.get(code,'')} {code}".strip()

    cur_buttons = [
        InlineKeyboardButton(
            text=f"{_onoff(code in selected_currencies)} {label_curr(code)}",
            callback_data=f"cur:{code}"
        )
        for code in COMMON_CURRENCIES
    ]

    rows = []
    # impacts split into two rows for readability
    rows.append(imp_btns[0:2])   # High, Medium
    rows.append(imp_btns[2:4])   # Low, Non-economic

    # currencies grid 3x3
    rows.append(cur_buttons[0:3])
    rows.append(cur_buttons[3:6])
    rows.append(cur_buttons[6:9])

    # --- Alert presets (2x3 layout) ---
    al_buttons = [
        InlineKeyboardButton(
            text=_radio(alert_minutes == p) + _fmt_minutes(lang, p),
            callback_data=f"al:{p}"
        ) for p in ALERT_PRESETS
    ]
    rows.append(al_buttons[0:3])
    rows.append(al_buttons[3:6])

    # language row
    lang_buttons = [
        InlineKeyboardButton(
            text=_radio(lang == "en") + _t(lang, "lang_en"),
            callback_data="lang:en"
        ),
        InlineKeyboardButton(
            text=_radio(lang == "ua") + _t(lang, "lang_ua"),
            callback_data="lang:ua"
        ),
    ]
    rows.append(lang_buttons)

    rows.append([
        InlineKeyboardButton(text=f"⏱ {_t(lang,'subscribe')}", callback_data="sub:ask"),
        InlineKeyboardButton(text=f"🧹 {_t(lang,'reset_filters')}", callback_data="reset"),
    ])
    rows.append([InlineKeyboardButton(text=f"◀️ {_t(lang,'back')}", callback_data="menu:home")])

    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- SUBSCRIBE TIME PRESETS ----------
def subscribe_time_kb(presets: list[str], lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    row = []
    for p in presets:
        row.append(InlineKeyboardButton(text=p, callback_data=f"sub:set:{p}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=f"◀️ {_t(lang,'back')}", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- ALERTS PRESETS (standalone) ----------
def alerts_presets_kb(current_minutes: int | None = None, lang: str = "en") -> InlineKeyboardMarkup:
    btns = [
        InlineKeyboardButton(
            text=_radio(current_minutes == p) + _fmt_minutes(lang, p),
            callback_data=f"al:{p}"
        ) for p in ALERT_PRESETS
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            btns[0:3],
            btns[3:6],
            [InlineKeyboardButton(text=f"◀️ {_t(lang,'back')}", callback_data="menu:home")]
        ]
    )

def metals_alerts_presets_kb(current_minutes: int | None = None, lang: str = "en") -> InlineKeyboardMarkup:
    """Alerts presets keyboard for metals menu."""
    btns = [
        InlineKeyboardButton(
            text=_radio(current_minutes == p) + _fmt_minutes(lang, p),
            callback_data=f"metals_al:{p}"
        ) for p in ALERT_PRESETS
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            btns[0:3],
            btns[3:6],
            [InlineKeyboardButton(text=f"◀️ {_t(lang,'back')}", callback_data="root:metals")]
        ]
    )

# ---------- TOPICS ----------
def topics_kb(lang: str = "en") -> InlineKeyboardMarkup:
    if lang == "ua":
        rows = [
            [
                InlineKeyboardButton(text="📈 Індекси цін (CPI/PPI)", callback_data="topic:prices"),
                InlineKeyboardButton(text="📊 ВВП (GDP)", callback_data="topic:gdp"),
            ],
            [
                InlineKeyboardButton(text="🏭 PMI", callback_data="topic:pmi"),
                InlineKeyboardButton(text="👷‍♂️ Ринок праці", callback_data="topic:labor"),
            ],
            [
                InlineKeyboardButton(text="💱 Ставки/Інфляція", callback_data="topic:rates"),
                InlineKeyboardButton(text="🏗 Торгівля/Виробн.", callback_data="topic:trade"),
            ],
            [
                InlineKeyboardButton(text="🏛 Центробанки", callback_data="topic:cbanks"),
                InlineKeyboardButton(text="📦 Інші показники", callback_data="topic:misc"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(text="📈 Price Indexes (CPI/PPI)", callback_data="topic:prices"),
                InlineKeyboardButton(text="📊 GDP", callback_data="topic:gdp"),
            ],
            [
                InlineKeyboardButton(text="🏭 PMI", callback_data="topic:pmi"),
                InlineKeyboardButton(text="👷‍♂️ Labor Market", callback_data="topic:labor"),
            ],
            [
                InlineKeyboardButton(text="💱 Rates/Inflation", callback_data="topic:rates"),
                InlineKeyboardButton(text="🏗 Trade/Production", callback_data="topic:trade"),
            ],
            [
                InlineKeyboardButton(text="🏛 Central Banks", callback_data="topic:cbanks"),
                InlineKeyboardButton(text="📦 Other Indicators", callback_data="topic:misc"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="menu:home")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_to_topics_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_t(lang, "back_topics"), callback_data="menu:topics")]]
    )

def metals_topics_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Topics keyboard for Metals calendar."""
    if lang == "ua":
        rows = [
            [
                InlineKeyboardButton(text="🪙 Метали та товари", callback_data="metals_topic:metals_commodities"),
                InlineKeyboardButton(text="📊 Облігації", callback_data="metals_topic:bonds"),
            ],
            [
                InlineKeyboardButton(text="📈 Індекси цін", callback_data="metals_topic:metals_prices"),
                InlineKeyboardButton(text="💹 Дані ВВП", callback_data="metals_topic:metals_gdp"),
            ],
            [
                InlineKeyboardButton(text="🏭 PMI та виробництво", callback_data="metals_topic:metals_production"),
            ],
            [
                InlineKeyboardButton(text="🏛 Центробанки", callback_data="metals_topic:metals_central_banks"),
            ],
            [
                InlineKeyboardButton(text="📦 Економічні показники", callback_data="metals_topic:metals_indicators"),
                InlineKeyboardButton(text="🔔 Загальні події", callback_data="metals_topic:metals_neutral"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="root:metals")],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(text="🪙 Metals & Commodities", callback_data="metals_topic:metals_commodities"),
                InlineKeyboardButton(text="📊 Bonds", callback_data="metals_topic:bonds"),
            ],
            [
                InlineKeyboardButton(text="📈 Price Indexes", callback_data="metals_topic:metals_prices"),
                InlineKeyboardButton(text="💹 GDP Data", callback_data="metals_topic:metals_gdp"),
            ],
            [
                InlineKeyboardButton(text="🏭 PMI & Production", callback_data="metals_topic:metals_production"),
            ],
            [
                InlineKeyboardButton(text="🏛 Central Banks", callback_data="metals_topic:metals_central_banks"),
            ],
            [
                InlineKeyboardButton(text="📦 Economic Indicators", callback_data="metals_topic:metals_indicators"),
                InlineKeyboardButton(text="🔔 General Events", callback_data="metals_topic:metals_neutral"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="root:metals")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_to_metals_topics_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Back button to metals topics menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_t(lang, "back_topics"), callback_data="metals:topics")]]
    )

# ---------- METALS SETTINGS KEYBOARD ----------
def metals_settings_kb(
    selected_impacts,
    selected_countries,
    alert_minutes,
    lang_mode: str = "en",
) -> InlineKeyboardMarkup:
    """
    Settings keyboard for Metals module.
    Filters by impact and country (not currency).
    Includes alert presets.
    """
    lang = lang_mode

    # --- Impacts (2x2 layout) ---
    imp_map = [
        ("High", _t(lang, "imp_high")),
        ("Medium", _t(lang, "imp_med")),
        ("Low", _t(lang, "imp_low")),
        ("Non-economic", _t(lang, "imp_noneco")),
    ]
    imp_btns = [
        InlineKeyboardButton(
            text=f"{_onoff(src in selected_impacts)} {label}",
            callback_data=f"metals_imp:{src}"
        )
        for src, label in imp_map
    ]

    # --- Countries (3x4 grid) ---
    def label_country(code: str) -> str:
        return f"{COUNTRY_FLAGS.get(code,'')} {code}".strip()

    country_buttons = [
        InlineKeyboardButton(
            text=f"{_onoff(code in selected_countries)} {label_country(code)}",
            callback_data=f"metals_country:{code}"
        )
        for code in METALS_COUNTRIES
    ]

    rows = []
    # impacts split into two rows
    rows.append(imp_btns[0:2])   # High, Medium
    rows.append(imp_btns[2:4])   # Low, Non-economic

    # countries grid 3x4
    rows.append(country_buttons[0:3])
    rows.append(country_buttons[3:6])
    rows.append(country_buttons[6:9])
    rows.append(country_buttons[9:12])

    # --- Alert presets (2x3 layout) ---
    al_buttons = [
        InlineKeyboardButton(
            text=_radio(alert_minutes == p) + _fmt_minutes(lang, p),
            callback_data=f"metals_al:{p}"
        ) for p in ALERT_PRESETS
    ]
    rows.append(al_buttons[0:3])
    rows.append(al_buttons[3:6])

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

    # Reset and back buttons
    rows.append([
        InlineKeyboardButton(text=f"🧹 {_t(lang,'reset_filters')}", callback_data="metals_reset"),
    ])
    rows.append([InlineKeyboardButton(text=f"◀️ {_t(lang,'back')}", callback_data="root:metals")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
