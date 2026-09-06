from enum import Enum

class FallbackPolicy(str, Enum):
    AI4BHARAT_FIRST_THEN_GEMMA = "AI4BHARAT_FIRST_THEN_GEMMA"
    DIRECT_GEMMA = "DIRECT_GEMMA"
    DEV_MOCK_FALLBACK = "DEV_MOCK_FALLBACK"

# Capability definitions: Never pretend Gemma does ASR/TTS if it's text-only
CAPABILITY_SUPPORT = {
    "translation": ["ai4bharat", "gemma4:12b", "dev_mock"],
    "asr": ["ai4bharat", "browser_speech_api", "dev_mock"],
    "tts": ["ai4bharat", "browser_speech_synthesis", "dev_mock"]
}
