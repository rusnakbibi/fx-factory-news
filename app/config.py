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
IMPACTS = ["High","Medium","Low","Non-economic"]
ALERT_PRESETS = [5, 15, 30, 60]
LANG_MODES = ["en","uk","auto"]  # 'auto' = detect from system TZ (example) or default to en

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

# Куди писати агрегований JSON (локально або у тимчасову/постійну директорію на Render)
AGGREGATE_JSON_PATH = os.getenv("AGGREGATE_JSON_PATH", "aggregated_calendar.json")


TOPIC_DEFS = {
    # ---------------- ІНДЕКСИ ЦІН ----------------
    "prices": {
        "title": {"en": "Price Indexes (CPI/PPI)", "ua": "Індекси цін (CPI/PPI)"},
        "blurb": {
            "en": "CPI and PPI show how fast consumer and producer prices rise — key for inflation trends.",
            "ua": "CPI та PPI показують темпи зростання цін для споживачів і виробників — ключ до розуміння інфляції.",
        },
        "keywords": [
            "cpi", "core cpi", "ppi", "core ppi", "producer price",
            "consumer price", "inflation rate", "hicp", "rpi",
        ],
    },

    # ---------------- ВВП ----------------
    "gdp": {
        "title": {"en": "Gross Domestic Product (GDP)", "ua": "Валовий внутрішній продукт (ВВП)"},
        "blurb": {
            "en": "GDP measures overall economic activity — the main gauge of growth or recession.",
            "ua": "ВВП відображає загальну економічну активність — головний показник зростання або спаду.",
        },
        "keywords": [
            "gdp", "gross domestic", "prelim gdp", "final gdp",
            "gdp growth", "gdp q/q", "gdp y/y", "gdp m/m",
        ],
    },

    # ---------------- PMI ----------------
    "pmi": {
        "title": {"en": "Purchasing Managers Index (PMI)", "ua": "Індекс ділової активності (PMI)"},
        "blurb": {
            "en": "PMI reflects business sentiment. >50 means expansion, <50 contraction.",
            "ua": "PMI відображає ділові настрої. >50 означає зростання, <50 — спад.",
        },
        "keywords": [
            "pmi", "manufacturing pmi", "services pmi",
            "composite pmi", "flash manufacturing", "flash services",
        ],
    },

    # ---------------- РИНОК ПРАЦІ ----------------
    "labor": {
        "title": {"en": "Labor Market", "ua": "Ринок праці"},
        "blurb": {
            "en": "Employment and wage data show labor demand and consumer income trends.",
            "ua": "Дані про зайнятість і зарплати показують попит на робочу силу та рівень доходів населення.",
        },
        "keywords": [
            "unemployment", "employment change", "average earnings", "wage growth",
            "claimant count", "jobless claims", "non-farm", "unemployment rate",
        ],
    },

    # ---------------- ІНФЛЯЦІЯ, СТАВКИ ----------------
    "rates": {
        "title": {"en": "Inflation & Interest Rates", "ua": "Інфляція та процентні ставки"},
        "blurb": {
            "en": "Interest rate decisions and inflation figures shape monetary policy expectations.",
            "ua": "Рішення щодо ставок та дані про інфляцію формують очікування монетарної політики.",
        },
        "keywords": [
            "inflation rate", "interest rate", "rate statement", "fomc statement",
            "monetary policy", "policy statement", "ecb press conference",
            "boj policy statement", "boe gov speech", "core inflation",
        ],
    },

    # ---------------- ТОРГІВЛЯ, БАЛАНС, ВИРОБНИЦТВО ----------------
    "trade": {
        "title": {"en": "Trade, Balance & Production", "ua": "Торгівля, баланс та виробництво"},
        "blurb": {
            "en": "Covers trade, industrial and housing activity — indicators of real economy performance.",
            "ua": "Охоплює торгівлю, промисловість і будівництво — індикатори реального сектору економіки.",
        },
        "keywords": [
            "trade balance", "current account", "retail sales", "core retail sales",
            "industrial production", "factory orders", "durable goods orders",
            "construction output", "building permits", "housing starts",
        ],
    },

    # ---------------- ЦЕНТРОБАНКИ ТА ІНСТИТУТИ ----------------
    "cbanks": {
        "title": {"en": "Central Banks & Institutions", "ua": "Центробанки та інститути"},
        "blurb": {
            "en": "Covers speeches and releases from major central banks and policy bodies.",
            "ua": "Включає заяви та звіти основних центробанків і фінансових інституцій.",
        },
        "keywords": [
            "fomc member", "fed chair", "ecb president",
            "boc business outlook", "central bank", "rba", "rbnz", "snb",
            "lagarde", "powell", "governor", "policy decision",
        ],
    },

    # ---------------- ІНШІ ПОКАЗНИКИ ----------------
    "misc": {
        "title": {"en": "Other Economic Indicators", "ua": "Інші економічні показники"},
        "blurb": {
            "en": "Consumer and business confidence, sentiment and leading indicators.",
            "ua": "Індекси впевненості споживачів, бізнесу та провідні індикатори.",
        },
        "keywords": [
            "consumer confidence", "business confidence", "consumer sentiment",
            "leading index", "economic growth", "balance of trade",
        ],
    },

    # ---------------- НЕЙТРАЛЬНІ / ЗАГАЛЬНІ ----------------
    "neutral": {
        "title": {"en": "Neutral / General", "ua": "Нейтральні / Загальні"},
        "blurb": {
            "en": "Covers non-economic or neutral calendar events like holidays or IMF meetings.",
            "ua": "Охоплює нейтральні події або неекономічні дати, як-от вихідні чи засідання МВФ.",
        },
        "keywords": ["holiday", "bank holiday", "tentative", "imf", "meetings"],
    },
}

