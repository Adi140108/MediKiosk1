import logging
import json
from typing import Dict, Any, Optional
from app.ai.providers.gemma_provider import GemmaProvider

logger = logging.getLogger("medikiosk.gemma")

class GemmaClient:
    """
    Client for Gemma 4 12B running on Ollama.
    Never fabricates clinical answers or synthetic patient information when Ollama is offline.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.provider = GemmaProvider(base_url=base_url, model=model, timeout=timeout or 8.0)

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False
    ) -> str:
        """
        Calls GemmaProvider for text generation.
        Returns empty string or structured empty JSON if Ollama is unavailable.
        """
        res = await self.provider.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            format_json=format_json
        )
        if res is not None:
            return res

        # Honest fallback without fabricating clinical facts
        if format_json:
            return json.dumps({
                "status": "ai_unavailable",
                "message": "AI generation service is currently offline. Deterministic clinical rules remain active.",
                "data": None
            })
        return ""
