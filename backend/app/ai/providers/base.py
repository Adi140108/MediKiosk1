import enum
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class ProviderCapability(str, enum.Enum):
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    VISION_OCR = "vision_ocr"
    STRUCTURED_EXTRACTION = "structured_extraction"

class ProviderStatus(str, enum.Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    ERROR = "error"

class HealthReport(BaseModel):
    provider_name: str
    capability: ProviderCapability
    status: ProviderStatus
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    last_checked_timestamp: float = Field(default_factory=time.time)

class BaseAIProvider(ABC):
    """
    Abstract base class for all AI/Speech/OCR service providers.
    """
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """Returns True if the provider advertises support for the requested capability."""
        pass

    @abstractmethod
    async def check_health(self, capability: Optional[ProviderCapability] = None) -> List[HealthReport]:
        """Runs live non-intrusive health checks for the provider's capabilities."""
        pass
