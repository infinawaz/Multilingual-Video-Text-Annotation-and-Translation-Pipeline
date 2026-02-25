"""
Overlay module for drawing bounding boxes and translated text
annotations onto original video frames using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any


# Color palette for different languages (RGB)
LANG_COLORS = {
    "eng": (0, 200, 100),    # Green
    "hin": (255, 150, 0),    # Orange
    "ben": (100, 100, 255),  # Blue
    "tam": (200, 50, 200),   # Purple
}

DEFAULT_COLOR = (0, 200, 200)  # Yellow-ish

# Cache the font objects so we don't re-load them per frame
_font_cache = {}


def _get_fonts():
    """Load and cache fonts for text rendering."""
    if "font" not in _font_cache:
        try:
            _font_cache["font"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
            )
            _font_cache["font_small"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
            )
        except (IOError, OSError):
            _font_cache["font"] = ImageFont.load_default()
            _font_cache["font_small"] = _font_cache["font"]
    return _font_cache["font"], _font_cache["font_small"]


def draw_bounding_boxes(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    thickness: int = 2,
) -> Image.Image:
    """Draw bounding boxes around detected text regions."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)

        for i in range(thickness):
            draw.rectangle(
                [x - i, y - i, x + w + i, y + h + i],
                outline=color,
            )

    return annotated


def draw_text_annotations(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    show_original: bool = True,
    show_translated: bool = True,
) -> Image.Image:
    """Draw text annotations (original + translated) near bounding boxes."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    font, font_small = _get_fonts()

    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)

        # Position label above the bounding box, clamped to image bounds
        label_y = max(0, y - 18)

        if show_translated and "translated_text" in det:
            translated = det["translated_text"]
            if translated:
                bbox = draw.textbbox((x, label_y), translated, font=font)
                draw.rectangle(
                    [bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2],
                    fill=(0, 0, 0),
                )
                draw.text(
                    (x, label_y), translated,
                    fill=(255, 255, 255), font=font,
                )
                label_y = max(0, label_y - 20)

        if show_original:
            original = det.get("text", "")
            if original:
                bbox = draw.textbbox((x, label_y), original, font=font_small)
                draw.rectangle(
                    [bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2],
                    fill=color,
                )
                draw.text(
                    (x, label_y), original,
                    fill=(0, 0, 0), font=font_small,
                )

    return annotated


def create_annotated_frame(
    image: Image.Image,
    detections: List[Dict[str, Any]],
) -> Image.Image:
    """Full overlay pipeline: bounding boxes + text annotations."""
    if not detections:
        return image.copy()
    annotated = draw_bounding_boxes(image, detections)
    annotated = draw_text_annotations(annotated, detections)
    return annotated
