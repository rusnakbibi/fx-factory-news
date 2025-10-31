# app/services/translator.py
# ==========================================
# Offline lightweight translator for FF titles
# ==========================================

from __future__ import annotations


# ---- Основний словник термінів ----
UA_DICT = {
    # Індекси цін
    "CPI y/y": "Індекс споживчих цін (р/р)",
    "CPI m/m": "Індекс споживчих цін (м/м)",
    "Core CPI": "Базовий ІСЦ",
    "CPI q/q": "Індекс споживчих цін (к/к)",
    "CPI Flash Estimate y/y": "Експрес-оцінка ІСЦ (р/р)",
    "PPI y/y": "Індекс цін виробників (р/р)",
    "PPI m/m": "Індекс цін виробників (м/м)",
    "Core PPI": "Базовий ІЦВ",
    "Import Prices m/m": "Ціни на імпорт (м/м)",
    "S&P/CS Composite-20 HPI y/y": "Індекс цін на житло S&P/CS-20 (р/р)",

    # ВВП
    "GDP q/q": "Валовий внутрішній продукт (к/к)",
    "GDP y/y": "Валовий внутрішній продукт (р/р)",
    "GDP m/m": "Валовий внутрішній продукт (м/м)",
    "Prelim GDP": "Попередній ВВП",
    "Final GDP": "Кінцевий ВВП",
    "GDP Growth": "Зростання ВВП",

    # PMI
    "Manufacturing PMI": "Індекс виробничої активності (PMI)",
    "Services PMI": "Індекс ділової активності у сфері послуг (PMI)",
    "Composite PMI": "Композитний PMI",
    "Flash Manufacturing PMI": "Попередній виробничий PMI",
    "Flash Services PMI": "Попередній сервісний PMI",
    "Richmond Manufacturing Index": "Виробничий індекс Річмонда",

    # Ринок праці
    "Unemployment Rate": "Рівень безробіття",
    "Employment Change": "Зміна кількості зайнятих",
    "Average Earnings": "Середній заробіток",
    "Wage Growth": "Зростання заробітної плати",
    "Claimant Count Change": "Зміна кількості заявок на допомогу",
    "Jobless Claims": "Заявки на допомогу з безробіття",
    "Non-Farm Employment Change": "Зміна зайнятості поза с/г",
    "Unemployment Claims": "Заявки на допомогу по безробіттю",

    # Інфляція, ставки
    "Inflation Rate": "Рівень інфляції",
    "Interest Rate Decision": "Рішення щодо процентної ставки",
    "Monetary Policy Statement": "Заява монетарної політики",
    "Rate Statement": "Заява про процентну ставку",
    "Federal Funds Rate": "Ставка федеральних фондів",
    "Fed Funds Rate": "Ставка федеральних фондів",
    "Overnight Rate": "Ставка овернайт",
    "Main Refinancing Rate": "Основна ставка рефінансування",
    "BOJ Policy Rate": "Процентна ставка Банку Японії",
    "FOMC Statement": "Заява ФРС (FOMC)",
    "FOMC Meeting": "Засідання FOMC",
    "FOMC Minutes": "Протокол засідання FOMC",
    "FOMC Press Conference": "Прес-конференція FOMC",
    "Fed Interest Rate Decision": "Рішення ФРС щодо процентної ставки",
    "ECB Press Conference": "Пресконференція ЄЦБ",
    "BOE Gov Speech": "Виступ голови Банку Англії",
    "BOJ Policy Statement": "Заява Банку Японії щодо політики",

    # Торгівля, баланс, виробництво
    "Trade Balance": "Торговельний баланс",
    "Current Account": "Поточний рахунок",
    "Retail Sales": "Роздрібні продажі",
    "Industrial Production": "Промислове виробництво",
    "Factory Orders": "Замовлення на товари виробництва",
    "Durable Goods Orders": "Замовлення на товари тривалого користування",
    "Construction Output": "Обсяг будівництва",
    "Building Permits": "Дозволи на будівництво",
    "Housing Starts": "Нові будівництва житла",
    "Pending Home Sales m/m": "Продажі житла, що очікуються (м/м)",
    "Core Retail Sales": "Базові роздрібні продажі",

    # Центробанки та інститути
    "FOMC Member": "Член FOMC",
    "Fed Chair Speech": "Виступ голови ФРС",
    "ECB President": "Президент ЄЦБ",
    "RBA Gov Bullock Speaks": "Виступ голови РБА Баллок",
    "RBNZ Gov Hawkesby Speaks": "Виступ голови РБНЗ Хоксбі",
    "BOC Business Outlook Survey": "Огляд ділових перспектив Банку Канади",
    "BOC Monetary Policy Report": "Звіт монетарної політики Банку Канади",
    "BOC Press Conference": "Прес-конференція Банку Канади",
    "BOJ Outlook Report": "Звіт Банку Японії про перспективи",
    "BOJ Press Conference": "Прес-конференція Банку Японії",

    # Інші важливі показники
    "Consumer Confidence": "Споживча впевненість",
    "Business Confidence": "Ділова впевненість",
    "Consumer Sentiment": "Споживчі настрої",
    "Core Inflation": "Базова інфляція",
    "Leading Index": "Індекс провідних індикаторів",
    "Balance of Trade": "Баланс торгівлі",
    "Budget Balance": "Бюджетний баланс",
    "PMI": "Індекс ділової активності (PMI)",
    "Economic Growth": "Економічне зростання",
    "M3 Money Supply y/y": "Грошова маса M3 (р/р)",
    "M4 Money Supply m/m": "Грошова маса M4 (м/м)",
    "Private Loans y/y": "Приватні кредити (р/р)",
    "Net Lending to Individuals m/m": "Чисте кредитування фізичних осіб (м/м)",
    "ifo Business Climate": "Індекс ділового клімату ifo",
    "KOF Economic Barometer": "Економічний барометр KOF",
    "UBS Economic Expectations": "Економічні очікування UBS",
    "CBI Realized Sales": "Реалізовані продажі CBI",
    "International Reserves": "Міжнародні резерви",

    # Нейтральні / загальні
    "Holiday": "Свято (ринок закритий)",
    "Bank Holiday": "Банківський вихідний",
    "Daylight Saving Time Shift": "Перехід на літній/зимовий час",
    "Tentative": "Попередньо",
    "IMF Meetings": "Засідання МВФ",
}


