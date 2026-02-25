"""
Preprocessing module for video frames.
Applies thresholding, denoising, and contrast enhancement
to improve OCR accuracy on low-resolution frames.
"""

import cv2
import numpy as np


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Apply adaptive thresholding for better text contrast."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )


def denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """Remove noise using Non-Local Means Denoising."""
    if len(image.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
    return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        enhanced = cv2.merge([l_channel, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image)


def preprocess_frame(image: np.ndarray, for_ocr: bool = True) -> np.ndarray:
    """
    Full preprocessing pipeline for a single frame.
    
    Args:
        image: Input BGR image (numpy array).
        for_ocr: If True, returns a binary image optimized for OCR.
                  If False, returns an enhanced color image.
    
    Returns:
        Preprocessed image as numpy array.
    """
    denoised = denoise(image)
    enhanced = enhance_contrast(denoised)

    if for_ocr:
        return adaptive_threshold(enhanced)

    return enhanced
