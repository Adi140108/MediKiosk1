from typing import Dict, Any, Optional, List
from app.ai.providers.base import BaseAIProvider, ProviderCapability, ProviderStatus, HealthReport

class BrowserFallbackProvider(BaseAIProvider):
    """
    Represents client-side browser capabilities (Web Speech API, SpeechSynthesis).
    """
    def __init__(self):
        super().__init__(provider_name="Browser Web Speech API")

    def supports_capability(self, capability: ProviderCapability) -> bool:
        return capability in (
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH
        )

    async def check_health(self, capability: Optional[ProviderCapability] = None) -> List[HealthReport]:
        capabilities = [capability] if capability else [
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH
        ]
        return [
            HealthReport(
                provider_name=self.provider_name,
                capability=cap,
                status=ProviderStatus.AVAILABLE,
                latency_ms=0.0,
                message="Browser Web Speech API standard client-side fallback"
            )
            for cap in capabilities
        ]
