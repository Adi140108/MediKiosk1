import logging
from typing import Dict, Any, Optional
from app.ai.providers.provider_manager import AIProviderManager

logger = logging.getLogger("medikiosk.fallback.manager")

class MultilingualFallbackManager:
    """
    Manages Multilingual translation & speech workflows via AIProviderManager.
    Never fabricates clinical answers or synthetic translations.
    """
    def __init__(
        self,
        provider_manager: Optional[AIProviderManager] = None,
        gemma_client: Optional[Any] = None
    ):
        self.provider_manager = provider_manager or AIProviderManager()
        self.gemma_client = gemma_client

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> str:
        """
        Translates text with fallback hierarchy: AI4Bharat -> Gemma 4 12B -> Original text.
        """
        if self.gemma_client:
            # Direct gemma_client override for testing / legacy compatibility
            try:
                if hasattr(self.gemma_client, "generate_response"):
                    res = await self.gemma_client.generate_response(
                        f"Translate from {source_lang} to {target_lang}: {text}"
                    )
                    if res:
                        return str(res).strip()
                elif hasattr(self.gemma_client, "generate_text"):
                    res = await self.gemma_client.generate_text(
                        f"Translate from {source_lang} to {target_lang}: {text}"
                    )
                    if res:
                        return str(res).strip()
            except Exception as e:
                logger.warning("Custom gemma_client translation error: %s", str(e))

        result = await self.provider_manager.translate_text(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang
        )
        return result.get("normalized_text", text)

    async def translate_with_metadata(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Translates text and returns full provenance metadata.
        """
        return await self.provider_manager.translate_text(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang
        )
