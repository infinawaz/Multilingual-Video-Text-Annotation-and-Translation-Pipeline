"""
Overlay module for drawing bounding boxes and translated text
annotations onto original video frames using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple


# Color palette for different languages (RGB)
LANG_COLORS = {
    "eng": (0, 200, 100),    # Green
    "hin": (255, 150, 0),    # Orange
    "ben": (100, 100, 255),  # Blue
    "tam": (200, 50, 200),   # Purple
}

DEFAULT_COLOR = (0, 200, 200)  # Yellow-ish


def draw_bounding_boxes(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    thickness: int = 2,
) -> Image.Image:
    """
    Draw bounding boxes around detected text regions.
    """
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    
    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        
        # Draw rectangle
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
    """
    Draw text annotations (original + translated) near bounding boxes.
    """
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    
    # Try to load a default font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except (IOError, OSError):
        font = ImageFont.load_default()
        font_small = font
    
    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        
        label_y = y - 18
        
        if show_translated and "translated_text" in det:
            translated = det["translated_text"]
            # Draw background for readability
            bbox = draw.textbbox((x, label_y), translated, font=font)
            draw.rectangle(
                [bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2],
                fill=(0, 0, 0),
            )
            draw.text((x, label_y), translated, fill=(255, 255, 255), font=font)
            label_y -= 20
        
        if show_original:
            original = det.get("text", "")
            bbox = draw.textbbox((x, label_y), original, font=font_small)
            draw.rectangle(
                [bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2],
                fill=color,
            )
            draw.text((x, label_y), original, fill=(0, 0, 0), font=font_small)
    
    return annotated


def create_annotated_frame(
    image: Image.Image,
    detections: List[Dict[str, Any]],
) -> Image.Image:
    """
    Full overlay pipeline: bounding boxes + text annotations.
    """
    annotated = draw_bounding_boxes(image, detections)
    annotated = draw_text_annotations(annotated, detections)
    return annotated
