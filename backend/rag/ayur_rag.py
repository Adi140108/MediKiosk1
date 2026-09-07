"""
Ayurvedic RAG Engine for MediKiosk
====================================
Integrates:
- AyurGenixAI Dataset (Kaggle: kagglekirti123/ayurgenixai-ayurvedic-dataset)
- BharatGenAI AyurParam LLM & Samhita Corpus (Hugging Face: bharatgenai/AyurParam)

Performs dense similarity + entity-driven sparse retrieval across Ayurvedic clinical parameters:
- Nidana & Dosha Imbalance Mapping
- Agni Status & Dhatwagnimandya
- Affected Dhatu & Srotas
- Classical Formulations & Herbs
- Pathya (Recommended Diet & Lifestyle) & Apathya (Contraindications)
- Classical Samhita Citations (Charaka, Sushruta, Ashtanga Hridaya)
"""

import math
import re
from typing import List, Dict, Any, Optional
from rag.ayurvedic_knowledge_base import (
    AYURVEDIC_KNOWLEDGE_RECORDS,
    AYURVEDIC_DATASET_METADATA
)
from rag.embeddings import LightweightEmbeddings

class AyurvedicRAGEngine:
    def __init__(self, records: Optional[List[Dict[str, Any]]] = None):
        self.embeddings = LightweightEmbeddings()
        self.records = records or list(AYURVEDIC_KNOWLEDGE_RECORDS)
        self.metadata = dict(AYURVEDIC_DATASET_METADATA)
        
        # Build dense index
        self.record_texts = [
            f"{r['ayurvedic_nidana']} {r['modern_correlation']} {' '.join(r.get('keywords', []))} {r['clinical_presentation']} {r['dominant_dosha']}"
            for r in self.records
        ]
        self.record_vectors = self.embeddings.embed_documents(self.record_texts)

    def retrieve_records(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: Combines keyword overlap score + dense cosine similarity
        """
        if not query or not query.strip():
            return self.records[:top_k]

        q_lower = query.lower().strip()
        q_vec = self.embeddings.embed_query(q_lower)
        q_tokens = set(re.findall(r'\w+', q_lower))

        scored: List[tuple] = []
        for doc, doc_vec in zip(self.records, self.record_vectors):
            # 1. Cosine dense similarity
            dense_score = sum(a * b for a, b in zip(q_vec, doc_vec))

            # 2. Sparse keyword matching on clinical entities & keywords
            doc_blob = f"{doc.get('ayurvedic_nidana', '')} {doc.get('modern_correlation', '')} {doc.get('category', '')} {' '.join(doc.get('keywords', []))}".lower()
            keyword_score = 0.0

            for tok in q_tokens:
                if len(tok) > 2 and tok in doc_blob:
                    keyword_score += 2.0

            for kw in doc.get("keywords", []):
                kw_lower = kw.lower()
                if kw_lower in q_lower:
                    keyword_score += 4.0

            # Direct symptom matching boosts
            if ("joint" in q_lower or "knee" in q_lower or "जोड़" in q_lower) and doc.get("category") == "orthopedics":
                keyword_score += 5.0
            if ("chest" in q_lower or "heart" in q_lower or "सीने" in q_lower) and doc.get("category") == "cardiology":
                keyword_score += 5.0
            if ("headache" in q_lower or "migraine" in q_lower or "सिरदर्द" in q_lower) and doc.get("category") == "neurology":
                keyword_score += 5.0
            if ("stomach" in q_lower or "acidity" in q_lower or "reflux" in q_lower or "पेट" in q_lower) and doc.get("category") == "gastroenterology":
                keyword_score += 5.0

            # Multi-symptom boost (e.g. chest + joint)
            if "chest" in q_lower and "joint" in q_lower and "multi" in doc.get("id", ""):
                keyword_score += 8.0
            if "छाती" in q_lower and "जोड़" in q_lower and "multi" in doc.get("id", ""):
                keyword_score += 8.0

            total_score = (dense_score * 2.0) + keyword_score
            scored.append((total_score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]

    def evaluate_patient_ayurvedic_profile(
        self,
        chief_complaint: str,
        associated_symptoms: Optional[List[str]] = None,
        pain_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a patient's clinical presentation using the AyurGenixAI & AyurParam dataset.
        Returns a complete structured Ayurvedic clinical synthesis.
        """
        assoc_str = " ".join(associated_symptoms) if associated_symptoms else ""
        query_text = f"{chief_complaint} {assoc_str}".strip()

        matched_docs = self.retrieve_records(query_text, top_k=2)
        primary_doc = matched_docs[0] if matched_docs else self.records[0]

        # Combine Pathya and Apathya from retrieved records
        combined_pathya = list(primary_doc.get("pathya", []))
        combined_apathya = list(primary_doc.get("apathya", []))
        combined_herbs = list(primary_doc.get("classical_herbs_formulations", []))

        if len(matched_docs) > 1:
            for item in matched_docs[1].get("pathya", []):
                if item not in combined_pathya:
                    combined_pathya.append(item)
            for item in matched_docs[1].get("apathya", []):
                if item not in combined_apathya:
                    combined_apathya.append(item)
            for item in matched_docs[1].get("classical_herbs_formulations", []):
                if item not in combined_herbs:
                    combined_herbs.append(item)

        # Build comprehensive structured assessment
        return {
            "dominant_dosha": primary_doc.get("dominant_dosha", "Vata-Pitta"),
            "prakriti_vikriti": primary_doc.get("prakriti_vikriti", "Vata-Pitta Srotorodha"),
            "agni_status": primary_doc.get("agni_status", "Vishama Agni (Irregular Metabolism)"),
            "dhatu_affected": primary_doc.get("dhatu_affected", ["Rasa", "Asthi"]),
            "srotas_affected": primary_doc.get("srotas_affected", ["Rasavaha Srotas"]),
            "ayurvedic_nidana": primary_doc.get("ayurvedic_nidana", "Vataja Vikara"),
            "modern_correlation": primary_doc.get("modern_correlation", "Clinical Presentation"),
            "dietary_guidelines": combined_pathya[:5],
            "pathya": combined_pathya[:6],
            "apathya": combined_apathya[:6],
            "classical_herbs": combined_herbs[:5],
            "classical_reference": primary_doc.get("classical_reference", "Charaka Samhita, Chikitsa Sthana"),
            "dataset_provenance": {
                "dataset_name": self.metadata["dataset_name"],
                "dataset_source": self.metadata["dataset_source"],
                "dataset_url": self.metadata["dataset_url"],
                "llm_model": self.metadata["llm_model"],
                "llm_source": self.metadata["llm_source"],
                "llm_url": self.metadata["llm_url"]
            },
            "rag_citations": [
                {
                    "id": d["id"],
                    "nidana": d["ayurvedic_nidana"],
                    "modern": d["modern_correlation"],
                    "reference": d["classical_reference"]
                }
                for d in matched_docs
            ]
        }

    def get_dataset_info(self) -> Dict[str, Any]:
        """Returns metadata about the imported AyurGenixAI dataset and AyurParam LLM."""
        return {
            **self.metadata,
            "indexed_records_count": len(self.records),
            "status": "LOADED_AND_READY"
        }

# Global singleton engine
ayurvedic_rag_engine = AyurvedicRAGEngine()
