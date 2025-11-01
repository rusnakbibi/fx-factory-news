# app/config/topics.py
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
            "cpi flash estimate", "import prices", "s&p/cs composite", "hpi",
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
            "richmond manufacturing index",
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
            "overnight rate", "main refinancing rate", "boj policy rate",
            "federal funds rate", "fed funds rate", "fomc minutes", "fomc meeting",
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
            "pending home sales",
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
            "rba gov bullock", "rbnz gov hawkesby", "boc monetary policy report",
            "boc press conference", "boj outlook report", "boj press conference",
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
            "leading index", "economic growth", "balance of trade", "budget balance",
            "m3 money supply", "m4 money supply", "private loans", "net lending",
            "ifo business climate", "kof economic barometer", "ubs economic expectations",
            "cbi realized sales", "international reserves",
        ],
    },

    # ---------------- НЕЙТРАЛЬНІ / ЗАГАЛЬНІ ----------------
    "neutral": {
        "title": {"en": "Neutral / General", "ua": "Нейтральні / Загальні"},
        "blurb": {
            "en": "Covers non-economic or neutral calendar events like holidays or IMF meetings.",
            "ua": "Охоплює нейтральні події або неекономічні дати, як-от вихідні чи засідання МВФ.",
        },
        "keywords": ["holiday", "bank holiday", "tentative", "imf", "meetings", "daylight saving time shift"],
    },
}


# ---- Metals & Commodities Topic Definitions ----
METALS_TOPIC_DEFS = {
    # ---------------- МЕТАЛИ ТА СИРОВИНА ----------------
    "metals_commodities": {
        "title": {"en": "Metals & Commodities", "ua": "Метали та товари"},
        "blurb": {
            "en": "Commodity inventories and metal markets — copper, oil, and other raw materials.",
            "ua": "Запаси товарів і ринки металів — мідь, нафта та інші сировинні матеріали.",
        },
        "keywords": [
            "lme copper", "crude oil", "api", "inventories",
        ],
    },
    
    # ---------------- ОБЛІГАЦІЇ ----------------
    "bonds": {
        "title": {"en": "Bonds & Auctions", "ua": "Облігації та аукціони"},
        "blurb": {
            "en": "Government bond auctions and fixed income market events.",
            "ua": "Аукціони державних облігацій та події на ринку боргових цінних паперів.",
        },
        "keywords": [
            "bond auction", "german bond", "10-y bond",
        ],
    },
    
    # ---------------- ІНДЕКСИ ЦІН ----------------
    "metals_prices": {
        "title": {"en": "Price Indexes", "ua": "Індекси цін"},
        "blurb": {
            "en": "CPI and inflation data from metals calendar sources.",
            "ua": "Дані CPI та інфляції з джерел календаря металів.",
        },
        "keywords": [
            "cpi", "flash cpi", "prelim cpi", "core cpi", "tokyo cpi", "boj core cpi",
            "trimmed mean cpi", "import prices", "s&p/cs composite", "hpi",
        ],
    },
    
    # ---------------- ВВП ----------------
    "metals_gdp": {
        "title": {"en": "GDP Data", "ua": "Дані ВВП"},
        "blurb": {
            "en": "GDP releases and economic growth indicators from metals calendar.",
            "ua": "Випуски даних ВВП та індикатори економічного зростання з календаря металів.",
        },
        "keywords": [
            "gdp", "flash gdp", "prelim gdp", "prelim flash gdp",
        ],
    },
    
    # ---------------- PMI ТА ВИРОБНИЦТВО ----------------
    "metals_production": {
        "title": {"en": "PMI & Production", "ua": "PMI та виробництво"},
        "blurb": {
            "en": "Manufacturing indexes and industrial production data.",
            "ua": "Виробничі індекси та дані промислового виробництва.",
        },
        "keywords": [
            "manufacturing pmi", "non-manufacturing pmi", "chicago pmi",
            "richmond manufacturing", "prelim industrial production",
        ],
    },
    
    # ---------------- ЦЕНТРОБАНКИ ----------------
    "metals_central_banks": {
        "title": {"en": "Central Banks", "ua": "Центробанки"},
        "blurb": {
            "en": "Central bank decisions, speeches, and policy statements.",
            "ua": "Рішення центробанків, виступи та заяви щодо політики.",
        },
        "keywords": [
            "boj outlook", "boj press conference", "boj policy rate",
            "monetary policy statement", "main refinancing rate", "ecb press conference",
            "fomc statement", "federal funds rate", "fomc press conference",
            "fomc member", "bowman", "logan", "bostic", "hammack",
            "rba gov bullock", "rbnz gov hawkesby",
            "boc monetary policy", "boc rate statement", "boc press conference",
            "overnight rate",
        ],
    },
    
    # ---------------- ІНШІ ПОКАЗНИКИ ----------------
    "metals_indicators": {
        "title": {"en": "Economic Indicators", "ua": "Економічні показники"},
        "blurb": {
            "en": "Money supply, confidence indexes, and other economic metrics.",
            "ua": "Грошова маса, індекси впевненості та інші економічні показники.",
        },
        "keywords": [
            "kof economic barometer", "international reserves",
            "m3 money supply", "m4 money supply", "ifo business climate",
            "trade balance", "cb leading index", "cb consumer confidence",
            "pending home sales", "unemployment rate", "gov budget balance",
        ],
    },
    
    # ---------------- НЕЙТРАЛЬНІ ----------------
    "metals_neutral": {
        "title": {"en": "General Events", "ua": "Загальні події"},
        "blurb": {
            "en": "Non-economic events affecting market schedules.",
            "ua": "Неекономічні події, що впливають на графік ринку.",
        },
        "keywords": [
            "daylight saving time", "time shift",
        ],
    },
}


