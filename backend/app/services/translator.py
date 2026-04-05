from deep_translator import GoogleTranslator
from loguru import logger

# Cache translations to avoid repeated API calls
_translation_cache = {}


def translate_to_hindi(text: str) -> str:
    """Translate English ISL label to Hindi."""
    if not text or text.strip() == "":
        return ""
    text_lower = text.strip().lower()
    if text_lower in _translation_cache:
        return _translation_cache[text_lower]
    try:
        result = GoogleTranslator(source='en', target='hi').translate(text)
        _translation_cache[text_lower] = result
        return result
    except Exception as e:
        logger.warning(f"Translation failed for '{text}': {e}")
        return text


def preload_vocabulary_translations(vocab_list: list) -> dict:
    """Pre-translate entire vocabulary at startup to cache all results."""
    translations = {}
    for word in vocab_list:
        translations[word.lower()] = translate_to_hindi(word)
    return translations
