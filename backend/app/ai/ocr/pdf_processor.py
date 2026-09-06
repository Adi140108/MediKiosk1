import io
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("medikiosk.ocr.pdf")

class PDFProcessor:
    """
    Processes PDF files for clinical intake:
    1. Extracts embedded machine-readable text directly from each page.
    2. If a page has minimal or no text (scanned page), renders it to high-res image bytes for OCR.
    """
    def __init__(self, render_dpi: int = 200):
        self.render_dpi = render_dpi

    def process_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parses PDF and returns page-by-page text extracts and/or rendered images.
        """
        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        is_scanned_pdf = False

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()

                page_info: Dict[str, Any] = {
                    "page_number": page_num + 1,
                    "extracted_text": text,
                    "has_embedded_text": bool(len(text) > 30),
                    "rendered_image_bytes": None
                }

                # If text is minimal (< 30 chars), render page for OCR
                if not page_info["has_embedded_text"]:
                    is_scanned_pdf = True
                    try:
                        zoom = self.render_dpi / 72.0
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat, alpha=False)
                        page_info["rendered_image_bytes"] = pix.tobytes("png")
                    except Exception as re_err:
                        logger.warning("Failed to render page %d: %s", page_num + 1, str(re_err))
                else:
                    full_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

                pages_data.append(page_info)

            doc.close()

        except Exception as e:
            logger.warning("PyMuPDF processing failed (%s), falling back to pypdf...", str(e))
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                total_pages = len(reader.pages)

                for page_num, page in enumerate(reader.pages):
                    text = (page.extract_text() or "").strip()
                    page_info = {
                        "page_number": page_num + 1,
                        "extracted_text": text,
                        "has_embedded_text": bool(len(text) > 30),
                        "rendered_image_bytes": None
                    }
                    if page_info["has_embedded_text"]:
                        full_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                    else:
                        is_scanned_pdf = True
                    pages_data.append(page_info)
            except Exception as pypdf_err:
                logger.error("All PDF processing libraries failed: %s", str(pypdf_err))
                return {
                    "success": False,
                    "total_pages": 0,
                    "pages": [],
                    "combined_text": "",
                    "is_scanned": True,
                    "error": str(pypdf_err)
                }

        return {
            "success": True,
            "total_pages": len(pages_data),
            "pages": pages_data,
            "combined_text": "\n\n".join(full_text_parts),
            "is_scanned": is_scanned_pdf
        }
