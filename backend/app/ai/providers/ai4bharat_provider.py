import logging
import time
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

logger = logging.getLogger("medikiosk.ai.ai4bharat")

class AI4BharatProvider(BaseAIProvider):
    """
    Provider for AI4Bharat Indian language models (IndicTrans2, IndicTTS, IndicASR).
    Provides robust validation, capability-level degradation, and health checks.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 6.0
    ):
        super().__init__(provider_name="AI4Bharat")
        self.api_key = api_key if api_key is not None else settings.AI4BHARAT_API_KEY
        self.base_url = base_url or settings.AI4BHARAT_BASE_URL
        self.timeout = timeout

    def supports_capability(self, capability: ProviderCapability) -> bool:
        return capability in (
            ProviderCapability.TRANSLATION,
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH
        )

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def check_health(self, capability: Optional[ProviderCapability] = None) -> List[HealthReport]:
        start = time.perf_counter()
        capabilities = [capability] if capability else [
            ProviderCapability.TRANSLATION,
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH
        ]

        if not self.is_configured():
            return [
                HealthReport(
                    provider_name=self.provider_name,
                    capability=cap,
                    status=ProviderStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    message="AI4Bharat API key not configured (Development fallback active)"
                )
                for cap in capabilities
            ]

        status = ProviderStatus.UNAVAILABLE
        msg = "AI4Bharat service unavailable"
        latency = None

        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                res = await client.get(
                    f"{self.base_url}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                latency = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code in (200, 204):
                    status = ProviderStatus.AVAILABLE
                    msg = "AI4Bharat API operational"
                else:
                    status = ProviderStatus.ERROR
                    msg = f"AI4Bharat returned HTTP {res.status_code}"
        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            msg = f"AI4Bharat ping unreachable: {type(e).__name__}"

        return [
            HealthReport(
                provider_name=self.provider_name,
                capability=cap,
                status=status,
                latency_ms=latency,
                message=msg
            )
            for cap in capabilities
        ]

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Translates text via AI4Bharat IndicTrans2.
        Returns dict with translated_text and metadata, or None if failed.
        """
        if not self.is_configured() or not text:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/translate",
                    json={
                        "text": text,
                        "source_language": source_lang,
                        "target_language": target_lang
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    translated = data.get("translated_text")
                    if translated:
                        return {
                            "translated_text": translated,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "provider": self.provider_name
                        }
                logger.warning("AI4Bharat translate returned HTTP %s", res.status_code)
        except Exception as e:
            logger.warning("AI4Bharat translation request error: %s", type(e).__name__)

        return None

    async def synthesize_speech(
        self,
        text: str,
        language: str,
        gender: str = "female"
    ) -> Optional[Dict[str, Any]]:
        """
        Generates TTS audio via AI4Bharat IndicTTS.
        """
        if not self.is_configured() or not text:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    f"{self.base_url}/tts",
                    json={
                        "text": text,
                        "language": language,
                        "gender": gender
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    audio_b64 = data.get("audio_base64")
                    if audio_b64:
                        return {
                            "audio_base64": audio_b64,
                            "language": language,
                            "provider": self.provider_name
                        }
        except Exception as e:
            logger.warning("AI4Bharat TTS request error: %s", type(e).__name__)

        return None

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribes speech audio via AI4Bharat IndicASR.
        """
        if not self.is_configured() or not audio_bytes:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
                res = await client.post(
                    f"{self.base_url}/asr",
                    files=files,
                    data={"language": language},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    transcript = data.get("transcript")
                    if transcript:
                        return {
                            "transcript": transcript,
                            "language": language,
                            "provider": self.provider_name
                        }
        except Exception as e:
            logger.warning("AI4Bharat ASR request error: %s", type(e).__name__)

        return None
