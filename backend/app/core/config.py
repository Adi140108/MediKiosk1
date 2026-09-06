import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "MediKiosk"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "medikiosk_super_secret_jwt_key_development_only_change_in_prod"

    # Cloudinary (Images only)
    CLOUDINARY_CLOUD_NAME: str = "q7tdtq1h"
    CLOUDINARY_API_KEY: str = "324984652911487"
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "MediKiosk"

    # Backblaze B2 (Medical Documents & PDFs only)
    B2_BUCKET_ID: str = "1ce157ad68537b21ad0d081a"
    B2_KEY_ID: str = "005c17d83b1dd8a0000000001"
    B2_KEY_NAME: str = "medikiosk-backend"
    B2_APPLICATION_KEY: str = ""
    B2_BUCKET_NAME: str = "medikiosk-documents"
    B2_ENDPOINT_URL: str = "https://s3.us-west-005.backblazeb2.com"

    # Firestore Database
    FIRESTORE_PROJECT_ID: str = "medikiosk1-cefd5"
    FIRESTORE_DATABASE_ID: str = "(default)"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    USE_MOCK_FIRESTORE_IN_DEV: bool = True  # Automatically fallback to in-memory store if Firestore credentials unavailable

    # Ollama & Gemma 4 12B
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMMA_MODEL: str = "gemma4:12b"
    GEMMA_TEMPERATURE: float = 0.2
    GEMMA_REQUEST_TIMEOUT: int = 45

    # AI4Bharat & Multilingual
    AI4BHARAT_API_KEY: str = ""
    AI4BHARAT_BASE_URL: str = "https://api.ai4bharat.org"
    AI4BHARAT_MODE: str = "auto"  # "local", "api", or "auto" (tries local repo/weights first, then API, then Gemma)
    LOCAL_INDICTRANS_PATH: str = "./models/indictrans2"
    LOCAL_INDIC_DEVICE: str = "auto"  # "cuda", "cpu", "auto"
    LOCAL_INDIC_COMPUTE_TYPE: str = "auto"  # "int8", "float16", "float32", "auto"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"]

    # Tesseract OCR & Local Tessdata
    TESSERACT_CMD_PATH: Optional[str] = None  # e.g., "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    TESSDATA_PATH: str = "./models/tessdata"
    
    # File Size Limits
    MAX_IMAGE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_DOCUMENT_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Socratic Intake Configuration
    MAX_INTAKE_QUESTIONS: int = 12
    MIN_INTAKE_QUESTIONS: int = 4
    CONFIDENCE_THRESHOLD_STOP: float = 0.85

    # External Integrations (ABDM, ABHA, DigiLocker)
    ABHA_MOCK_MODE: bool = True
    DIGILOCKER_MOCK_MODE: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
