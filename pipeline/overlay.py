"""
Overlay module for drawing bounding boxes and translated text
annotations onto original video frames.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple


# Color palette for different languages
LANG_COLORS = {
    "eng": (0, 200, 100),    # Green
    "hin": (255, 150, 0),    # Orange
    "ben": (100, 100, 255),  # Blue
    "tam": (200, 50, 200),   # Purple
}

DEFAULT_COLOR = (0, 200, 200)  # Yellow-ish


def draw_bounding_boxes(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw bounding boxes around detected text regions.
    
    Args:
        image: Input BGR image.
        detections: List of detection dicts with 'bbox' and 'language'.
        thickness: Line thickness for bounding boxes.
    
    Returns:
        Annotated image with bounding boxes.
    """
    annotated = image.copy()
    
    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        
        # Draw rectangle
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
    
    return annotated


def draw_text_annotations(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    show_original: bool = True,
    show_translated: bool = True,
    font_scale: float = 0.5,
) -> np.ndarray:
    """
    Draw text annotations (original + translated) near bounding boxes.
    
    Args:
        image: Input BGR image.
        detections: List of detection dicts.
        show_original: Whether to show original detected text.
        show_translated: Whether to show translated text.
        font_scale: Font scale for text rendering.
    
    Returns:
        Annotated image with text labels.
    """
    annotated = image.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    for det in detections:
        x, y, w, h = det["bbox"]
        lang = det.get("language", "eng")
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        
        label_y = y - 5
        
        if show_translated and "translated_text" in det:
            translated = det["translated_text"]
            # Draw background for readability
            (tw, th), _ = cv2.getTextSize(translated, font, font_scale, 1)
            cv2.rectangle(
                annotated,
                (x, label_y - th - 4),
                (x + tw + 4, label_y + 2),
                (0, 0, 0),
                -1,
            )
            cv2.putText(
                annotated, translated, (x + 2, label_y),
                font, font_scale, (255, 255, 255), 1, cv2.LINE_AA,
            )
            label_y -= th + 8
        
        if show_original:
            original = det.get("text", "")
            (tw, th), _ = cv2.getTextSize(original, font, font_scale * 0.8, 1)
            cv2.rectangle(
                annotated,
                (x, label_y - th - 4),
                (x + tw + 4, label_y + 2),
                color,
                -1,
            )
            cv2.putText(
                annotated, original, (x + 2, label_y),
                font, font_scale * 0.8, (0, 0, 0), 1, cv2.LINE_AA,
            )
    
    return annotated


def create_annotated_frame(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
) -> np.ndarray:
    """
    Full overlay pipeline: bounding boxes + text annotations.
    
    Args:
        image: Original BGR frame.
        detections: List of detection dicts with translations.
    
    Returns:
        Fully annotated frame.
    """
    annotated = draw_bounding_boxes(image, detections)
    annotated = draw_text_annotations(annotated, detections)
    return annotated
