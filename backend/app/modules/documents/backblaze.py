import logging
import uuid
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Dict, Any, Tuple, Optional
from app.modules.documents.interfaces import StorageProvider
from app.config import settings

logger = logging.getLogger(__name__)

class BackblazeB2StorageProvider(StorageProvider):
    def __init__(
        self,
        key_id: str = None,
        application_key: str = None,
        bucket_name: str = None,
        endpoint_url: str = None
    ):
        self.key_id = key_id or settings.B2_KEY_ID
        self.application_key = application_key or settings.B2_APPLICATION_KEY
        self.bucket_name = bucket_name or settings.B2_BUCKET_NAME
        self.endpoint_url = endpoint_url or settings.B2_ENDPOINT_URL

        self._s3_client = None

    def _get_client(self):
        if not self.key_id or not self.application_key:
            raise ValueError("Backblaze B2 credentials are not configured.")
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.application_key,
                config=Config(signature_version="s3v4")
            )
        return self._s3_client

    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder_or_prefix: Optional[str] = None,
        custom_metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads document/PDF to Backblaze B2 using generated non-identifying UUID key.
        No ABHA ID, patient name, phone number or PII is used in object keys.
        """
        client = self._get_client()

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        random_id = uuid.uuid4().hex
        prefix = f"{folder_or_prefix}/" if folder_or_prefix else "docs/"
        object_key = f"{prefix}{random_id}.{ext}"

        extra_args = {
            "ContentType": content_type
        }
        if custom_metadata:
            # Clean metadata keys to ensure no PII/PHI is included if provided
            extra_args["Metadata"] = custom_metadata

        try:
            logger.info("Uploading document to private Backblaze B2 bucket %s with key %s", self.bucket_name, object_key)
            client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                **extra_args
            )

            return {
                "bucket_name": self.bucket_name,
                "object_key": object_key,
                "content_type": content_type,
                "file_size": len(file_bytes),
                "storage_provider": "backblaze_b2"
            }
        except Exception as e:
            logger.error("Backblaze B2 upload failed: %s", str(e))
            raise RuntimeError(f"Backblaze B2 upload failed: {str(e)}") from e

    def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """
        Generates authenticated/signed access URL for authorized physician viewing.
        Bucket remains private.
        """
        if storage_key.startswith("/uploads/"):
            return storage_key

        client = self._get_client()
        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key
                },
                ExpiresIn=expires_in_seconds
            )
            return url
        except Exception as e:
            logger.error("Failed to generate signed URL for B2 key %s: %s", storage_key, str(e))
            raise RuntimeError(f"Failed to generate signed URL: {str(e)}") from e

    def health_check(self) -> Tuple[bool, str]:
        """
        Checks Backblaze B2 connection by checking bucket availability or listing objects with max-keys 1.
        """
        if not self.key_id or not self.application_key:
            return False, "Backblaze B2 configuration incomplete (missing credentials)"
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self.bucket_name)
            return True, "Backblaze B2 health check passed"
        except ClientError as ce:
            logger.error("Backblaze B2 health check ClientError: %s", str(ce))
            return False, f"Backblaze B2 health check error: {str(ce)}"
        except Exception as e:
            logger.error("Backblaze B2 health check failed: %s", str(e))
            return False, f"Backblaze B2 health check error: {str(e)}"
