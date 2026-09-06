from app.ai.gemma.client import GemmaClient
from app.ai.gemma.prompts.ayurvedic_questioning import AYURVEDIC_DOMAIN_TEMPLATES
from app.ai.gemma.prompts.socratic_prompts import SOCRATIC_QUESTION_PROMPT
from app.ai.gemma.prompts.summary_prompts import LIVE_SUMMARY_PROMPT, DRAFT_PHYSICIAN_SUMMARY_PROMPT
from app.ai.gemma.prompts.extraction_prompts import DOCUMENT_EXTRACTION_PROMPT

__all__ = [
    "GemmaClient",
    "AYURVEDIC_DOMAIN_TEMPLATES",
    "SOCRATIC_QUESTION_PROMPT",
    "LIVE_SUMMARY_PROMPT",
    "DRAFT_PHYSICIAN_SUMMARY_PROMPT",
    "DOCUMENT_EXTRACTION_PROMPT"
]
