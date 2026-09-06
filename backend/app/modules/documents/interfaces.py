from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

class StorageProvider(ABC):
    @abstractmethod
    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder_or_prefix: Optional[str] = None,
        custom_metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads a file to the storage provider and returns provider metadata.
        Must not log sensitive keys or secrets.
        """
        pass

    @abstractmethod
    def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """
        Generates an authenticated/signed temporary access URL for viewing.
        """
        pass

    @abstractmethod
    def health_check(self) -> Tuple[bool, str]:
        """
        Checks health/connectivity of the provider.
        Returns (is_healthy, status_message).
        """
        pass