# ---- Словник термінів для металів та товарних ринків ----
METALS_DICT = {
    # Метали
    "LME Copper Inventories": "Запаси міді LME",
    
    # Нафта та енергоносії
    "Crude Oil Inventories": "Запаси сирої нафти",
    "API Weekly Statistical Bulletin": "Тижневий статистичний бюлетень API",
    
    # Облігації
    "German 10-y Bond Auction": "Аукціон 10-річних облігацій Німеччини",
    
    # Індекси цін
    "CPI y/y": "Індекс споживчих цін (р/р)",
    "CPI q/q": "Індекс споживчих цін (к/к)",
    "CPI Flash Estimate y/y": "Експрес-оцінка ІСЦ (р/р)",
    "Flash CPI y/y": "Експрес-оцінка ІСЦ (р/р)",
    "Core CPI Flash Estimate y/y": "Експрес-оцінка базового ІСЦ (р/р)",
    "Prelim CPI m/m": "Попередній ІСЦ (м/м)",
    "Tokyo Core CPI y/y": "Базовий ІСЦ Токіо (р/р)",
    "BOJ Core CPI y/y": "Базовий ІСЦ Банку Японії (р/р)",
    "Trimmed Mean CPI q/q": "Скорочений середній ІСЦ (к/к)",
    "Import Prices m/m": "Ціни на імпорт (м/м)",
    "S&P/CS Composite-20 HPI y/y": "Індекс цін на житло S&P/CS-20 (р/р)",
    
    # ВВП
    "GDP m/m": "Валовий внутрішній продукт (м/м)",
    "Flash GDP q/q": "Експрес-оцінка ВВП (к/к)",
    "Prelim GDP q/q": "Попередній ВВП (к/к)",
    "Prelim Flash GDP q/q": "Попередня експрес-оцінка ВВП (к/к)",
    "Prelim GDP y/y": "Попередній ВВП (р/р)",
    
    # PMI та виробництво
    "Manufacturing PMI": "Індекс виробничої активності (PMI)",
    "Non-Manufacturing PMI": "Індекс невиробничої активності (PMI)",
    "Chicago PMI": "Індекс ділової активності Чикаго (PMI)",
    "Richmond Manufacturing Index": "Виробничий індекс Річмонда",
    "Prelim Industrial Production m/m": "Попереднє промислове виробництво (м/м)",
    
    # Центробанки та виступи
    "BOJ Outlook Report": "Звіт Банку Японії про перспективи",
    "BOJ Press Conference": "Прес-конференція Банку Японії",
    "BOJ Policy Rate": "Процентна ставка Банку Японії",
    "Monetary Policy Statement": "Заява монетарної політики",
    "Main Refinancing Rate": "Основна ставка рефінансування",
    "ECB Press Conference": "Пресконференція ЄЦБ",
    "FOMC Statement": "Заява ФРС (FOMC)",
    "Federal Funds Rate": "Ставка федеральних фондів",
    "FOMC Press Conference": "Прес-конференція FOMC",
    "FOMC Member Bowman Speaks": "Виступ члена FOMC Боумен",
    "FOMC Member Logan Speaks": "Виступ члена FOMC Логан",
    "FOMC Member Bostic Speaks": "Виступ члена FOMC Бостік",
    "FOMC Member Hammack Speaks": "Виступ члена FOMC Хаммак",
    "RBA Gov Bullock Speaks": "Виступ голови РБА Баллок",
    "RBNZ Gov Hawkesby Speaks": "Виступ голови РБНЗ Хоксбі",
    "BOC Monetary Policy Report": "Звіт монетарної політики Банку Канади",
    "BOC Rate Statement": "Заява Банку Канади про ставку",
    "BOC Press Conference": "Прес-конференція Банку Канади",
    "Overnight Rate": "Ставка овернайт",
    
    # Інші показники
    "KOF Economic Barometer": "Економічний барометр KOF",
    "International Reserves": "Міжнародні резерви",
    "M3 Money Supply y/y": "Грошова маса M3 (р/р)",
    "M4 Money Supply m/m": "Грошова маса M4 (м/м)",
    "ifo Business Climate": "Індекс ділового клімату ifo",
    "Trade Balance": "Торговельний баланс",
    "CB Leading Index m/m": "Індекс провідних індикаторів CB (м/м)",
    "CB Consumer Confidence": "Споживча впевненість CB",
    "Pending Home Sales m/m": "Продажі житла, що очікуються (м/м)",
    "Unemployment Rate": "Рівень безробіття",
    "Gov Budget Balance": "Державний бюджетний баланс",
    
    # Нейтральні / загальні
    "Daylight Saving Time Shift": "Перехід на літній/зимовий час",
}


def translate_title(text: str, target_lang: str) -> str:
    """
    Повертає переклад назви економічної події (Forex).
    Підтримує 'en' (без перекладу) і 'ua' (через локальний словник).
    """
    if not text or target_lang == "en":
        return text

    if target_lang == "ua":
        lowered = text.lower()
        for key, value in UA_DICT.items():
            if key.lower() in lowered:
                return value
        return text  # якщо не знайдено в словнику

    # fallback: якщо target_lang не en/ua
    return text


def translate_metals_title(text: str, target_lang: str) -> str:
    """
    Повертає переклад назви події для металів та товарних ринків.
    Підтримує 'en' (без перекладу) і 'ua' (через локальний словник).
    """
    if not text or target_lang == "en":
        return text

    if target_lang == "ua":
        lowered = text.lower()
        for key, value in METALS_DICT.items():
            if key.lower() in lowered:
                return value
        return text  # якщо не знайдено в словнику

    # fallback: якщо target_lang не en/ua
    return text
