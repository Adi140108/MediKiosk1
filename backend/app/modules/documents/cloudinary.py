import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any, Tuple, Optional
from app.modules.documents.interfaces import StorageProvider
from app.config import settings

logger = logging.getLogger(__name__)

class CloudinaryStorageProvider(StorageProvider):
    def __init__(self, cloud_name: str = None, api_key: str = None, api_secret: str = None, folder: str = None):
        self.cloud_name = cloud_name or settings.CLOUDINARY_CLOUD_NAME
        self.api_key = api_key or settings.CLOUDINARY_API_KEY
        self.api_secret = api_secret or settings.CLOUDINARY_API_SECRET
        self.folder = folder or settings.CLOUDINARY_FOLDER

        # Configure Cloudinary SDK
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder_or_prefix: Optional[str] = None,
        custom_metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads image file to Cloudinary using signed server-side upload.
        Never exposes API secret in logs or returned payload.
        """
        folder = f"{self.folder}/{folder_or_prefix}" if folder_or_prefix else self.folder

        if not self.api_secret or not self.cloud_name or not self.api_key:
            raise ValueError("Cloudinary credentials are not configured.")

        try:
            logger.info("Uploading image asset to Cloudinary folder: %s", folder)
            response = cloudinary.uploader.upload(
                file_bytes,
                folder=folder,
                resource_type="image",
                use_filename=True,
                unique_filename=True
            )

            # Extract required Cloudinary fields
            result = {
                "asset_id": response.get("asset_id"),
                "public_id": response.get("public_id"),
                "secure_url": response.get("secure_url"),
                "resource_type": response.get("resource_type", "image"),
                "format": response.get("format"),
                "bytes": response.get("bytes")
            }
            return result
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", str(e))
            raise RuntimeError(f"Cloudinary upload failed: {str(e)}") from e

    def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """
        Generates a secure Cloudinary URL for the public_id.
        """
        url, _ = cloudinary.utils.cloudinary_url(
            storage_key,
            secure=True
        )
        return url

    def health_check(self) -> Tuple[bool, str]:
        """
        Checks Cloudinary API connection by pinging the API.
        """
        if not self.api_secret or not self.cloud_name or not self.api_key:
            return False, "Cloudinary configuration incomplete (missing credentials)"
        try:
            res = cloudinary.api.ping()
            if res.get("status") == "ok":
                return True, "Cloudinary health check passed"
            return False, f"Unexpected ping status: {res}"
        except Exception as e:
            logger.error("Cloudinary health check failed: %s", str(e))
            return False, f"Cloudinary health check error: {str(e)}"
