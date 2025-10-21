# app/translator.py
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
    "PPI y/y": "Індекс цін виробників (р/р)",
    "PPI m/m": "Індекс цін виробників (м/м)",
    "Core PPI": "Базовий ІЦВ",

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
    "FOMC Statement": "Заява ФРС (FOMC)",
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
    "Core Retail Sales": "Базові роздрібні продажі",

    # Центробанки та інститути
    "FOMC Member": "Член FOMC",
    "Fed Chair Speech": "Виступ голови ФРС",
    "ECB President": "Президент ЄЦБ",
    "BOC Business Outlook Survey": "Огляд ділових перспектив Банку Канади",

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

    # Нейтральні / загальні
    "Holiday": "Свято (ринок закритий)",
    "Bank Holiday": "Банківський вихідний",
    "Tentative": "Попередньо",
    "IMF Meetings": "Засідання МВФ",
}


def translate_title(text: str, target_lang: str) -> str:
    """
    Повертає переклад назви економічної події.
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