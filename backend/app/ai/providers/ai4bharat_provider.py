import logging
import time
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.telemetry import telemetry
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

logger = logging.getLogger("medikiosk.ai.ai4bharat")

class AI4BharatProvider(BaseAIProvider):
    """
    Provider for AI4Bharat Indian language models (IndicTrans2, IndicTTS, IndicASR).
    Features interactive short timeout (1.5s), translation caching, and Circuit Breaker.
    """
    _translation_cache: Dict[str, str] = {}

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 1.5
    ):
        super().__init__(provider_name="AI4Bharat")
        self.api_key = api_key if api_key is not None else settings.AI4BHARAT_API_KEY
        self.base_url = base_url or settings.AI4BHARAT_BASE_URL
        self.timeout = timeout
        self._failure_count: int = 0
        self._circuit_open_until: float = 0.0

    def is_circuit_open(self) -> bool:
        return time.time() < self._circuit_open_until

    def _record_success(self):
        self._failure_count = 0
        self._circuit_open_until = 0.0

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= 2:
            self._circuit_open_until = time.time() + 60.0
            logger.info("AI4Bharat circuit breaker opened for 60s (failing/unreachable)")

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

        if self.is_circuit_open():
            return [
                HealthReport(
                    provider_name=self.provider_name,
                    capability=cap,
                    status=ProviderStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    message="Circuit breaker open (Service failing, offline fallback active)"
                )
                for cap in capabilities
            ]

        status = ProviderStatus.UNAVAILABLE
        msg = "AI4Bharat service unavailable"
        latency = None

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(
                    f"{self.base_url}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                latency = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code in (200, 204):
                    status = ProviderStatus.AVAILABLE
                    msg = "AI4Bharat API operational"
                    self._record_success()
                else:
                    status = ProviderStatus.ERROR
                    msg = f"AI4Bharat returned HTTP {res.status_code}"
                    self._record_failure()
        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            msg = f"AI4Bharat unreachable: {type(e).__name__}"
            self._record_failure()

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
        Translates text via AI4Bharat IndicTrans2 with cache and circuit breaker.
        """
        if not text:
            return None

        clean_text = text.strip()
        cache_key = f"{source_lang}:{target_lang}:{clean_text.lower()}"
        if cache_key in self._translation_cache:
            return {
                "translated_text": self._translation_cache[cache_key],
                "source_lang": source_lang,
                "target_lang": target_lang,
                "provider": "AI4Bharat (Cached)"
            }

        if not self.is_configured() or self.is_circuit_open():
            return None

        try:
            with telemetry.measure("translation"):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        f"{self.base_url}/translate",
                        json={
                            "text": clean_text,
                            "source_language": source_lang,
                            "target_language": target_lang
                        },
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        translated = data.get("translated_text")
                        if translated:
                            self._record_success()
                            self._translation_cache[cache_key] = translated.strip()
                            return {
                                "translated_text": translated.strip(),
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                                "provider": self.provider_name
                            }
                    logger.warning("AI4Bharat translate returned HTTP %s", res.status_code)
                    self._record_failure()
        except Exception as e:
            logger.debug("AI4Bharat translation request note (fallback active): %s", type(e).__name__)
            self._record_failure()

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
        if not self.is_configured() or not text or self.is_circuit_open():
            return None

        try:
            with telemetry.measure("ai"):
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
                            self._record_success()
                            return {
                                "audio_base64": audio_b64,
                                "format": data.get("format", "wav"),
                                "language": language,
                                "provider": self.provider_name
                            }
                    self._record_failure()
        except Exception as e:
            logger.debug("AI4Bharat TTS note: %s", type(e).__name__)
            self._record_failure()

        return None
