import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.modules.documents.storage_service import StorageService
from app.ai.ocr.pipeline import DocumentOCRPipeline
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.core.security import SourceType
from app.db.repositories.timeline_repository import TimelineRepository

logger = logging.getLogger("medikiosk.api.documents")
router = APIRouter(prefix="/documents", tags=["documents"])

storage_service = StorageService()
ocr_pipeline = DocumentOCRPipeline()
timeline_repo = TimelineRepository()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    patient_id: str = Form(...),
    document_type: str = Form("medical_report"),
    perform_ocr: bool = Form(True)
):
    try:
        file_bytes = await file.read()
        metadata = storage_service.store_document(
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_document",
            content_type=file.content_type or "application/octet-stream",
            session_id=session_id,
            document_type=document_type,
            patient_id=patient_id
        )

        ocr_result = None
        if perform_ocr:
            ocr_res = await ocr_pipeline.process_document(
                file_bytes=file_bytes,
                filename=file.filename or "uploaded_document",
                mime_type=file.content_type or "application/octet-stream"
            )
            ocr_result = ocr_res
            # Update metadata with real OCR text & structured findings
            metadata.ocr_status = ocr_res.get("status", "OCR_COMPLETE")
            metadata.extracted_text = ocr_res.get("extracted_text")
            if hasattr(metadata, "provider_metadata") and isinstance(metadata.provider_metadata, dict):
                metadata.provider_metadata["confidence"] = ocr_res.get("confidence", 0.0)
                metadata.provider_metadata["page_count"] = ocr_res.get("page_count", 1)
                metadata.provider_metadata["structured_findings"] = ocr_res.get("structured_findings")
            storage_service.firestore.save_document_metadata(metadata)

        # Log timeline event
        event = TimelineEvent(
            event_id=f"evt_doc_{metadata.document_id}",
            patient_id=patient_id,
            session_id=session_id,
            event_type=TimelineEventType.DOCUMENT_UPLOADED,
            title=f"Document Uploaded ({metadata.storage_provider})",
            description=f"File {file.filename} uploaded to {metadata.storage_provider}." + (f" OCR: {ocr_result.get('engine_used')}" if ocr_result else ""),
            source_type=SourceType.DOCUMENT,
            evidence_reference=metadata.storage_key
        )
        timeline_repo.record_event(event)

        return {
            "status": "success",
            "metadata": metadata.model_dump(),
            "ocr": ocr_result
        }
    except Exception as e:
        logger.error("Document upload/OCR failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}/access-url")
def get_document_access_url(document_id: str):
    try:
        url, metadata = storage_service.get_document_access_url(document_id)
        return {
            "document_id": document_id,
            "access_url": url,
            "storage_provider": metadata.get("storage_provider"),
            "original_filename": metadata.get("original_filename")
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