# ---- Metals & Commodities Topic Explainers ----
METALS_TOPIC_EXPLAINERS = {
    # ---------------- МЕТАЛИ ТА СИРОВИНА ----------------
    "metals_commodities": {
        "en": [
            ("LME Copper Inventories", "London Metal Exchange copper stocks; indicator of global industrial demand and supply conditions."),
            ("Crude Oil Inventories", "U.S. weekly oil stockpiles; affects energy prices, inflation, and USD-CAD movements."),
            ("API Weekly Statistical Bulletin", "American Petroleum Institute's oil inventory data; precedes official EIA release."),
        ],
        "ua": [
            ("LME Copper Inventories", "Запаси міді на Лондонській біржі металів; індикатор глобального промислового попиту та умов постачання."),
            ("Crude Oil Inventories", "Тижневі запаси нафти в США; впливає на ціни на енергоносії, інфляцію та рух USD-CAD."),
            ("API Weekly Statistical Bulletin", "Дані API про запаси нафти; передує офіційному звіту EIA."),
        ],
    },
    
    # ---------------- ОБЛІГАЦІЇ ----------------
    "bonds": {
        "en": [
            ("German 10-y Bond Auction", "Sale of German government bonds; influences EUR yields and borrowing costs across Eurozone."),
        ],
        "ua": [
            ("German 10-y Bond Auction", "Продаж німецьких державних облігацій; впливає на дохідність EUR та вартість позик у Єврозоні."),
        ],
    },
    
    # ---------------- ІНДЕКСИ ЦІН ----------------
    "metals_prices": {
        "en": [
            ("CPI y/y", "Year-over-year consumer price change; key inflation gauge for monetary policy."),
            ("CPI q/q", "Quarterly consumer price change; common in Australia and New Zealand."),
            ("Flash CPI y/y", "Preliminary inflation estimate; early release moves markets sharply."),
            ("CPI Flash Estimate y/y", "Preliminary year-over-year inflation estimate; early Eurozone release with high market impact."),
            ("Core CPI Flash Estimate", "Excluding food and energy; shows underlying inflation trends."),
            ("Core CPI Flash Estimate y/y", "Year-over-year core inflation flash; excludes volatile items, reveals policy-relevant price pressure."),
            ("Prelim CPI m/m", "First estimate of monthly price changes; subject to revisions."),
            ("Tokyo Core CPI", "Excludes fresh food; early indicator for Japan's national inflation."),
            ("BOJ Core CPI", "Bank of Japan's preferred inflation measure excluding food and energy."),
            ("Trimmed Mean CPI", "Statistical measure removing extreme price changes; smooths volatility."),
            ("Import Prices", "Cost of imported goods; reflects external price pressures and FX effects."),
            ("S&P/CS Composite-20 HPI", "Home price index for 20 major U.S. cities; housing market strength indicator."),
        ],
        "ua": [
            ("CPI y/y", "Зміна споживчих цін за рік; ключовий показник інфляції для монетарної політики."),
            ("CPI q/q", "Квартальна зміна споживчих цін; поширена в Австралії та Новій Зеландії."),
            ("Flash CPI y/y", "Попередня оцінка інфляції; ранній випуск сильно рухає ринки."),
            ("CPI Flash Estimate y/y", "Попередня річна оцінка інфляції; ранній випуск для Єврозони з високим ринковим впливом."),
            ("Core CPI Flash Estimate", "Без їжі та енергії; показує базові інфляційні тренди."),
            ("Core CPI Flash Estimate y/y", "Річна експрес-оцінка базової інфляції; без волатильних складових, показує ціновий тиск для політики."),
            ("Prelim CPI m/m", "Перша оцінка місячних цінових змін; підлягає ревізіям."),
            ("Tokyo Core CPI", "Без свіжої їжі; ранній індикатор національної інфляції Японії."),
            ("BOJ Core CPI", "Пріоритетний показник інфляції Банку Японії без їжі та енергії."),
            ("Trimmed Mean CPI", "Статистична міра, що виключає екстремальні цінові зміни; згладжує волатильність."),
            ("Import Prices", "Вартість імпортних товарів; відображає зовнішній ціновий тиск та ефекти валютного курсу."),
            ("S&P/CS Composite-20 HPI", "Індекс цін на житло для 20 великих міст США; індикатор сили ринку нерухомості."),
        ],
    },
    
    # ---------------- ВВП ----------------
    "metals_gdp": {
        "en": [
            ("GDP m/m", "Monthly GDP change; high-frequency growth indicator."),
            ("Flash GDP q/q", "Preliminary quarterly GDP estimate; first look at economic performance."),
            ("Prelim GDP q/q", "Early GDP reading; most market-sensitive, often revised."),
            ("Prelim Flash GDP q/q", "Very early GDP estimate; combines preliminary and flash methodologies."),
            ("Prelim GDP y/y", "Preliminary year-over-year GDP; smooths out seasonal variations."),
        ],
        "ua": [
            ("GDP m/m", "Місячна зміна ВВП; високочастотний індикатор зростання."),
            ("Flash GDP q/q", "Попередня квартальна оцінка ВВП; перший погляд на економічні показники."),
            ("Prelim GDP q/q", "Рання оцінка ВВП; найчутливіша для ринку, часто переглядається."),
            ("Prelim Flash GDP q/q", "Дуже рання оцінка ВВП; поєднує попередню та експрес-методологію."),
            ("Prelim GDP y/y", "Попередній ВВП за рік; згладжує сезонні коливання."),
        ],
    },
    
    # ---------------- PMI ТА ВИРОБНИЦТВО ----------------
    "metals_production": {
        "en": [
            ("Manufacturing PMI", "Manufacturers survey; above 50 signals expansion, below 50 contraction."),
            ("Non-Manufacturing PMI", "Services sector activity index; dominant in modern economies."),
            ("Chicago PMI", "Chicago-area business conditions; regional manufacturing gauge."),
            ("Richmond Manufacturing Index", "Richmond Fed's manufacturing survey; early production trends indicator."),
            ("Prelim Industrial Production", "Early estimate of factory and energy output; reflects industrial cycle."),
        ],
        "ua": [
            ("Manufacturing PMI", "Опитування виробників; понад 50 сигналізує розширення, менше 50 — скорочення."),
            ("Non-Manufacturing PMI", "Індекс активності сектору послуг; домінує в сучасних економіках."),
            ("Chicago PMI", "Ділові умови в районі Чикаго; регіональний виробничий індикатор."),
            ("Richmond Manufacturing Index", "Виробниче опитування ФРС Річмонда; ранній індикатор виробничих трендів."),
            ("Prelim Industrial Production", "Рання оцінка обсягів заводів і енергетики; відображає промисловий цикл."),
        ],
    },
    
    # ---------------- ЦЕНТРОБАНКИ ----------------
    "metals_central_banks": {
        "en": [
            ("BOJ Outlook Report", "Bank of Japan's economic forecast; key for JPY traders and policy expectations."),
            ("BOJ Press Conference", "Governor's remarks after policy meeting; reveals BOJ's policy stance."),
            ("BOJ Policy Rate", "Bank of Japan's benchmark rate; historically near zero or negative."),
            ("Monetary Policy Statement", "Official policy text; explains rate decisions and economic outlook."),
            ("Main Refinancing Rate", "ECB's key rate for Eurozone banks; main EUR monetary policy tool."),
            ("ECB Press Conference", "ECB President's Q&A; offers insight into European monetary policy."),
            ("FOMC Statement", "Federal Reserve's policy announcement; outlines U.S. rate stance and risks."),
            ("Federal Funds Rate", "Fed's target for overnight bank lending; primary U.S. inflation control tool."),
            ("FOMC Press Conference", "Fed Chair's remarks; provides forward guidance on policy direction."),
            ("FOMC Member Speaks", "Speeches by Fed officials; can signal policy shifts or confirm current stance."),
            ("FOMC Member Bowman Speaks", "Fed Governor Michelle Bowman's remarks; provides insight into FOMC voting member views."),
            ("FOMC Member Logan Speaks", "Fed official Lorie Logan's speech; offers perspective on Fed policy direction."),
            ("FOMC Member Bostic Speaks", "Atlanta Fed President Raphael Bostic's remarks; regional Fed voice on monetary policy."),
            ("FOMC Member Hammack Speaks", "Fed official Beth Hammack's speech; contributes to understanding of Fed policy stance."),
            ("RBA Gov Bullock Speaks", "Reserve Bank of Australia Governor's speech; signals AUD rate outlook."),
            ("RBNZ Gov Hawkesby Speaks", "RBNZ official's remarks; provides NZD policy direction insights."),
            ("BOC Monetary Policy Report", "Bank of Canada's detailed forecast; guides CAD rate expectations."),
            ("BOC Rate Statement", "Bank of Canada's policy announcement; immediate CAD market mover."),
            ("BOC Press Conference", "BOC officials' Q&A; clarifies policy stance for Canadian dollar."),
            ("Overnight Rate", "Central bank rate for overnight lending; set by BOC and others."),
        ],
        "ua": [
            ("BOJ Outlook Report", "Економічний прогноз Банку Японії; ключовий для трейдерів JPY та очікувань політики."),
            ("BOJ Press Conference", "Заяви голови після засідання; розкривають позицію політики БЯ."),
            ("BOJ Policy Rate", "Базова ставка Банку Японії; історично близька до нуля або негативна."),
            ("Monetary Policy Statement", "Офіційний текст політики; пояснює рішення щодо ставок та економічний прогноз."),
            ("Main Refinancing Rate", "Ключова ставка ЄЦБ для банків Єврозони; основний інструмент монетарної політики EUR."),
            ("ECB Press Conference", "Запитання та відповіді президента ЄЦБ; дає уявлення про європейську монетарну політику."),
            ("FOMC Statement", "Оголошення політики Федрезерву; окреслює позицію США щодо ставок та ризиків."),
            ("Federal Funds Rate", "Цільова ставка ФРС для міжбанківського кредитування овернайт; основний інструмент контролю інфляції США."),
            ("FOMC Press Conference", "Заяви голови ФРС; надає орієнтири щодо напрямку політики."),
            ("FOMC Member Speaks", "Виступи посадовців ФРС; можуть сигналізувати зміни політики або підтверджувати поточну позицію."),
            ("FOMC Member Bowman Speaks", "Заяви голови ФРС Мішель Боумен; надає уявлення про погляди голосуючого члена FOMC."),
            ("FOMC Member Logan Speaks", "Виступ посадовця ФРС Лорі Логан; пропонує перспективу щодо напрямку політики ФРС."),
            ("FOMC Member Bostic Speaks", "Заяви президента ФРС Атланти Рафаеля Бостіка; регіональний голос ФРС щодо монетарної політики."),
            ("FOMC Member Hammack Speaks", "Виступ посадовця ФРС Бет Хаммак; сприяє розумінню позиції політики ФРС."),
            ("RBA Gov Bullock Speaks", "Виступ голови Резервного банку Австралії; сигналізує про перспективи ставок AUD."),
            ("RBNZ Gov Hawkesby Speaks", "Заяви посадовця РБНЗ; надає уявлення про напрямок політики NZD."),
            ("BOC Monetary Policy Report", "Детальний прогноз Банку Канади; формує очікування щодо ставок CAD."),
            ("BOC Rate Statement", "Оголошення політики Банку Канади; миттєво рухає ринок CAD."),
            ("BOC Press Conference", "Запитання та відповіді посадовців БК; прояснює позицію політики для канадського долара."),
            ("Overnight Rate", "Ставка центробанку для кредитування овернайт; встановлюється БК та іншими."),
        ],
    },
    
    # ---------------- ІНШІ ПОКАЗНИКИ ----------------
    "metals_indicators": {
        "en": [
            ("KOF Economic Barometer", "Swiss forward-looking indicator; predicts Swiss GDP and CHF trends."),
            ("International Reserves", "Central bank FX and gold holdings; reflects intervention capacity."),
            ("M3 Money Supply", "Broad money measure; tracks liquidity and inflation pressures."),
            ("M4 Money Supply", "Even broader money aggregate; includes near-cash assets, mainly UK."),
            ("ifo Business Climate", "German business sentiment survey; leading Eurozone indicator."),
            ("Trade Balance", "Exports minus imports; surpluses strengthen currency, deficits weaken."),
            ("CB Leading Index", "Conference Board's forward-looking indicator; signals economic direction."),
            ("CB Consumer Confidence", "Household optimism measure; leads spending and growth trends."),
            ("Pending Home Sales", "Signed but not closed home contracts; leading housing market indicator."),
            ("Unemployment Rate", "Jobless percentage of workforce; declines signal economic strength."),
            ("Gov Budget Balance", "Government revenue minus spending; affects fiscal policy and yields."),
        ],
        "ua": [
            ("KOF Economic Barometer", "Швейцарський випереджаючий індикатор; прогнозує ВВП Швейцарії та тренди CHF."),
            ("International Reserves", "Валютні та золоті запаси центробанку; відображає можливості інтервенції."),
            ("M3 Money Supply", "Широкий грошовий показник; відстежує ліквідність та інфляційний тиск."),
            ("M4 Money Supply", "Ще ширший грошовий агрегат; включає майже-готівкові активи, переважно у Великобританії."),
            ("ifo Business Climate", "Опитування німецьких ділових настроїв; випереджаючий індикатор Єврозони."),
            ("Trade Balance", "Експорт мінус імпорт; профіцит зміцнює валюту, дефіцит послаблює."),
            ("CB Leading Index", "Випереджаючий індикатор Conference Board; сигналізує про економічний напрямок."),
            ("CB Consumer Confidence", "Міра оптимізму домогосподарств; випереджає тренди витрат і зростання."),
            ("Pending Home Sales", "Підписані, але не закриті контракти на житло; випереджаючий індикатор ринку нерухомості."),
            ("Unemployment Rate", "Відсоток безробітних у робочій силі; зниження сигналізує про економічну силу."),
            ("Gov Budget Balance", "Доходи мінус видатки уряду; впливає на фіскальну політику та дохідність."),
        ],
    },
    
    # ---------------- НЕЙТРАЛЬНІ ----------------
    "metals_neutral": {
        "en": [
            ("Daylight Saving Time Shift", "Seasonal time change; affects trading session overlaps and market hours."),
        ],
        "ua": [
            ("Daylight Saving Time Shift", "Сезонна зміна часу; впливає на перекриття торгових сесій та години роботи ринку."),
        ],
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
            ("CPI Flash Estimate", "Preliminary inflation reading for the Eurozone; comes early and often moves EUR pairs sharply."),
            ("Import Prices", "Tracks cost of imported goods; reflects external inflation pressures from trade and FX."),
            ("S&P/CS Composite-20 HPI", "U.S. house price index covering 20 major metro areas; signals housing market strength."),
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
            ("CPI Flash Estimate", "Попередній показник інфляції для Єврозони; виходить рано і часто сильно рухає пари з EUR."),
            ("Import Prices", "Відслідковує вартість імпортних товарів; показує зовнішній інфляційний тиск через торгівлю та валютний курс."),
            ("S&P/CS Composite-20 HPI", "Індекс цін на житло у 20 найбільших американських містах; сигналізує про стан ринку нерухомості."),
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
            ("Richmond Manufacturing Index", "Regional U.S. manufacturing survey from the Richmond Fed; early gauge of production trends."),
        ],
        "ua": [
            ("Manufacturing PMI", "Опитування виробників — понад 50 означає зростання, менше 50 — спад."),
            ("Services PMI", "Відображає активність у секторі послуг, який є основним у більшості економік."),
            ("Composite PMI", "Комбінує виробничий і сервісний PMI, даючи загальну картину ділової активності."),
            ("Flash PMI", "Попередній показник за місяць — публікується раніше, тому має сильний ринковий вплив."),
            ("Richmond Manufacturing Index", "Регіональне опитування виробників від ФРС Річмонда; ранній індикатор виробничих трендів."),
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
            ("Federal Funds Rate", "U.S. Fed's target rate for overnight lending between banks; primary tool for controlling U.S. inflation."),
            ("Overnight Rate", "Rate at which banks lend to each other overnight; set by central banks like BOC."),
            ("Main Refinancing Rate", "ECB's key lending rate for banks in the Eurozone; main lever for EUR monetary policy."),
            ("BOJ Policy Rate", "Bank of Japan's benchmark interest rate; historically near zero or negative."),
            ("FOMC Minutes", "Detailed record of the Fed's meeting discussions; reveals member views and forward guidance."),
            ("FOMC Meeting", "Scheduled gathering where the Fed decides on interest rates and policy direction."),
        ],
        "ua": [
            ("Interest Rate Decision", "Оголошення центробанку щодо ключової ставки — головний інструмент контролю інфляції."),
            ("Rate Statement", "Супровідна заява, яка формує ринкові очікування щодо подальших дій."),
            ("FOMC/ECB/BOE/BOJ Press Conference", "Сесії запитань і відповідей, що розкривають позицію центробанку."),
            ("Monetary Policy Statement", "Офіційний текст із поясненням рішення та прогнозом для економіки."),
            ("Federal Funds Rate", "Цільова ставка ФРС для міжбанківського кредитування овернайт; основний інструмент контролю інфляції в США."),
            ("Overnight Rate", "Ставка, за якою банки кредитують одне одного овернайт; встановлюється центробанками, як-от Банк Канади."),
            ("Main Refinancing Rate", "Ключова ставка ЄЦБ для кредитування банків у Єврозоні; основний важіль монетарної політики EUR."),
            ("BOJ Policy Rate", "Базова процентна ставка Банку Японії; історично на рівні нуля або негативна."),
            ("FOMC Minutes", "Детальний протокол засідання ФРС; розкриває думки членів та орієнтири на майбутнє."),
            ("FOMC Meeting", "Заплановане засідання, на якому ФРС приймає рішення щодо ставок і напрямку політики."),
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
            ("Pending Home Sales", "Tracks home purchase contracts signed but not yet closed; leading indicator for the housing market."),
        ],
        "ua": [
            ("Trade Balance", "Різниця між експортом та імпортом. Профіцит зміцнює валюту, дефіцит — послаблює."),
            ("Current Account", "Включає торгівлю, доходи й трансфери. Відображає співвідношення заощаджень та інвестицій."),
            ("Retail Sales", "Вимірює споживчі витрати — ключовий показник внутрішнього попиту."),
            ("Industrial Production", "Оцінює обсяги виробництва в промисловості та енергетиці."),
            ("Building Permits", "Ранній сигнал активності у сфері будівництва та житлового попиту."),
            ("Pending Home Sales", "Відстежує підписані, але ще не завершені угоди купівлі житла; випереджаючий індикатор ринку нерухомості."),
        ],
    },

    # ---------------- ЦЕНТРОБАНКИ ----------------
    "cbanks": {
        "en": [
            ("Central Bank Speech", "Public remarks by top officials often move markets via policy hints."),
            ("FOMC Statement", "U.S. Fed's main communication tool — outlines rate stance and risks."),
            ("ECB/BOE/BOJ Decision", "Policy updates from major central banks that set global tone."),
            ("RBA Gov Bullock Speaks", "Speech by Reserve Bank of Australia Governor; can signal rate outlook for AUD."),
            ("RBNZ Gov Hawkesby Speaks", "Speech by Reserve Bank of New Zealand official; offers insight into NZD policy direction."),
            ("BOC Monetary Policy Report", "Bank of Canada's detailed economic and inflation forecast; guides rate expectations."),
            ("BOC Press Conference", "Q&A session after BOC rate decision; clarifies policy stance for CAD."),
            ("BOJ Outlook Report", "Bank of Japan's forward-looking economic assessment; key for JPY traders."),
            ("BOJ Press Conference", "Governor's remarks after policy meeting; reveals BOJ's view on rates and yield curve control."),
        ],
        "ua": [
            ("Central Bank Speech", "Виступи посадовців центробанків часто рухають ринки через натяки на політику."),
            ("FOMC Statement", "Основний канал комунікації ФРС США — містить позицію щодо ставок і ризиків."),
            ("ECB/BOE/BOJ Decision", "Рішення головних центробанків світу, що задають загальний ринковий тон."),
            ("RBA Gov Bullock Speaks", "Виступ голови Резервного банку Австралії; може сигналізувати про перспективи ставок для AUD."),
            ("RBNZ Gov Hawkesby Speaks", "Виступ посадовця Резервного банку Нової Зеландії; дає уявлення про напрямок політики для NZD."),
            ("BOC Monetary Policy Report", "Детальний економічний прогноз Банку Канади; формує очікування щодо ставок."),
            ("BOC Press Conference", "Сесія запитань після рішення Банку Канади; прояснює позицію політики для CAD."),
            ("BOJ Outlook Report", "Прогнозна економічна оцінка Банку Японії; ключовий документ для трейдерів JPY."),
            ("BOJ Press Conference", "Заяви голови після засідання; розкривають погляд БЯ на ставки та контроль кривої дохідності."),
        ],
    },

    # ---------------- ІНШІ ----------------
    "misc": {
        "en": [
            ("Consumer Confidence", "Measures household optimism about income and jobs; often leads spending trends."),
            ("Business Confidence", "Firms' outlook on sales and investment; can signal economic turning points."),
            ("Leading Index", "Composite forward-looking indicator summarising expected growth direction."),
            ("Budget Balance", "Government revenue minus spending; deficits can influence fiscal policy and bond yields."),
            ("M3 Money Supply", "Broad measure of money in circulation; tracks liquidity and potential inflation pressures."),
            ("M4 Money Supply", "Even broader money aggregate including near-cash assets; used mainly in the UK."),
            ("Private Loans", "Lending to households and businesses; signals credit growth and economic expansion."),
            ("Net Lending to Individuals", "Change in consumer borrowing; reflects household spending capacity and confidence."),
            ("ifo Business Climate", "German survey of business sentiment; leading indicator for Eurozone's largest economy."),
            ("KOF Economic Barometer", "Swiss forward-looking indicator; predicts Swiss GDP trends and CHF direction."),
            ("UBS Economic Expectations", "Swiss bank's survey of economic outlook; moves CHF when diverging from consensus."),
            ("CBI Realized Sales", "UK retail sales survey from Confederation of British Industry; early gauge for GBP retail data."),
            ("International Reserves", "Central bank holdings of foreign currencies and gold; reflects policy capacity and FX intervention."),
        ],
        "ua": [
            ("Consumer Confidence", "Відображає впевненість домогосподарств у доходах та роботі — випереджає витратні тренди."),
            ("Business Confidence", "Оцінює настрої бізнесу щодо продажів і інвестицій; часто сигналізує про поворотні точки."),
            ("Leading Index", "Композитний індикатор, що прогнозує напрямок економічного зростання."),
            ("Budget Balance", "Різниця між доходами та видатками уряду; дефіцити впливають на фіскальну політику та дохідність облігацій."),
            ("M3 Money Supply", "Широкий показник грошей в обігу; відстежує ліквідність і потенційний інфляційний тиск."),
            ("M4 Money Supply", "Ще ширший грошовий агрегат з майже-готівковими активами; використовується головним чином у Великобританії."),
            ("Private Loans", "Кредитування домогосподарств та бізнесу; сигналізує про кредитне зростання та економічне розширення."),
            ("Net Lending to Individuals", "Зміна споживчих позик; відображає купівельну спроможність та впевненість домогосподарств."),
            ("ifo Business Climate", "Німецьке опитування ділових настроїв; випереджаючий індикатор для найбільшої економіки Єврозони."),
            ("KOF Economic Barometer", "Швейцарський випереджаючий індикатор; прогнозує тренди ВВП Швейцарії та напрямок CHF."),
            ("UBS Economic Expectations", "Опитування економічних очікувань від швейцарського банку; рухає CHF при розбіжності з консенсусом."),
            ("CBI Realized Sales", "Опитування роздрібних продажів у Великобританії від CBI; ранній індикатор для GBP роздрібних даних."),
            ("International Reserves", "Запаси центробанків у іноземних валютах та золоті; відображає можливості політики та валютних інтервенцій."),
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
