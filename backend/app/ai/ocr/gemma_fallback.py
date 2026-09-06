import logging
import base64
import json
import httpx
from typing import Tuple, Dict, Any, Optional, List
from app.ai.ocr.base import BaseOCREngine
from app.core.config import settings

logger = logging.getLogger("medikiosk.ocr.gemma_fallback")

class GemmaVisionFallbackOCR(BaseOCREngine):
    """
    Vision OCR fallback using multimodal vision models.
    Sends real image bytes to Ollama vision API when available.
    Supports auto-discovery of available multimodal models (gemma4, llava, moondream, llama3.2-vision).
    Never fabricates clinical text when vision service is offline.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip('/')
        self.model = model or settings.GEMMA_MODEL
        self._cached_vision_model: Optional[str] = None

    def _discover_vision_model(self, client: httpx.Client) -> str:
        if self._cached_vision_model:
            return self._cached_vision_model

        # Check installed models on Ollama
        try:
            res = client.get(f"{self.base_url}/api/tags", timeout=3.0)
            if res.status_code == 200:
                models = [m.get("name", "") for m in res.json().get("models", [])]
                # Prioritize configured model
                if self.model in models:
                    self._cached_vision_model = self.model
                    return self.model
                
                # Check for other vision-capable models
                vision_candidates = ["gemma4", "gemma", "llava", "moondream", "llama3.2-vision", "bakllava", "minicpm-v"]
                for vc in vision_candidates:
                    match = next((m for m in models if vc in m.lower()), None)
                    if match:
                        self._cached_vision_model = match
                        return match
                
                if models:
                    self._cached_vision_model = models[0]
                    return models[0]
        except Exception as e:
            logger.debug("Ollama vision discovery check: %s", str(e))

        self._cached_vision_model = self.model
        return self.model

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Synchronous wrapper calling the vision model.
        Transcribes all visible medical document text and tables.
        """
        if not image_bytes:
            return "", 0.0

        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            prompt = (
                "You are a medical OCR vision engine. Transcribe ALL text, patient info, laboratory test names, "
                "observed values, units, and reference ranges visibly present in this medical report or prescription image. "
                "Transcribe accurately line by line without adding commentary or conversational remarks."
            )

            with httpx.Client(timeout=15.0) as client:
                model_to_use = self._discover_vision_model(client)
                payload = {
                    "model": model_to_use,
                    "prompt": prompt,
                    "images": [b64_image],
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }

                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    extracted = data.get("response", "").strip()
                    if extracted:
                        logger.info("Gemma/Vision OCR successfully transcribed document (%d chars)", len(extracted))
                        return extracted, 0.88
        except Exception as e:
            logger.info("Vision model unavailable for OCR: %s", str(e))

        # Honest empty return when vision model is offline
        return "", 0.0
