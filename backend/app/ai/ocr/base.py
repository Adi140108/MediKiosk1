from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class BaseOCREngine(ABC):
    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Extracts raw text from image bytes and returns (extracted_text, confidence_score).
        Confidence score between 0.0 and 1.0.
        """
        pass
