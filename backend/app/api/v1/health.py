import logging
import pytesseract
from fastapi import APIRouter
from typing import Dict, Any
from app.modules.documents.storage_service import StorageService
from app.ai.providers.provider_manager import AIProviderManager
from app.ai.ocr.tesseract import TesseractOCREngine

logger = logging.getLogger("medikiosk.api.health")
router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
@router.get("")
async def get_system_health() -> Dict[str, Any]:
    storage_svc = StorageService()
    storage_health = storage_svc.health_check()
    ai_manager = AIProviderManager()
    ai_overview = await ai_manager.get_health_overview()

    ocr_installed_langs = []
    ocr_status = "unavailable"
    try:
        tess = TesseractOCREngine()
        ocr_installed_langs = tess.available_languages
        ocr_status = "available" if ocr_installed_langs else "degraded"
    except Exception as e:
        logger.warning("OCR health check error: %s", str(e))

    return {
        "status": "online",
        "service": "MediKiosk Clinical Intelligence API",
        "storage": {
            "cloudinary": {
                "status": "available" if storage_health["cloudinary"][0] else "unavailable",
                "message": storage_health["cloudinary"][1]
            },
            "backblaze_b2": {
                "status": "available" if storage_health["backblaze_b2"][0] else "unavailable",
                "message": storage_health["backblaze_b2"][1]
            }
        },
        "ai_engine": {
            "gemma_status": ai_overview.get("gemma_status", "unavailable"),
            "ai4bharat_translation": ai_overview.get("ai4bharat_translation", "unavailable"),
            "ai4bharat_tts": ai_overview.get("ai4bharat_tts", "unavailable"),
            "ai4bharat_asr": ai_overview.get("ai4bharat_asr", "unavailable")
        },
        "ocr_engine": {
            "status": ocr_status,
            "installed_languages": ocr_installed_langs
        }
    }

@router.get("/ai")
async def get_ai_health() -> Dict[str, Any]:
    ai_manager = AIProviderManager()
    return await ai_manager.get_health_overview()

@router.get("/ocr")
async def get_ocr_health() -> Dict[str, Any]:
    try:
        tess = TesseractOCREngine()
        return {
            "status": "available" if tess.available_languages else "degraded",
            "available_languages": tess.available_languages,
            "active_language_string": tess.active_lang_string,
            "supported_document_types": ["image/jpeg", "image/png", "image/webp", "application/pdf"]
        }
    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
            "fallback": "Gemma Vision OCR"
        }

@router.get("/storage")
async def get_storage_health() -> Dict[str, Any]:
    storage_svc = StorageService()
    return storage_svc.health_check()

@router.get("/multilingual")
async def get_multilingual_health() -> Dict[str, Any]:
    ai_manager = AIProviderManager()
    overview = await ai_manager.get_health_overview()
    return {
        "supported_languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "Hindi (हिंदी)"},
            {"code": "kn", "name": "Kannada (ಕನ್ನಡ)"},
            {"code": "ta", "name": "Tamil (தமிழ்)"},
            {"code": "te", "name": "Telugu (తెలుగు)"},
            {"code": "ml", "name": "Malayalam (മലയാളം)"},
            {"code": "mr", "name": "Marathi (मराठी)"},
            {"code": "bn", "name": "Bengali (বাংলা)"},
            {"code": "gu", "name": "Gujarati (ગુજરાતી)"},
            {"code": "pa", "name": "Punjabi (ਪੰਜਾਬੀ)"}
        ],
        "translation_provider_status": overview.get("ai4bharat_translation", "unavailable"),
        "tts_provider_status": overview.get("ai4bharat_tts", "unavailable"),
        "asr_provider_status": overview.get("ai4bharat_asr", "unavailable"),
        "fallback_provider": "Gemma 4 12B / Browser Speech Engine"
    }
