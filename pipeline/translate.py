"""
Translation module using LibreTranslate API.
Includes caching to avoid duplicate API calls for the same text.
"""

import os
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# LibreTranslate API configuration
LIBRETRANSLATE_URL = os.getenv("LIBRETRANSLATE_URL", "https://libretranslate.com")
LIBRETRANSLATE_API_KEY = os.getenv("LIBRETRANSLATE_API_KEY", "")

# Map from our language codes to LibreTranslate codes
LANG_CODE_MAP = {
    "eng": "en",
    "hin": "hi",
    "ben": "bn",
    "tam": "ta",
}

# In-memory translation cache: (text, source, target) -> translated_text
_translation_cache: Dict[tuple, str] = {}


def clear_cache():
    """Clear the translation cache (call between different processing jobs)."""
    _translation_cache.clear()


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    timeout: int = 10,
) -> Optional[str]:
    """
    Translate text using LibreTranslate API with caching.
    """
    if not text or not text.strip():
        return text

    # If source == target, no translation needed
    if source_lang == target_lang:
        return text

    # Check cache first
    cache_key = (text.strip(), source_lang, target_lang)
    if cache_key in _translation_cache:
        logger.info(f"Cache hit for: '{text[:30]}...'")
        return _translation_cache[cache_key]

    try:
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }

        if LIBRETRANSLATE_API_KEY:
            payload["api_key"] = LIBRETRANSLATE_API_KEY

        response = requests.post(
            f"{LIBRETRANSLATE_URL}/translate",
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            translated = result.get("translatedText", text)
            # Store in cache
            _translation_cache[cache_key] = translated
            return translated
        else:
            logger.warning(
                f"Translation API returned {response.status_code}: {response.text}"
            )
            return None

    except requests.exceptions.Timeout:
        logger.warning("Translation API request timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot connect to Translation API")
        return None
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return None


def translate_detections(
    detections: list,
    target_lang: str = "en",
) -> list:
    """
    Translate all text detections to the target language.
    Uses cache so identical text across frames is only translated once.
    """
    for det in detections:
        source_code = LANG_CODE_MAP.get(det.get("language", "eng"), "en")

        if source_code == target_lang:
            det["translated_text"] = det["text"]
            det["translation_status"] = "same_language"
        else:
            translated = translate_text(
                det["text"],
                source_lang=source_code,
                target_lang=target_lang,
            )
            if translated:
                det["translated_text"] = translated
                det["translation_status"] = "success"
            else:
                det["translated_text"] = det["text"]
                det["translation_status"] = "failed"

    return detections
