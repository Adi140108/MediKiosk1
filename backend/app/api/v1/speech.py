import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.ai.providers.provider_manager import AIProviderManager

logger = logging.getLogger("medikiosk.api.speech")
router = APIRouter(prefix="/speech", tags=["speech"])
provider_manager = AIProviderManager()

class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = "en"

class SynthesizeRequest(BaseModel):
    text: str
    language: str
    gender: Optional[str] = "female"

@router.post("/translate")
async def translate_text_endpoint(req: TranslateRequest):
    """
    Translates text between Indian languages and English.
    Returns normalized text, original text, and verification metadata.
    """
    try:
        result = await provider_manager.translate_text(
            text=req.text,
            target_lang=req.target_language,
            source_lang=req.source_language or "en"
        )
        return result
    except Exception as e:
        logger.error("Translation API error: %s", str(e))
        return {
            "original_text": req.text,
            "original_language": req.source_language or "en",
            "normalized_text": req.text,
            "normalized_language": req.source_language or "en",
            "translation_provider": "Error Fallback",
            "translation_status": "unavailable"
        }

@router.post("/synthesize")
async def synthesize_speech(req: SynthesizeRequest):
    """
    Generates text-to-speech audio via AI4Bharat IndicTTS or delegates to browser SpeechSynthesis.
    """
    ai4b_res = await provider_manager.ai4bharat.synthesize_speech(
        text=req.text,
        language=req.language,
        gender=req.gender or "female"
    )
    if ai4b_res:
        return {
            "status": "success",
            "audio_base64": ai4b_res.get("audio_base64"),
            "provider": "AI4Bharat IndicTTS"
        }

    lang_voices = {
        "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
        "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
        "pa": "pa-IN", "en": "en-IN"
    }
    return {
        "status": "ready_for_client_synthesis",
        "text": req.text,
        "language": req.language,
        "voice_locale": lang_voices.get(req.language, "en-IN"),
        "provider": "Browser Web Speech API"
    }

@router.post("/transcribe")
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Transcribes audio bytes via AI4Bharat IndicASR or signals client to use browser SpeechRecognition.
    """
    try:
        audio_bytes = await audio.read()
        res = await provider_manager.ai4bharat.transcribe_audio(audio_bytes, language=language)
        if res:
            return {
                "status": "success",
                "transcript": res.get("transcript"),
                "provider": "AI4Bharat IndicASR"
            }
    except Exception as e:
        logger.warning("Server ASR error: %s", str(e))

    return {
        "status": "client_fallback_required",
        "message": "Server ASR unavailable. Client browser SpeechRecognition recommended.",
        "provider": "Browser Web Speech API"
    }
