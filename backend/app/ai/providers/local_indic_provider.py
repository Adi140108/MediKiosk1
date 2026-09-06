import os
import time
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

logger = logging.getLogger("medikiosk.ai.local_indic")

# IndicTrans2 BCP-47 / Flores script language tag mapping
INDICTRANS2_LANG_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ml": "mal_Mlym",
    "mr": "mar_Deva",
    "bn": "ben_Beng",
    "gu": "guj_Gujr",
    "pa": "pan_Guru"
}

class LocalIndicProvider(BaseAIProvider):
    """
    Self-Hosted, 100% Offline AI4Bharat IndicTrans2 Neural Translation Provider.
    Supports CTranslate2 (Quantized int8/float16) and Hugging Face Transformers.
    """
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ):
        super().__init__(provider_name="Local AI4Bharat IndicTrans2")
        self.model_path = model_path or settings.LOCAL_INDICTRANS_PATH
        self.configured_device = device or settings.LOCAL_INDIC_DEVICE
        self.configured_compute = compute_type or settings.LOCAL_INDIC_COMPUTE_TYPE
        self._translator = None
        self._tokenizer = None
        self._engine_type = None  # "ctranslate2" or "transformers"
        self._load_attempted = False

    def supports_capability(self, capability: ProviderCapability) -> bool:
        return capability == ProviderCapability.TRANSLATION

    def is_model_present(self) -> bool:
        """Checks if local model weights directory exists and contains model artifacts."""
        if not os.path.exists(self.model_path):
            return False
        
        # Check for CTranslate2 artifacts or Hugging Face checkpoints
        files = os.listdir(self.model_path) if os.path.isdir(self.model_path) else []
        has_ct2 = any("model.bin" in f for f in files)
        has_hf = any(f.endswith(".safetensors") or f.endswith(".bin") for f in files)
        return has_ct2 or has_hf

    def _determine_device_and_compute(self):
        device = "cpu"
        compute_type = "int8"
        try:
            import torch
            if torch.cuda.is_available() and self.configured_device != "cpu":
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass

        if self.configured_device in ("cuda", "cpu"):
            device = self.configured_device
        if self.configured_compute in ("int8", "float16", "float32"):
            compute_type = self.configured_compute

        return device, compute_type

    def load_model(self) -> bool:
        """Lazy loader for local neural weights."""
        if self._translator is not None:
            return True
        if self._load_attempted:
            return False

        self._load_attempted = True
        if not self.is_model_present():
            logger.info("Local IndicTrans2 weights not detected at path: %s", self.model_path)
            return False

        device, compute_type = self._determine_device_and_compute()

        # 1. Try CTranslate2 (Fastest, low VRAM)
        try:
            import ctranslate2
            import sentencepiece as spm

            logger.info("Loading CTranslate2 IndicTrans2 from %s (device: %s, compute: %s)...", self.model_path, device, compute_type)
            self._translator = ctranslate2.Translator(
                self.model_path,
                device=device,
                compute_type=compute_type
            )
            sp_model_path = os.path.join(self.model_path, "spm.model")
            if os.path.exists(sp_model_path):
                self._tokenizer = spm.SentencePieceProcessor(model_file=sp_model_path)
            self._engine_type = "ctranslate2"
            logger.info("Successfully loaded CTranslate2 IndicTrans2.")
            return True
        except ImportError:
            logger.debug("ctranslate2 not installed, attempting transformers...")
        except Exception as e:
            logger.warning("Error loading CTranslate2 model: %s", str(e))

        # 2. Try Hugging Face Transformers
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            import torch

            logger.info("Loading Transformers IndicTrans2 from %s...", self.model_path)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self._translator = AutoModelForSeq2SeqLM.from_pretrained(self.model_path, trust_remote_code=True).to(device)
            self._engine_type = "transformers"
            logger.info("Successfully loaded Transformers IndicTrans2.")
            return True
        except ImportError:
            logger.info("Neither ctranslate2 nor transformers available for local IndicTrans2.")
        except Exception as e:
            logger.warning("Error loading Transformers IndicTrans2: %s", str(e))

        return False

    async def check_health(self, capability: Optional[ProviderCapability] = None) -> List[HealthReport]:
        start = time.perf_counter()
        present = self.is_model_present()
        device, compute = self._determine_device_and_compute()

        if present:
            status = ProviderStatus.AVAILABLE
            msg = f"Offline IndicTrans2 model present at {self.model_path} ({device.upper()} / {compute})"
        else:
            status = ProviderStatus.UNAVAILABLE
            msg = f"Local weights not found at {self.model_path}. (Run scripts/download_indictrans2.py to download)"

        latency = round((time.perf_counter() - start) * 1000, 2)
        return [
            HealthReport(
                provider_name=self.provider_name,
                capability=ProviderCapability.TRANSLATION,
                status=status,
                latency_ms=latency,
                message=msg
            )
        ]

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Performs local high-speed translation.
        Returns None if model is unavailable so the pipeline can gracefully fall back.
        """
        if not text or not text.strip():
            return {"translated_text": text}

        if not self.load_model():
            return None

        src_tag = INDICTRANS2_LANG_MAP.get(source_lang, "eng_Latn")
        tgt_tag = INDICTRANS2_LANG_MAP.get(target_lang, "hin_Deva")

        try:
            if self._engine_type == "ctranslate2":
                # Tokenize -> Translate -> Detokenize
                if self._tokenizer:
                    tokens = self._tokenizer.encode(f"{src_tag} {tgt_tag} {text}", out_type=str)
                else:
                    tokens = text.split()

                results = self._translator.translate_batch([tokens])
                output_tokens = results[0].hypotheses[0]
                
                if self._tokenizer:
                    translated = self._tokenizer.decode(output_tokens)
                else:
                    translated = " ".join(output_tokens)

                # Strip language prefix if present
                translated = translated.replace(tgt_tag, "").strip()
                return {"translated_text": translated, "engine": "local_ctranslate2"}

            elif self._engine_type == "transformers":
                import torch
                device = next(self._translator.parameters()).device
                inputs = self._tokenizer(text, return_tensors="pt").to(device)
                with torch.no_grad():
                    outputs = self._translator.generate(**inputs)
                translated = self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                return {"translated_text": translated, "engine": "local_transformers"}

        except Exception as e:
            logger.warning("Local IndicTrans2 translation failed: %s", str(e))

        return None
