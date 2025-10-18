from deep_translator import GoogleTranslator

def translate_title(text: str, target_lang: str) -> str:
    if not text or target_lang == "en":
        return text
    try:
        if target_lang == "auto":
            # naive: default to 'en' (source already en). You could auto-detect later.
            return text
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception:
        return text
