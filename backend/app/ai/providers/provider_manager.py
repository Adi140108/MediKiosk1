import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings
from app.ai.providers.base import ProviderCapability, ProviderStatus, HealthReport
from app.ai.providers.ai4bharat_provider import AI4BharatProvider
from app.ai.providers.local_indic_provider import LocalIndicProvider
from app.ai.providers.gemma_provider import GemmaProvider
from app.ai.providers.browser_fallback import BrowserFallbackProvider

logger = logging.getLogger("medikiosk.ai.provider_manager")

class AIProviderManager:
    """
    Central AI and Speech Provider Orchestrator.
    Supports Local Offline Models (CTranslate2/Transformers), Cloud AI4Bharat API,
    Gemma 4 12B Ollama, and Browser APIs without inventing medical data.
    """
    def __init__(
        self,
        local_indic: Optional[LocalIndicProvider] = None,
        ai4bharat: Optional[AI4BharatProvider] = None,
        gemma: Optional[GemmaProvider] = None,
        browser: Optional[BrowserFallbackProvider] = None
    ):
        self.local_indic = local_indic or LocalIndicProvider()
        self.ai4bharat = ai4bharat or AI4BharatProvider()
        self.gemma = gemma or GemmaProvider()
        self.browser = browser or BrowserFallbackProvider()

    async def get_health_overview(self) -> Dict[str, Any]:
        """
        Gathers live health reports across local neural models, AI4Bharat API, Gemma, and browser speech.
        """
        reports: List[HealthReport] = []

        try:
            reports.extend(await self.local_indic.check_health())
        except Exception as e:
            logger.warning("Local Indic health check error: %s", str(e))
        
        try:
            reports.extend(await self.ai4bharat.check_health())
        except Exception as e:
            logger.warning("AI4Bharat API health check error: %s", str(e))

        try:
            reports.extend(await self.gemma.check_health())
        except Exception as e:
            logger.warning("Gemma health check error: %s", str(e))

        try:
            reports.extend(await self.browser.check_health())
        except Exception as e:
            logger.warning("Browser fallback health check error: %s", str(e))

        local_indic_stat = next((r.status.value for r in reports if r.provider_name == "Local AI4Bharat IndicTrans2"), "unavailable")
        ai4b_trans_stat = next((r.status.value for r in reports if r.provider_name == "AI4Bharat" and r.capability == ProviderCapability.TRANSLATION), "unavailable")

        # Composite translation status (local model takes precedence if available)
        effective_trans_stat = local_indic_stat if local_indic_stat == "available" else ai4b_trans_stat

        return {
            "providers": [r.model_dump() for r in reports],
            "mode": settings.AI4BHARAT_MODE,
            "local_indictrans2": local_indic_stat,
            "gemma_status": (
                next((r.status.value for r in reports if r.provider_name.startswith("Gemma")), "unavailable")
            ),
            "ai4bharat_translation": effective_trans_stat,
            "ai4bharat_tts": (
                next((r.status.value for r in reports if r.provider_name == "AI4Bharat" and r.capability == ProviderCapability.TEXT_TO_SPEECH), "unavailable")
            ),
            "ai4bharat_asr": (
                next((r.status.value for r in reports if r.provider_name == "AI4Bharat" and r.capability == ProviderCapability.SPEECH_TO_TEXT), "unavailable")
            )
        }

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Translates text with provenance tracking.
        Hierarchy:
        1. Local IndicTrans2 (if local weights present & mode is 'local' or 'auto')
        2. AI4Bharat Cloud API (if mode is 'api' or 'auto')
        3. Local Gemma 4 12B (Ollama)
        4. Original text with translation_status='unavailable' (Zero Hallucination)
        """
        if not text or source_lang == target_lang:
            return {
                "original_text": text,
                "original_language": source_lang,
                "normalized_text": text,
                "normalized_language": target_lang,
                "translation_provider": "None (identical language)",
                "translation_status": "verified"
            }

        mode = settings.AI4BHARAT_MODE.lower()

        # 1. Attempt Local IndicTrans2
        if mode in ("local", "auto"):
            local_res = await self.local_indic.translate(text, target_lang=target_lang, source_lang=source_lang)
            if local_res and local_res.get("translated_text"):
                return {
                    "original_text": text,
                    "original_language": source_lang,
                    "normalized_text": local_res["translated_text"].strip(),
                    "normalized_language": target_lang,
                    "translation_provider": "Local AI4Bharat IndicTrans2",
                    "translation_status": "verified"
                }

        # 2. Attempt AI4Bharat Cloud API
        if mode in ("api", "auto"):
            ai4b_res = await self.ai4bharat.translate(text, target_lang=target_lang, source_lang=source_lang)
            if ai4b_res and ai4b_res.get("translated_text"):
                return {
                    "original_text": text,
                    "original_language": source_lang,
                    "normalized_text": ai4b_res["translated_text"].strip(),
                    "normalized_language": target_lang,
                    "translation_provider": "AI4Bharat Cloud API",
                    "translation_status": "verified"
                }

        # 3. Attempt Gemma 4 12B translation
        prompt = (
            f"You are a medical translator. Translate the following text from {source_lang} to {target_lang}. "
            f"Preserve medication names, numeric dosages, and clinical terms accurately without embellishment:\n\n{text}"
        )
        gemma_res = await self.gemma.generate_text(prompt)
        if gemma_res and gemma_res.strip():
            return {
                "original_text": text,
                "original_language": source_lang,
                "normalized_text": gemma_res.strip(),
                "normalized_language": target_lang,
                "translation_provider": "Gemma 4 12B (Ollama)",
                "translation_status": "verified"
            }

        # 4. Fallback: Keep original text without faking translation
        return {
            "original_text": text,
            "original_language": source_lang,
            "normalized_text": text,
            "normalized_language": source_lang,
            "translation_provider": "None",
            "translation_status": "unavailable"
        }

    async def extract_structured_facts_from_ocr(self, raw_text: str) -> Dict[str, Any]:
        """
        Structures extracted OCR text using Gemma or deterministic regex without inventing facts.
        """
        if not raw_text or not raw_text.strip():
            return {
                "raw_text": "",
                "conditions": [],
                "medications": [],
                "allergies": [],
                "vitals": {},
                "lab_values": [],
                "confidence": 0.0,
                "extraction_method": "empty"
            }

        prompt = (
            "You are a clinical document parser. Extract ONLY facts explicitly present in this OCR text. "
            "Do NOT invent or infer facts. If not mentioned, leave the list empty.\n\n"
            "Return JSON matching:\n"
            "{\n"
            "  \"conditions\": [string],\n"
            "  \"medications\": [{\"name\": string, \"dosage\": string, \"frequency\": string}],\n"
            "  \"allergies\": [string],\n"
            "  \"vitals\": {\"bp\": string, \"pulse\": string, \"spo2\": string, \"temp\": string},\n"
            "  \"lab_values\": [{\"test\": string, \"value\": string, \"unit\": string, \"is_abnormal\": bool}]\n"
            "}\n\n"
            f"OCR TEXT:\n{raw_text}"
        )

        gemma_res = await self.gemma.generate_text(prompt, format_json=True)
        if gemma_res:
            try:
                data = json.loads(gemma_res)
                data["raw_text"] = raw_text
                data["extraction_method"] = "gemma_ai"
                return data
            except Exception:
                pass

        # Deterministic regex extraction (safe baseline)
        return self._regex_extract_facts(raw_text)

    def _regex_extract_facts(self, text: str) -> Dict[str, Any]:
        vitals = {}
        bp_match = re.search(r'\b(BP|Blood Pressure)[:\s]*([0-9]{2,3}/[0-9]{2,3})\b', text, re.IGNORECASE)
        if bp_match:
            vitals["bp"] = bp_match.group(2)
        pulse_match = re.search(r'\b(HR|Pulse|Heart Rate)[:\s]*([0-9]{2,3})\b', text, re.IGNORECASE)
        if pulse_match:
            vitals["pulse"] = pulse_match.group(2)

        return {
            "raw_text": text,
            "conditions": [],
            "medications": [],
            "allergies": [],
            "vitals": vitals,
            "lab_values": [],
            "confidence": 0.5,
            "extraction_method": "deterministic_rule"
        }
