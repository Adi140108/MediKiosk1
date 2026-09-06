import logging
import time
import json
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

logger = logging.getLogger("medikiosk.ai.gemma_provider")

class GemmaProvider(BaseAIProvider):
    """
    Provider for local/hosted Gemma 4 12B via Ollama.
    Never fabricates clinical answers when offline.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0
    ):
        super().__init__(provider_name="Gemma 4 12B (Ollama)")
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.GEMMA_MODEL
        self.timeout = timeout

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
        
        status = ProviderStatus.UNAVAILABLE
        msg = "Ollama service unreachable"
        latency = None

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                latency = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    if any(self.model.split(":")[0] in m for m in models):
                        status = ProviderStatus.AVAILABLE
                        msg = f"Gemma model '{self.model}' active"
                    else:
                        status = ProviderStatus.DEGRADED
                        msg = f"Ollama running but model '{self.model}' not loaded"
                else:
                    status = ProviderStatus.ERROR
                    msg = f"Ollama returned HTTP {res.status_code}"
        except Exception as e:
            msg = f"Connection failed: {str(e)}"
            latency = round((time.perf_counter() - start) * 1000, 2)

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
        Generates text using Gemma 4 12B.
        Returns None if generation fails or Ollama is unavailable.
        """
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text
                logger.warning("Gemma Ollama returned status %s: %s", res.status_code, res.text)
        except Exception as e:
            logger.info("Gemma generation unavailable: %s", str(e))

        return None
