import logging
import time
import json
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.telemetry import telemetry
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

logger = logging.getLogger("medikiosk.ai.gemma_provider")

class GemmaProvider(BaseAIProvider):
    """
    Provider for local/hosted Gemma 4 12B via Ollama.
    Features short timeout (1.0s) and Circuit Breaker to prevent Vercel stalls.
    Never fabricates clinical answers when offline.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 1.0
    ):
        super().__init__(provider_name="Gemma 4 12B (Ollama)")
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.GEMMA_MODEL
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
            # Trip circuit breaker for 60 seconds
            self._circuit_open_until = time.time() + 60.0
            logger.info("Gemma Ollama circuit breaker opened for 60s (unreachable)")

    def supports_capability(self, capability: ProviderCapability) -> bool:
        return capability in (
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.TRANSLATION,
            ProviderCapability.STRUCTURED_EXTRACTION
        )

    async def check_health(self, capability: Optional[ProviderCapability] = None) -> List[HealthReport]:
        start = time.perf_counter()
        capabilities = [capability] if capability else [
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.TRANSLATION,
            ProviderCapability.STRUCTURED_EXTRACTION
        ]
        
        if self.is_circuit_open():
            return [
                HealthReport(
                    provider_name=self.provider_name,
                    capability=cap,
                    status=ProviderStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    message="Circuit breaker open (Ollama offline, deterministic fallback active)"
                )
                for cap in capabilities
            ]

        status = ProviderStatus.UNAVAILABLE
        msg = "Ollama service unreachable"
        latency = None

        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                latency = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    if any(self.model.split(":")[0] in m for m in models):
                        status = ProviderStatus.AVAILABLE
                        msg = f"Gemma model '{self.model}' active"
                        self._record_success()
                    else:
                        status = ProviderStatus.DEGRADED
                        msg = f"Ollama running but model '{self.model}' not loaded"
                else:
                    status = ProviderStatus.ERROR
                    msg = f"Ollama returned HTTP {res.status_code}"
                    self._record_failure()
        except Exception as e:
            msg = f"Connection failed: {str(e)}"
            latency = round((time.perf_counter() - start) * 1000, 2)
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

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False
    ) -> Optional[str]:
        """
        Generates text using Gemma 4 12B with circuit breaker and short timeout.
        Returns None in 0ms if circuit is open or generation fails.
        """
        if self.is_circuit_open():
            return None

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        try:
            with telemetry.measure("ai"):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(f"{self.base_url}/api/generate", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        response_text = data.get("response", "").strip()
                        if response_text:
                            self._record_success()
                            return response_text
                    logger.warning("Gemma Ollama returned status %s: %s", res.status_code, res.text)
                    self._record_failure()
        except Exception as e:
            logger.debug("Gemma generation note (safe fallback active): %s", str(e))
            self._record_failure()

        return None
