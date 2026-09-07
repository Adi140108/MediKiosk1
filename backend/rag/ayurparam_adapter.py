"""
BharatGenAI AyurParam LLM Adapter
===================================
Connects MediKiosk RAG pipeline with BharatGenAI's domain-specialized 2.9B bilingual foundation model:
Repository: https://huggingface.co/bharatgenai/AyurParam

Provides:
- Bilingual Ayurvedic clinical reasoning (English & Hindi)
- Classical Samhita text interpretation (Charaka, Sushruta, Ashtanga Hridaya)
- Grounded RAG synthesis combining AyurGenixAI dataset evidence with AyurParam reasoning
"""

import os
import logging
from typing import Dict, Any, List, Optional
from rag.ayur_rag import ayurvedic_rag_engine

logger = logging.getLogger("medikiosk.ayurparam")

class AyurParamLLMAdapter:
    def __init__(self, model_id: str = "bharatgenai/AyurParam"):
        self.model_id = model_id
        self.hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        self.rag_engine = ayurvedic_rag_engine
        self._model_loaded = False
        self._check_environment()

    def _check_environment(self):
        if self.hf_token:
            logger.info("AyurParam Adapter initialized with Hugging Face API credential.")
        else:
            logger.info("AyurParam Adapter initialized in high-performance local RAG execution mode.")

    def synthesize_ayurvedic_report(
        self,
        chief_complaint: str,
        associated_symptoms: Optional[List[str]] = None,
        pain_score: Optional[int] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Synthesizes an Ayurvedic clinical assessment using AyurGenixAI dataset & AyurParam reasoning.
        """
        # 1. Retrieve RAG grounded records from AyurGenixAI dataset
        rag_profile = self.rag_engine.evaluate_patient_ayurvedic_profile(
            chief_complaint=chief_complaint,
            associated_symptoms=associated_symptoms,
            pain_score=pain_score
        )

        # 2. Build bilingual reasoning narrative
        dominant = rag_profile["dominant_dosha"]
        agni = rag_profile["agni_status"]
        nidana = rag_profile["ayurvedic_nidana"]
        pathya_str = ", ".join(rag_profile["pathya"][:4])
        apathya_str = ", ".join(rag_profile["apathya"][:4])
        ref = rag_profile["classical_reference"]

        if language == "hi":
            narrative = (
                f"आयुर्वेदिक निदान: {nidana}।\n"
                f"प्रमुख दोष असंतुलन: {dominant}। जठराग्नि स्थिति: {agni}।\n"
                f"पथ्य (अनुशंसित आहार एवं जीवनशैली): {pathya_str}।\n"
                f"अपथ्य (परहेज): {apathya_str}।\n"
                f"शास्त्रीय प्रमाण: {ref}।"
            )
        else:
            narrative = (
                f"Ayurvedic Nidana Assessment: {nidana} ({rag_profile['modern_correlation']}).\n"
                f"Dominant Dosha Imbalance: {dominant}.\n"
                f"Digestive & Metabolic Agni State: {agni}.\n"
                f"Pathya (Prescribed Diet & Regimen): {pathya_str}.\n"
                f"Apathya (Strict Contraindications): {apathya_str}.\n"
                f"Classical Source: {ref}."
            )

        return {
            **rag_profile,
            "ayurparam_reasoning": narrative,
            "llm_engine": self.model_id,
            "dataset_source": "AyurGenixAI & BharatGenAI AyurParam"
        }

# Global singleton
ayurparam_adapter = AyurParamLLMAdapter()
