import logging
from typing import Dict, Any, Optional
from app.ai.ocr.tesseract import TesseractOCREngine
from app.ai.ocr.gemma_fallback import GemmaVisionFallbackOCR
from app.ai.ocr.pdf_processor import PDFProcessor
from app.ai.ocr.medical_extractor import MedicalDocumentExtractor, StructuredMedicalDocument

logger = logging.getLogger("medikiosk.ocr.pipeline")

class DocumentOCRPipeline:
    """
    Comprehensive, robust Document OCR & Clinical Extraction Pipeline:
    - Supports JPG, JPEG, PNG, WEBP, and multi-page PDF documents.
    - PDF handling: extracts machine text or renders scanned pages.
    - Multi-strategy image OCR with confidence scoring.
    - Structures clinical facts with strict source evidence.
    """
    def __init__(
        self,
        tesseract_engine: Optional[TesseractOCREngine] = None,
        gemma_fallback: Optional[GemmaVisionFallbackOCR] = None,
        pdf_processor: Optional[PDFProcessor] = None,
        medical_extractor: Optional[MedicalDocumentExtractor] = None,
        min_confidence_threshold: float = 0.40
    ):
        self.tesseract = tesseract_engine or TesseractOCREngine()
        self.gemma_fallback = gemma_fallback or GemmaVisionFallbackOCR()
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.medical_extractor = medical_extractor or MedicalDocumentExtractor()
        self.min_confidence_threshold = min_confidence_threshold

    async def process_document(
        self,
        file_bytes: bytes,
        filename: str = "document",
        mime_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Executes end-to-end document processing and structured clinical fact extraction.
        """
        logger.info("Processing document: %s (%s, %d bytes)", filename, mime_type, len(file_bytes))
        
        extracted_text = ""
        confidence = 0.0
        engine_used = "none"
        fallback_triggered = False
        page_count = 1
        is_pdf = mime_type.lower() == "application/pdf" or filename.lower().endswith(".pdf")

        if is_pdf:
            pdf_res = self.pdf_processor.process_pdf(file_bytes)
            page_count = pdf_res.get("total_pages", 1)
            
            if pdf_res.get("combined_text"):
                extracted_text = pdf_res["combined_text"]
                confidence = 0.95
                engine_used = "pdf_embedded_text"
            else:
                # Scanned PDF: OCR rendered pages
                page_texts = []
                page_confs = []
                for p in pdf_res.get("pages", []):
                    img_bytes = p.get("rendered_image_bytes")
                    if img_bytes:
                        p_text, p_conf = self.tesseract.extract_text(img_bytes)
                        if not p_text and self.gemma_fallback:
                            p_text, p_conf = self.gemma_fallback.extract_text(img_bytes)
                            fallback_triggered = True
                        if p_text:
                            page_texts.append(f"--- Page {p['page_number']} ---\n{p_text}")
                            page_confs.append(p_conf)
                
                extracted_text = "\n\n".join(page_texts)
                confidence = round(sum(page_confs) / len(page_confs), 2) if page_confs else 0.0
                engine_used = "pdf_rendered_ocr"
        else:
            # Image OCR
            raw_text, conf = self.tesseract.extract_text(file_bytes)
            engine_used = "tesseract_multistrategy"

            if not raw_text or conf < self.min_confidence_threshold:
                logger.info("Tesseract confidence low (%.2f). Attempting Gemma vision fallback.", conf)
                vis_text, vis_conf = self.gemma_fallback.extract_text(file_bytes)
                if vis_text:
                    raw_text = vis_text
                    conf = vis_conf
                    engine_used = "gemma4_vision_fallback"
                    fallback_triggered = True

            extracted_text = raw_text
            confidence = conf

        # Extract structured medical entities with source evidence
        structured_doc: StructuredMedicalDocument = await self.medical_extractor.extract_structured_document(
            raw_text=extracted_text,
            document_filename=filename,
            page_number=1,
            ocr_confidence=confidence
        )

        return {
            "filename": filename,
            "page_count": page_count,
            "extracted_text": extracted_text,
            "confidence": confidence,
            "engine_used": engine_used,
            "fallback_triggered": fallback_triggered,
            "status": "OCR_COMPLETE" if extracted_text else "FAILED",
            "structured_findings": structured_doc.model_dump()
        }
