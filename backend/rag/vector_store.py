from typing import List, Dict, Any, Tuple
from rag.embeddings import LightweightEmbeddings

CLINICAL_KNOWLEDGE_DOCUMENTS = [
    {
        "id": "kb_headache_01",
        "category": "neurology",
        "content": "Headache red flags: sudden thunderclap onset, neck stiffness, high fever, altered mental status, visual disturbance, projectile vomiting. Route to Neurology/Emergency.",
        "metadata": {"department": "neurology", "red_flag": "CRITICAL"}
    },
    {
        "id": "kb_chest_pain_01",
        "category": "cardiology",
        "content": "Chest pain radiating to left arm, neck, jaw, accompanied by diaphoresis, shortness of breath. Indicates acute coronary syndrome. Route to Cardiology/Emergency.",
        "metadata": {"department": "cardiology", "red_flag": "CRITICAL"}
    },
    {
        "id": "kb_abdominal_pain_01",
        "category": "gastroenterology",
        "content": "Abdominal pain related to food intake, digestion issues, heartburn, epigastric tenderness, bowel changes. Assess Agni, Ahara, and Mala.",
        "metadata": {"department": "gastroenterology", "ayurvedic": ["AGNI", "AHARA", "MALA"]}
    },
    {
        "id": "kb_ayurvedic_agni",
        "category": "ayush",
        "content": "Agni assessment: Tikshnagni (sharp, excessive hunger), Mandagni (sluggish, heaviness after eating), Vishamagni (irregular digestion), Samagni (balanced digestion).",
        "metadata": {"ayurvedic_domain": "AGNI"}
    },
    {
        "id": "kb_orthopedics_01",
        "category": "orthopedics",
        "content": "Joint pain, knee swelling, morning stiffness, trauma, bone fractures, restricted mobility. Route to Orthopedics.",
        "metadata": {"department": "orthopedics"}
    }
]

class InMemoryVectorStore:
    def __init__(self):
        self.embeddings = LightweightEmbeddings()
        self.documents: List[Dict[str, Any]] = list(CLINICAL_KNOWLEDGE_DOCUMENTS)
        self.doc_vectors = [self.embeddings.embed_query(doc["content"]) for doc in self.documents]

    def similarity_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vec = self.embeddings.embed_query(query)
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for doc, doc_vec in zip(self.documents, self.doc_vectors):
            dot_product = sum(a * b for a, b in zip(query_vec, doc_vec))
            scored.append((dot_product, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:top_k]]
