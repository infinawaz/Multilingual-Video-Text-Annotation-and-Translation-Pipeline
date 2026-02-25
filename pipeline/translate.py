"""
Translation module using LibreTranslate API.
Translates detected text between languages with graceful fallback.
"""

import os
import logging
import requests
from typing import Optional

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

REVERSE_LANG_MAP = {v: k for k, v in LANG_CODE_MAP.items()}


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
    timeout: int = 10,
) -> Optional[str]:
    """
    Translate text using LibreTranslate API.
    
    Args:
        text: Text to translate.
        source_lang: Source language code (LibreTranslate format, e.g., 'hi').
                     Use 'auto' for auto-detection.
        target_lang: Target language code (e.g., 'en').
        timeout: Request timeout in seconds.
    
    Returns:
        Translated text string, or None if translation fails.
    """
    if not text or not text.strip():
        return text
    
    # If source == target, no translation needed
    if source_lang == target_lang:
        return text
    
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
            return result.get("translatedText", text)
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
    
    Args:
        detections: List of detection dicts with 'text' and 'language' keys.
        target_lang: Target language code (e.g., 'en').
    
    Returns:
        Updated detections list with 'translated_text' field added.
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
