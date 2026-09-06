import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.ocr.pipeline import DocumentOCRPipeline
from app.ai.ocr.tesseract import TesseractOCREngine
from app.ai.ocr.gemma_fallback import GemmaVisionFallbackOCR
from app.ai.fallback.manager import MultilingualFallbackManager

# 18. OCR failure triggers Gemma fallback
@pytest.mark.asyncio
async def test_ocr_failure_triggers_gemma_fallback(mocker):
    # Mock Tesseract failing / low confidence
    mock_tesseract = mocker.MagicMock()
    mock_tesseract.extract_text.return_value = ("", 0.10)

    # Mock Gemma Vision fallback succeeding
    mock_gemma_ocr = mocker.MagicMock()
    mock_gemma_ocr.extract_text.return_value = ("Prescription: Paracetamol 500mg TDS", 0.95)

    pipeline = DocumentOCRPipeline(
        tesseract_engine=mock_tesseract,
        gemma_fallback=mock_gemma_ocr,
        min_confidence_threshold=0.50
    )

    result = await pipeline.process_document(b"fake_image_bytes")

    assert result["fallback_triggered"] is True
    assert result["engine_used"] == "gemma4_vision_fallback"
    assert "Paracetamol" in result["extracted_text"]
    assert result["confidence"] >= 0.90
    mock_tesseract.extract_text.assert_called_once()
    mock_gemma_ocr.extract_text.assert_called_once()

# 19. AI4Bharat failure triggers appropriate fallback
@pytest.mark.asyncio
async def test_ai4bharat_failure_triggers_gemma_fallback(mocker):
    # Mock Gemma client
    mock_gemma = mocker.MagicMock()
    mock_gemma.generate_response = mocker.AsyncMock(return_value="आपकी पाचन क्रिया कैसी है? (Agni)")

    manager = MultilingualFallbackManager(gemma_client=mock_gemma)

    # Calling translation with AI4Bharat key unset/failing will invoke Gemma
    translated = await manager.translate_text(
        text="How is your digestion? (Agni)",
        target_lang="hi",
        source_lang="en"
    )

    assert "पाचन" in translated or "Agni" in translated
    mock_gemma.generate_response.assert_called_once()
