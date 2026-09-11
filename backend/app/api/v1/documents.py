import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from app.core.telemetry import telemetry
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

async def _background_ocr_worker(
    document_id: str,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    session_id: str,
    patient_id: str,
    storage_provider: str,
    storage_key: str
):
    """
    Asynchronous Background Worker for OCR & Structured Clinical Fact Extraction.
    Executes outside the HTTP request lifecycle so Vercel endpoints respond in <400ms.
    """
    try:
        logger.info("Starting background OCR for document: %s (%s)", document_id, filename)
        with telemetry.measure("ocr"):
            ocr_res = await ocr_pipeline.process_document(
                file_bytes=file_bytes,
                filename=filename,
                mime_type=mime_type
            )

        # Retrieve and update stored metadata
        with telemetry.measure("database"):
            meta = storage_service.firestore.get_document_metadata(document_id)
            if meta:
                if isinstance(meta, dict):
                    meta["ocr_status"] = "COMPLETED"
                    meta["extracted_text"] = ocr_res.get("extracted_text", "")
                    prov_meta = meta.get("provider_metadata")
                    if not isinstance(prov_meta, dict):
                        prov_meta = {}
                    prov_meta["confidence"] = ocr_res.get("confidence", 0.90)
                    prov_meta["page_count"] = ocr_res.get("page_count", 1)
                    prov_meta["structured_findings"] = ocr_res.get("structured_findings")
                    prov_meta["engine_used"] = ocr_res.get("engine_used")
                    meta["provider_metadata"] = prov_meta
                    storage_service.firestore.save_document_metadata(meta)
                else:
                    meta.ocr_status = "COMPLETED"
                    meta.extracted_text = ocr_res.get("extracted_text", "")
                    if hasattr(meta, "provider_metadata") and isinstance(meta.provider_metadata, dict):
                        meta.provider_metadata["confidence"] = ocr_res.get("confidence", 0.90)
                        meta.provider_metadata["page_count"] = ocr_res.get("page_count", 1)
                        meta.provider_metadata["structured_findings"] = ocr_res.get("structured_findings")
                        meta.provider_metadata["engine_used"] = ocr_res.get("engine_used")
                    storage_service.firestore.save_document_metadata(meta)

            # Record timeline event
            event = TimelineEvent(
                event_id=f"evt_doc_{document_id}",
                patient_id=patient_id,
                session_id=session_id,
                event_type=TimelineEventType.DOCUMENT_UPLOADED,
                title=f"Document Processed ({storage_provider})",
                description=f"File {filename} verified and processed. OCR: {ocr_res.get('engine_used', 'complete')}.",
                source_type=SourceType.DOCUMENT,
                evidence_reference=storage_key
            )
            timeline_repo.record_event(event)

        logger.info("Background OCR completed successfully for document %s", document_id)
    except Exception as e:
        logger.error("Background OCR worker encountered error for %s: %s", document_id, str(e))
        try:
            meta = storage_service.firestore.get_document_metadata(document_id)
            if meta:
                if isinstance(meta, dict):
                    meta["ocr_status"] = "OCR_FAILED"
                else:
                    meta.ocr_status = "OCR_FAILED"
                storage_service.firestore.save_document_metadata(meta)
        except Exception:
            pass

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    patient_id: str = Form(...),
    document_type: str = Form("medical_report"),
    perform_ocr: bool = Form(True)
):
    """
    Non-blocking document upload:
    1. Stores document bytes securely to Cloudinary/Backblaze B2.
    2. Writes metadata with status='PROCESSING'.
    3. Dispatches OCR processing to background task.
    4. Returns immediate response in <400ms.
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "uploaded_document"
        content_type = file.content_type or "application/octet-stream"

        with telemetry.measure("storage"):
            metadata = storage_service.store_document(
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
                session_id=session_id,
                document_type=document_type,
                patient_id=patient_id
            )

        if perform_ocr:
            metadata.ocr_status = "PROCESSING"
            with telemetry.measure("database"):
                storage_service.firestore.save_document_metadata(metadata)

            # Dispatch non-blocking background task
            background_tasks.add_task(
                _background_ocr_worker,
                document_id=metadata.document_id,
                file_bytes=file_bytes,
                filename=filename,
                mime_type=content_type,
                session_id=session_id,
                patient_id=patient_id,
                storage_provider=metadata.storage_provider,
                storage_key=metadata.storage_key
            )

        access_url = f"/api/v1/documents/{metadata.document_id}/file"
        try:
            url, _ = storage_service.get_document_access_url(metadata.document_id)
            if url and (url.startswith("http://") or url.startswith("https://")):
                access_url = url
        except Exception:
            pass

        return {
            "status": "success",
            "document_id": metadata.document_id,
            "ocr_status": metadata.ocr_status,
            "storage_provider": metadata.storage_provider,
            "access_url": access_url,
            "metadata": metadata.model_dump(),
            "message": "Document uploaded and stored securely. OCR processing in background."
        }
    except Exception as e:
        logger.error("Document upload failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}/status")
def get_document_status(document_id: str):
    """
    Returns live OCR processing status and structured extracted findings for frontend polling.
    """
    try:
        with telemetry.measure("database"):
            meta = storage_service.firestore.get_document_metadata(document_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Document metadata not found")

        access_url = f"/api/v1/documents/{document_id}/file"
        try:
            url, _ = storage_service.get_document_access_url(document_id)
            if url and (url.startswith("http://") or url.startswith("https://")):
                access_url = url
        except Exception:
            pass

        if isinstance(meta, dict):
            prov_meta = meta.get("provider_metadata") or {}
            created_at_val = meta.get("created_at")
            return {
                "document_id": meta.get("document_id", document_id),
                "ocr_status": meta.get("ocr_status", "COMPLETED"),
                "extracted_text": meta.get("extracted_text", ""),
                "confidence": prov_meta.get("confidence", 0.92),
                "page_count": prov_meta.get("page_count", 1),
                "structured_findings": prov_meta.get("structured_findings"),
                "storage_provider": meta.get("storage_provider", "encrypted"),
                "access_url": access_url,
                "created_at": created_at_val.isoformat() if hasattr(created_at_val, 'isoformat') else str(created_at_val or '')
            }
        else:
            prov_meta = meta.provider_metadata if hasattr(meta, 'provider_metadata') and isinstance(meta.provider_metadata, dict) else {}
            return {
                "document_id": meta.document_id,
                "ocr_status": meta.ocr_status,
                "extracted_text": meta.extracted_text,
                "confidence": prov_meta.get("confidence", 0.92),
                "page_count": prov_meta.get("page_count", 1),
                "structured_findings": prov_meta.get("structured_findings"),
                "storage_provider": meta.storage_provider,
                "access_url": access_url,
                "created_at": meta.created_at.isoformat() if hasattr(meta.created_at, 'isoformat') else str(meta.created_at)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}/access-url")
def get_document_access_url(document_id: str):
    try:
        url, metadata = storage_service.get_document_access_url(document_id)
        if not url or url.startswith("data:") or url.startswith("/uploads/"):
            url = f"/api/v1/documents/{document_id}/file"
        return {
            "document_id": document_id,
            "access_url": url,
            "storage_provider": metadata.get("storage_provider") if isinstance(metadata, dict) else getattr(metadata, "storage_provider", "encrypted"),
            "original_filename": metadata.get("original_filename") if isinstance(metadata, dict) else getattr(metadata, "original_filename", "document")
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{document_id}/file")
def get_document_file(document_id: str):
    """
    Directly streams document image or PDF for browser rendering in patient & physician portals.
    Supports local base64 fallback, data URIs, and remote signed cloud storage.
    """
    try:
        meta = storage_service.firestore.get_document_metadata(document_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Document metadata not found")

        content_type = (
            (meta.get("content_type") if isinstance(meta, dict) else getattr(meta, "content_type", None))
            or "application/octet-stream"
        )
        filename = (
            (meta.get("original_filename") if isinstance(meta, dict) else getattr(meta, "original_filename", None))
            or "document"
        )
        if filename.lower().endswith(".pdf") and (not content_type or content_type == "application/octet-stream"):
            content_type = "application/pdf"
        prov_meta = (
            (meta.get("provider_metadata") if isinstance(meta, dict) else getattr(meta, "provider_metadata", None))
            or {}
        )
        secure_url = prov_meta.get("secure_url") or ""

        # If remote HTTPS, redirect directly
        if secure_url.startswith("http://") or secure_url.startswith("https://"):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=secure_url)

        # If data URI, decode and stream bytes
        if secure_url.startswith("data:"):
            import base64
            header, b64_data = secure_url.split(",", 1)
            mime_part = header.split(";")[0].replace("data:", "").strip()
            if mime_part:
                content_type = mime_part
            file_bytes = base64.b64decode(b64_data)
            from fastapi import Response
            return Response(
                content=file_bytes,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{filename}\"",
                    "Cache-Control": "public, max-age=3600"
                }
            )

        # Check storage service access url
        try:
            url, _ = storage_service.get_document_access_url(document_id)
            if url and (url.startswith("http://") or url.startswith("https://")):
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=url)
            elif url and url.startswith("data:"):
                import base64
                header, b64_data = url.split(",", 1)
                file_bytes = base64.b64decode(b64_data)
                from fastapi import Response
                return Response(
                    content=file_bytes,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"inline; filename=\"{filename}\"",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
        except Exception:
            pass

        raise HTTPException(status_code=404, detail="Document file content not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to serve document file %s: %s", document_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))
