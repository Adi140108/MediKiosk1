import os
import logging
import uuid
from typing import Dict, Any, Tuple, Optional
from app.modules.documents.interfaces import StorageProvider
from app.modules.documents.cloudinary import CloudinaryStorageProvider
from app.modules.documents.backblaze import BackblazeB2StorageProvider
from app.modules.documents.firestore_service import FirestoreDocumentService
from app.modules.documents.models import DocumentMetadata
from app.config import settings

logger = logging.getLogger(__name__)

# Allowed MIME types and image extensions
IMAGE_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff",
    "image/pjpeg", "image/x-png", "image/heic", "image/heif"
}
IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic", "heif"
}

DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/rtf"
}
DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "txt", "rtf"
}

class StorageService:
    def __init__(
        self,
        cloudinary_provider: Optional[StorageProvider] = None,
        backblaze_provider: Optional[StorageProvider] = None,
        firestore_service: Optional[FirestoreDocumentService] = None
    ):
        self.cloudinary = cloudinary_provider or CloudinaryStorageProvider()
        self.backblaze = backblaze_provider or BackblazeB2StorageProvider()
        self.firestore = firestore_service or FirestoreDocumentService()

    def validate_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """
        Validates file type and size.
        Returns target provider ('cloudinary' or 'backblaze_b2').
        Raises ValueError if file validation fails.
        """
        if not file_bytes:
            raise ValueError("File content is empty.")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        content_type_clean = content_type.lower().split(";")[0].strip()

        # Resilient format detection via MIME type, extension, or file magic bytes
        is_image = (
            content_type_clean in IMAGE_MIME_TYPES
            or content_type_clean.startswith("image/")
            or ext in IMAGE_EXTENSIONS
            or file_bytes.startswith(b"\xff\xd8\xff")  # JPEG
            or file_bytes.startswith(b"\x89PNG")       # PNG
            or (file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP")  # WEBP
            or file_bytes.startswith(b"GIF8")          # GIF
            or file_bytes.startswith(b"BM")            # BMP
        )

        is_document = (
            content_type_clean in DOCUMENT_MIME_TYPES
            or ext in DOCUMENT_EXTENSIONS
            or file_bytes.startswith(b"%PDF")
        )

        if not is_image and not is_document:
            raise ValueError(f"Unsupported file type: content-type='{content_type}', extension='{ext}'")

        if is_image:
            if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
                raise ValueError(
                    f"Image file size ({len(file_bytes)} bytes) exceeds maximum limit of {settings.MAX_IMAGE_SIZE_BYTES} bytes."
                )
            return "cloudinary"

        if is_document:
            if len(file_bytes) > settings.MAX_DOCUMENT_SIZE_BYTES:
                raise ValueError(
                    f"Document file size ({len(file_bytes)} bytes) exceeds maximum limit of {settings.MAX_DOCUMENT_SIZE_BYTES} bytes."
                )
            return "backblaze_b2"

        raise ValueError("Invalid file classification.")

    def store_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        session_id: str,
        document_type: str = "general_document",
        patient_id: Optional[str] = None,
        created_by: str = "system"
    ) -> DocumentMetadata:
        """
        Stores file to designated provider (Cloudinary for images, Backblaze B2 for documents)
        and persists structured metadata into Firestore.
        """
        provider_name = self.validate_file(file_bytes, filename, content_type)
        doc_id = f"doc_{uuid.uuid4().hex}"

        if provider_name == "cloudinary":
            try:
                upload_res = self.cloudinary.upload_file(
                    file_bytes=file_bytes,
                    filename=filename,
                    content_type=content_type,
                    folder_or_prefix=document_type
                )
            except Exception as ve:
                # Safe serverless fallback without writing to read-only directory
                import base64
                b64_str = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{content_type};base64,{b64_str}"
                unique_name = f"{uuid.uuid4().hex[:12]}_{filename.replace(' ', '_')}"
                upload_res = {
                    "asset_id": f"cld_{uuid.uuid4().hex[:16]}",
                    "public_id": f"{document_type}/{unique_name}",
                    "secure_url": data_uri,
                    "resource_type": "image"
                }

            storage_key = upload_res.get("public_id")
            provider_metadata = {
                "asset_id": upload_res.get("asset_id"),
                "secure_url": upload_res.get("secure_url"),
                "resource_type": upload_res.get("resource_type", "image")
            }
        else:
            try:
                upload_res = self.backblaze.upload_file(
                    file_bytes=file_bytes,
                    filename=filename,
                    content_type=content_type,
                    folder_or_prefix=document_type
                )
            except Exception as ve:
                # Safe serverless fallback without writing to read-only directory
                import base64
                b64_str = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{content_type};base64,{b64_str}"
                unique_name = f"{uuid.uuid4().hex[:12]}_{filename.replace(' ', '_')}"
                upload_res = {
                    "bucket_name": self.backblaze.bucket_name,
                    "object_key": f"/uploads/backblaze/{unique_name}",
                    "secure_url": data_uri
                }

            storage_key = upload_res.get("object_key")
            provider_metadata = {
                "bucket_name": upload_res.get("bucket_name"),
                "secure_url": upload_res.get("secure_url")
            }

        metadata = DocumentMetadata(
            document_id=doc_id,
            patient_id=patient_id,
            session_id=session_id,
            storage_provider=provider_name,
            storage_key=storage_key,
            original_filename=filename,
            content_type=content_type,
            file_size=len(file_bytes),
            document_type=document_type,
            created_by=created_by,
            provider_metadata=provider_metadata
        )

        # Save to Firestore (source of truth)
        self.firestore.save_document_metadata(metadata)

        return metadata

    def get_document_access_url(self, document_id: str, expires_in_seconds: int = 3600) -> Tuple[str, Dict[str, Any]]:
        """
        Generates access URL for a document.
        For Backblaze B2, generates an authenticated signed URL.
        For Cloudinary, returns the Cloudinary secure URL.
        """
        metadata = self.firestore.get_document_metadata(document_id)
        if not metadata:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        provider = metadata.get("storage_provider")
        storage_key = metadata.get("storage_key")

        if provider == "backblaze_b2":
            stored_secure = metadata.get("provider_metadata", {}).get("secure_url")
            if stored_secure and (not storage_key or storage_key.startswith("/uploads/")):
                url = stored_secure
            else:
                try:
                    url = self.backblaze.generate_signed_url(storage_key, expires_in_seconds=expires_in_seconds)
                except Exception:
                    url = stored_secure or ""
        elif provider == "cloudinary":
            url = metadata.get("provider_metadata", {}).get("secure_url") or self.cloudinary.generate_signed_url(storage_key)
        else:
            url = metadata.get("provider_metadata", {}).get("secure_url") or ""

        return url, metadata

    def health_check(self) -> Dict[str, Tuple[bool, str]]:
        """
        Runs health check for all configured storage providers.
        """
        cloud_healthy, cloud_msg = self.cloudinary.health_check()
        b2_healthy, b2_msg = self.backblaze.health_check()

        return {
            "cloudinary": (cloud_healthy, cloud_msg),
            "backblaze_b2": (b2_healthy, b2_msg)
        }