# ---- Per-topic explainers (EN default, UA if lang_mode == "ua") ----
TOPIC_EXPLAINERS = {
    # ---------------- ІНДЕКСИ ЦІН ----------------
    "prices": {
        "en": [
            ("CPI y/y", "Measures how much consumer prices have risen compared to a year ago. A key indicator of long-term inflation pressure."),
            ("CPI m/m", "Shows the month-over-month change in prices. Often triggers sharp short-term reactions as it reflects fresh data."),
            ("CPI q/q", "Quarterly change in consumer prices; mostly used in Australia and New Zealand releases."),
            ("Core CPI", "Excludes volatile categories like food and energy. Focused on underlying price trends that central banks watch closely."),
            ("PPI m/m", "Producer prices compared to the previous month. Reflects cost pressures in manufacturing that can later affect CPI."),
            ("PPI y/y", "Producer prices vs the same month last year. Useful for spotting long-term cost inflation for businesses."),
            ("Core PPI", "Excludes volatile producer items such as energy; a measure of core production inflation."),
            ("HICP", "Harmonised index for EU countries — makes inflation comparable across the Eurozone."),
            ("UoM Inflation Expectations", "Survey that reflects how households expect inflation to evolve in the future."),
        ],
        "ua": [
            ("CPI y/y", "Показує, наскільки споживчі ціни зросли порівняно з минулим роком. Основний індикатор довгострокового інфляційного тиску."),
            ("CPI m/m", "Відображає зміну цін за місяць. Часто викликає миттєву реакцію ринку, бо показує свіжі дані."),
            ("CPI q/q", "Квартальна зміна споживчих цін; найчастіше використовується в Австралії та Новій Зеландії."),
            ("Core CPI", "Без урахування волатильних категорій, як-от їжа чи енергоносії. Ключовий показник базової інфляції."),
            ("PPI m/m", "Ціни виробників до попереднього місяця. Відображає тиск витрат у виробництві, який згодом може перейти у CPI."),
            ("PPI y/y", "Ціни виробників у річному вимірі. Дає уявлення про тенденції витрат бізнесу."),
            ("Core PPI", "Показник виробничої інфляції без енергії та інших волатильних складових."),
            ("HICP", "Гармонізований індекс інфляції для країн ЄС — забезпечує порівнянність даних між ними."),
            ("UoM Inflation Expectations", "Опитування Мічиганського університету про очікування інфляції в коротко- та довгостроковій перспективі."),
        ],
    },

    # ---------------- ВВП ----------------
    "gdp": {
        "en": [
            ("GDP q/q", "Quarterly growth in total economic output. The clearest measure of current momentum."),
            ("GDP y/y", "Compares GDP to the same quarter last year. Useful for smoothing out volatility."),
            ("Prelim/Advance GDP", "First estimate — most market-sensitive, often revised in later releases."),
            ("Final GDP", "Updated estimate after incorporating more complete data."),
            ("GDP Growth", "General term describing expansion or contraction in the economy."),
        ],
        "ua": [
            ("GDP q/q", "Зміна ВВП до попереднього кварталу — найточніший показник поточного імпульсу зростання."),
            ("GDP y/y", "Порівняння ВВП з аналогічним кварталом минулого року. Дозволяє згладити коливання."),
            ("Prelim/Advance GDP", "Попередня оцінка, що найсильніше впливає на ринок. Може бути переглянута."),
            ("Final GDP", "Уточнена оцінка після надходження повніших даних."),
            ("GDP Growth", "Загальний показник розширення або скорочення економіки."),
        ],
    },

    # ---------------- PMI ----------------
    "pmi": {
        "en": [
            ("Manufacturing PMI", "Survey of manufacturers — above 50 means expansion, below 50 contraction."),
            ("Services PMI", "Measures activity in the services sector, which dominates most modern economies."),
            ("Composite PMI", "Weighted combination of manufacturing and services — snapshot of total business conditions."),
            ("Flash PMI", "Preliminary reading for the month; comes earlier and often moves markets."),
        ],
        "ua": [
            ("Manufacturing PMI", "Опитування виробників — понад 50 означає зростання, менше 50 — спад."),
            ("Services PMI", "Відображає активність у секторі послуг, який є основним у більшості економік."),
            ("Composite PMI", "Комбінує виробничий і сервісний PMI, даючи загальну картину ділової активності."),
            ("Flash PMI", "Попередній показник за місяць — публікується раніше, тому має сильний ринковий вплив."),
        ],
    },

    # ---------------- РИНОК ПРАЦІ ----------------
    "labor": {
        "en": [
            ("Unemployment Rate", "Percentage of the labour force without work. Declines imply stronger hiring."),
            ("Employment Change", "Shows how many jobs were gained or lost — main labour market headline."),
            ("Average Earnings", "Tracks wage growth; higher wages can push inflation via stronger demand."),
            ("Jobless Claims", "Weekly or monthly count of unemployment benefit claims; high-frequency gauge of layoffs."),
            ("Non-Farm Payrolls", "U.S. jobs report excluding agriculture; highly market-sensitive release."),
        ],
        "ua": [
            ("Unemployment Rate", "Частка безробітних у робочій силі. Зниження означає зростання зайнятості."),
            ("Employment Change", "Кількість створених або втрачених робочих місць — основний заголовок ринку праці."),
            ("Average Earnings", "Відображає динаміку зарплат; зростання може підвищувати інфляцію через попит."),
            ("Jobless Claims", "Кількість заявок на допомогу з безробіття — оперативний індикатор звільнень."),
            ("Non-Farm Payrolls", "Найважливіший звіт США про робочі місця, без урахування сільського господарства."),
        ],
    },

    # ---------------- СТАВКИ ТА ІНФЛЯЦІЯ ----------------
    "rates": {
        "en": [
            ("Interest Rate Decision", "Central bank announcement on its key rate — primary tool for controlling inflation."),
            ("Rate Statement", "Details that accompany the rate decision, shaping future expectations."),
            ("FOMC/ECB/BOE/BOJ Press Conference", "Q&A sessions offering deeper insight into central bank thinking."),
            ("Monetary Policy Statement", "Official text outlining rationale for rate changes and economic outlook."),
        ],
        "ua": [
            ("Interest Rate Decision", "Оголошення центробанку щодо ключової ставки — головний інструмент контролю інфляції."),
            ("Rate Statement", "Супровідна заява, яка формує ринкові очікування щодо подальших дій."),
            ("FOMC/ECB/BOE/BOJ Press Conference", "Сесії запитань і відповідей, що розкривають позицію центробанку."),
            ("Monetary Policy Statement", "Офіційний текст із поясненням рішення та прогнозом для економіки."),
        ],
    },

    # ---------------- ТОРГІВЛЯ, БАЛАНС, ВИРОБНИЦТВО ----------------
    "trade": {
        "en": [
            ("Trade Balance", "Difference between exports and imports. Surpluses strengthen currency; deficits weaken it."),
            ("Current Account", "Covers trade plus income flows and transfers; measures national saving vs investment."),
            ("Retail Sales", "Tracks consumer spending — vital for gauging domestic demand."),
            ("Industrial Production", "Measures manufacturing and energy output; reflects industrial cycle."),
            ("Building Permits", "Early indicator of construction activity and housing demand."),
        ],
        "ua": [
            ("Trade Balance", "Різниця між експортом та імпортом. Профіцит зміцнює валюту, дефіцит — послаблює."),
            ("Current Account", "Включає торгівлю, доходи й трансфери. Відображає співвідношення заощаджень та інвестицій."),
            ("Retail Sales", "Вимірює споживчі витрати — ключовий показник внутрішнього попиту."),
            ("Industrial Production", "Оцінює обсяги виробництва в промисловості та енергетиці."),
            ("Building Permits", "Ранній сигнал активності у сфері будівництва та житлового попиту."),
        ],
    },

    # ---------------- ЦЕНТРОБАНКИ ----------------
    "cbanks": {
        "en": [
            ("Central Bank Speech", "Public remarks by top officials often move markets via policy hints."),
            ("FOMC Statement", "U.S. Fed’s main communication tool — outlines rate stance and risks."),
            ("ECB/BOE/BOJ Decision", "Policy updates from major central banks that set global tone."),
        ],
        "ua": [
            ("Central Bank Speech", "Виступи посадовців центробанків часто рухають ринки через натяки на політику."),
            ("FOMC Statement", "Основний канал комунікації ФРС США — містить позицію щодо ставок і ризиків."),
            ("ECB/BOE/BOJ Decision", "Рішення головних центробанків світу, що задають загальний ринковий тон."),
        ],
    },

    # ---------------- ІНШІ ----------------
    "misc": {
        "en": [
            ("Consumer Confidence", "Measures household optimism about income and jobs; often leads spending trends."),
            ("Business Confidence", "Firms’ outlook on sales and investment; can signal economic turning points."),
            ("Leading Index", "Composite forward-looking indicator summarising expected growth direction."),
        ],
        "ua": [
            ("Consumer Confidence", "Відображає впевненість домогосподарств у доходах та роботі — випереджає витратні тренди."),
            ("Business Confidence", "Оцінює настрої бізнесу щодо продажів і інвестицій; часто сигналізує про поворотні точки."),
            ("Leading Index", "Композитний індикатор, що прогнозує напрямок економічного зростання."),
        ],
    },

    # ---------------- НЕЙТРАЛЬНІ ----------------
    "neutral": {
        "en": [
            ("Holiday", "Public or national holiday. Market liquidity drops and volatility can rise."),
            ("Bank Holiday", "Financial institutions closed; FX remains open but with thinner volumes."),
            ("Tentative", "Unconfirmed or flexible event — may shift or be cancelled."),
            ("IMF Meetings", "Gatherings of international financial officials. Policy remarks can occasionally move markets."),
            ("Daylight Saving Time Shift", "Seasonal time change affecting session overlaps and trading hours."),
        ],
        "ua": [
            ("Holiday", "Державне або національне свято. Ліквідність знижується, волатильність може зростати."),
            ("Bank Holiday", "Банки зачинені; ринки FX працюють, але з меншими обсягами торгів."),
            ("Tentative", "Подія не має фіксованого часу або може бути скасована."),
            ("IMF Meetings", "Зустрічі міжнародних фінансових інституцій; заяви можуть вплинути на ринок."),
            ("Daylight Saving Time Shift", "Перехід на літній/зимовий час — змінює перекривання торгових сесій."),
        ],
    },
}