import io
import logging
import re
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger("medikiosk.ocr.preprocessing")

def preprocess_image_for_ocr(image_bytes: bytes) -> Image.Image:
    """
    Standard preprocessing for single-pass OCR:
    converts to grayscale and enhances contrast.
    """
    base_img = Image.open(io.BytesIO(image_bytes))
    gray = base_img.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    contrast = enhancer.enhance(2.0)
    return contrast

def generate_preprocessing_variants(image_bytes: bytes) -> List[Tuple[str, Image.Image]]:
    """
    Generates multiple image preprocessing variants for multi-strategy OCR:
    1. original
    2. grayscale
    3. contrast_enhanced
    4. sharpened
    5. adaptive_threshold (autocontrast + binary thresholding)
    6. denoised (median filter)
    """
    variants = []
    try:
        base_img = Image.open(io.BytesIO(image_bytes))
        
        # 1. Original
        variants.append(("original", base_img.convert("RGB")))

        # 2. Grayscale
        gray = base_img.convert("L")
        variants.append(("grayscale", gray))

        # 3. Contrast Enhanced
        enhancer = ImageEnhance.Contrast(gray)
        contrast = enhancer.enhance(2.0)
        variants.append(("contrast_enhanced", contrast))

        # 4. Sharpened
        sharpened = contrast.filter(ImageFilter.SHARPEN)
        variants.append(("sharpened", sharpened))

        # 5. Adaptive Threshold / AutoContrast
        auto_c = ImageOps.autocontrast(gray, cutoff=2)
        # Binarize
        fn = lambda x : 255 if x > 140 else 0
        binarized = auto_c.point(fn, mode='1')
        variants.append(("adaptive_threshold", binarized))

        # 6. Denoised
        denoised = gray.filter(ImageFilter.MedianFilter(size=3))
        variants.append(("denoised", denoised))

    except Exception as e:
        logger.warning("Error generating preprocessing variants: %s", str(e))
        try:
            fallback_img = Image.open(io.BytesIO(image_bytes))
            variants.append(("original", fallback_img))
        except Exception:
            pass

    return variants

def evaluate_ocr_quality(text: str, avg_confidence: float) -> float:
    """
    Evaluates OCR output quality based on:
    - Word count & character count
    - OCR token confidence
    - Malformed token ratio
    - Character-to-word density
    Returns a normalized quality score between 0.0 and 1.0.
    """
    if not text or not text.strip():
        return 0.0

    words = text.strip().split()
    total_words = len(words)
    total_chars = len(text.strip())

    if total_words == 0:
        return 0.0

    # Count alphanumeric / recognizable tokens
    valid_tokens = [w for w in words if re.search(r'[a-zA-Z0-9]', w)]
    valid_ratio = len(valid_tokens) / total_words

    # Check for excessive unreadable symbols
    malformed_symbols = re.findall(r'[^\w\s\.,;:/\-–%()#\n\r]', text)
    malformed_ratio = len(malformed_symbols) / max(1, total_chars)

    # Word length reasonableness (average English/medical word length ~ 4-10)
    avg_word_len = total_chars / total_words
    len_penalty = 1.0
    if avg_word_len > 25 or avg_word_len < 2:
        len_penalty = 0.5

    # Composite score
    conf_factor = max(0.0, min(1.0, avg_confidence / 100.0 if avg_confidence > 1.0 else avg_confidence))
    quality_score = (
        (conf_factor * 0.4) +
        (valid_ratio * 0.4) +
        ((1.0 - min(1.0, malformed_ratio * 5)) * 0.2)
    ) * len_penalty

    return round(max(0.0, min(1.0, quality_score)), 3)
