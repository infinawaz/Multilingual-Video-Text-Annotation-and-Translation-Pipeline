"""
Preprocessing module for video frames.
Uses Pillow for lightweight image processing.
Applies contrast enhancement and basic sharpening
to improve OCR accuracy on low-resolution frames.
"""

from PIL import Image, ImageFilter, ImageEnhance


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Enhance contrast using Pillow's ImageEnhance."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def sharpen(image: Image.Image) -> Image.Image:
    """Sharpen image to improve text clarity."""
    return image.filter(ImageFilter.SHARPEN)


def denoise(image: Image.Image) -> Image.Image:
    """Simple denoising using median filter."""
    return image.filter(ImageFilter.MedianFilter(size=3))


def to_grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale."""
    return image.convert("L")


def preprocess_frame(image: Image.Image, for_ocr: bool = True) -> Image.Image:
    """
    Full preprocessing pipeline for a single frame.

    Args:
        image: Input PIL Image.
        for_ocr: If True, returns a grayscale image optimized for OCR.
                  If False, returns an enhanced color image.

    Returns:
        Preprocessed PIL Image.
    """
    enhanced = enhance_contrast(image)
    sharpened = sharpen(enhanced)

    if for_ocr:
        return to_grayscale(sharpened)

    return sharpened
