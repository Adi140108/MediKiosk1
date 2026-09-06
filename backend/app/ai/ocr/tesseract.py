import io
import os
import shutil
import logging
from typing import Tuple, List, Optional
from PIL import Image
import pytesseract
from app.core.config import settings
from app.ai.ocr.base import BaseOCREngine
from app.ai.ocr.preprocessing import generate_preprocessing_variants, evaluate_ocr_quality

logger = logging.getLogger("medikiosk.ocr.tesseract")

class TesseractOCREngine(BaseOCREngine):
    """
    Production-grade Tesseract OCR engine with multi-strategy image evaluation,
    auto-discovery of Windows/Linux binaries, and cloned/local tessdata pack integration.
    """
    def __init__(self, languages: str = "eng"):
        self.preferred_languages = languages
        self._configure_binary_and_tessdata()
        self.available_languages = self._detect_installed_languages()
        self.active_lang_string = self._build_lang_string()

    def _configure_binary_and_tessdata(self):
        """Auto-discovers Tesseract binary executable and local tessdata directory."""
        # 1. Binary discovery
        if settings.TESSERACT_CMD_PATH and os.path.exists(settings.TESSERACT_CMD_PATH):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD_PATH
            logger.info("Using configured Tesseract binary: %s", settings.TESSERACT_CMD_PATH)
        else:
            # Check standard Windows paths
            candidate_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
                os.path.abspath("./bin/tesseract.exe"),
                os.path.abspath("./tesseract/tesseract.exe"),
                shutil.which("tesseract")
            ]
            for cp in candidate_paths:
                if cp and os.path.exists(cp):
                    pytesseract.pytesseract.tesseract_cmd = cp
                    logger.info("Auto-discovered Tesseract binary at: %s", cp)
                    break

        # 2. Local / Cloned Tessdata directory discovery
        local_tessdata = os.path.abspath(settings.TESSDATA_PATH)
        if os.path.exists(local_tessdata) and any(f.endswith(".traineddata") for f in os.listdir(local_tessdata)):
            os.environ["TESSDATA_PREFIX"] = local_tessdata
            logger.info("Configured local TESSDATA_PREFIX: %s", local_tessdata)
        elif os.path.exists("./models/tessdata") and any(f.endswith(".traineddata") for f in os.listdir("./models/tessdata")):
            os.environ["TESSDATA_PREFIX"] = os.path.abspath("./models/tessdata")
            logger.info("Auto-discovered ./models/tessdata prefix: %s", os.environ["TESSDATA_PREFIX"])

    def _detect_installed_languages(self) -> List[str]:
        # 1. If local tessdata directory exists, check .traineddata files directly
        tessdata_dir = os.environ.get("TESSDATA_PREFIX") or settings.TESSDATA_PATH
        if os.path.exists(tessdata_dir) and os.path.isdir(tessdata_dir):
            files = os.listdir(tessdata_dir)
            langs = [f.replace(".traineddata", "") for f in files if f.endswith(".traineddata")]
            if langs:
                logger.info("Detected languages in local tessdata directory: %s", langs)
                return langs

        # 2. Query Tesseract binary if available
        try:
            installed = pytesseract.get_languages(config='')
            logger.info("Tesseract installed languages via binary: %s", installed)
            return installed
        except Exception as e:
            logger.debug("Tesseract binary not in path or tessdata uninitialized: %s", str(e))
            return ["eng"]

    def _build_lang_string(self) -> str:
        # Check which of eng, hin, kan, tam, tel, mal, mar, ben, guj, pan are present
        target_langs = ["eng", "hin", "kan", "tam", "tel", "mal", "mar", "ben", "guj", "pan"]
        matched = [l for l in target_langs if l in self.available_languages]
        return "+".join(matched) if matched else "eng"

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Runs multi-strategy OCR across image preprocessing variants.
        Selects the variant with the highest combined quality score.
        """
        variants = generate_preprocessing_variants(image_bytes)
        best_text = ""
        best_conf = 0.0
        best_quality = -1.0

        for variant_name, img in variants:
            try:
                data = pytesseract.image_to_data(
                    img,
                    lang=self.active_lang_string,
                    output_type=pytesseract.Output.DICT
                )
                
                confidences = [int(c) for c in data.get("conf", []) if int(c) >= 0]
                avg_conf = (sum(confidences) / len(confidences)) / 100.0 if confidences else 0.0
                
                text = pytesseract.image_to_string(img, lang=self.active_lang_string).strip()
                quality = evaluate_ocr_quality(text, avg_conf)

                logger.debug("Variant '%s' -> conf: %.2f, quality: %.2f, len: %d", variant_name, avg_conf, quality, len(text))

                if quality > best_quality:
                    best_quality = quality
                    best_text = text
                    best_conf = avg_conf

            except Exception as err:
                logger.debug("Variant '%s' OCR failed: %s", variant_name, str(err))

        logger.info("Best OCR result selected (confidence: %.2f, length: %d)", best_conf, len(best_text))
        return best_text, round(best_conf, 2)
