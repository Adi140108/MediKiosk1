import logging
import base64
import json
import httpx
from typing import Tuple, Dict, Any, Optional
from app.ai.ocr.base import BaseOCREngine
from app.core.config import settings

logger = logging.getLogger("medikiosk.ocr.gemma_fallback")

class GemmaVisionFallbackOCR(BaseOCREngine):
    """
    Vision OCR fallback using multimodal vision models.
    Sends real image bytes to Ollama vision API when available.
    Never fabricates clinical text when vision service is offline.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.GEMMA_MODEL

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Synchronous wrapper calling the vision model.
        """
        if not image_bytes:
            return "", 0.0

        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": self.model,
                "prompt": "You are a medical OCR vision engine. Transcribe all text visibly present in this image accurately without adding commentary.",
                "images": [b64_image],
                "stream": False
            }

            with httpx.Client(timeout=10.0) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    extracted = data.get("response", "").strip()
                    if extracted:
                        return extracted, 0.85
        except Exception as e:
            logger.info("Vision model unavailable for OCR: %s", str(e))

        # Honest empty return when vision model is offline
        return "", 0.0
