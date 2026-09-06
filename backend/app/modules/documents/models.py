from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    document_id: str
    patient_id: Optional[str] = None  # ABHA ID or Patient ID when available
    session_id: str
    storage_provider: str  # 'cloudinary' or 'backblaze_b2'
    storage_key: str  # public_id or b2_object_key
    original_filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document_type: str  # 'profile_image', 'medical_report', 'prescription', 'id_card', etc.
    ocr_status: str = "pending"  # 'pending', 'completed', 'failed', 'not_applicable'
    extraction_status: str = "pending"  # 'pending', 'completed', 'failed', 'not_applicable'
    extracted_text: Optional[str] = None
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    source_evidence: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)  # e.g., asset_id, secure_url for Cloudinary

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        if isinstance(data.get("uploaded_at"), datetime):
            data["uploaded_at"] = data["uploaded_at"].isoformat()
        return data
