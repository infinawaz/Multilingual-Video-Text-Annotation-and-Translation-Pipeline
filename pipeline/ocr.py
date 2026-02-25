"""
OCR module for text detection and recognition.
Uses Tesseract OCR with multi-language support
(English, Hindi, Bengali, Tamil).
"""

import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Any

from .preprocess import preprocess_frame


# Tesseract language codes
LANGUAGE_MAP = {
    "english": "eng",
    "hindi": "hin",
    "bengali": "ben",
    "tamil": "tam",
}

# Combined lang string for Tesseract (detect all supported languages)
ALL_LANGS = "+".join(LANGUAGE_MAP.values())


def detect_text_regions(image: np.ndarray, languages: str = ALL_LANGS) -> List[Dict[str, Any]]:
    """
    Detect and recognize text regions in a frame using Tesseract.
    
    Args:
        image: Input BGR image (numpy array).
        languages: Tesseract language string (e.g., 'eng+hin+ben+tam').
    
    Returns:
        List of dicts with keys:
          - 'text': recognized text string
          - 'bbox': [x, y, width, height]
          - 'confidence': OCR confidence (0-100)
          - 'language': detected language code
    """
    # Preprocess for better OCR
    preprocessed = preprocess_frame(image, for_ocr=True)
    
    # Run Tesseract with detailed output
    data = pytesseract.image_to_data(
        preprocessed, lang=languages, output_type=pytesseract.Output.DICT
    )
    
    results = []
    n_boxes = len(data["text"])
    
    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        
        # Filter out empty strings and low-confidence detections
        if text and conf > 30:
            results.append({
                "text": text,
                "bbox": [
                    int(data["left"][i]),
                    int(data["top"][i]),
                    int(data["width"][i]),
                    int(data["height"][i]),
                ],
                "confidence": conf,
                "block_num": int(data["block_num"][i]),
                "line_num": int(data["line_num"][i]),
            })
    
    return results


def detect_language(text: str) -> str:
    """
    Simple heuristic language detection based on Unicode ranges.
    
    Returns:
        Language code: 'eng', 'hin', 'ben', or 'tam'
    """
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    bengali = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    tamil = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    
    counts = {
        "hin": devanagari,
        "ben": bengali,
        "tam": tamil,
        "eng": latin,
    }
    
    detected = max(counts, key=counts.get)
    return detected if counts[detected] > 0 else "eng"


def group_text_by_lines(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group individual word detections into logical text lines.
    
    Returns:
        List of dicts with merged text and bounding boxes per line.
    """
    if not detections:
        return []
    
    lines = {}
    for det in detections:
        key = (det.get("block_num", 0), det.get("line_num", 0))
        if key not in lines:
            lines[key] = {
                "texts": [],
                "bboxes": [],
                "confidences": [],
            }
        lines[key]["texts"].append(det["text"])
        lines[key]["bboxes"].append(det["bbox"])
        lines[key]["confidences"].append(det["confidence"])
    
    grouped = []
    for key, line_data in sorted(lines.items()):
        # Merge bounding boxes
        all_bboxes = line_data["bboxes"]
        x_min = min(b[0] for b in all_bboxes)
        y_min = min(b[1] for b in all_bboxes)
        x_max = max(b[0] + b[2] for b in all_bboxes)
        y_max = max(b[1] + b[3] for b in all_bboxes)
        
        full_text = " ".join(line_data["texts"])
        avg_conf = sum(line_data["confidences"]) / len(line_data["confidences"])
        
        grouped.append({
            "text": full_text,
            "bbox": [x_min, y_min, x_max - x_min, y_max - y_min],
            "confidence": round(avg_conf, 1),
            "language": detect_language(full_text),
        })
    
    return grouped


def extract_text_from_frame(image: np.ndarray) -> List[Dict[str, Any]]:
    """
    Full OCR pipeline for a single frame.
    Detects text, groups into lines, detects language.
    
    Args:
        image: Input BGR image.
    
    Returns:
        List of text region dicts with text, bbox, confidence, language.
    """
    detections = detect_text_regions(image)
    return group_text_by_lines(detections)
