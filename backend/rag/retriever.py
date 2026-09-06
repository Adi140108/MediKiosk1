from typing import List, Dict, Any
from rag.vector_store import InMemoryVectorStore

class RAGRetriever:
    def __init__(self, vector_store: InMemoryVectorStore = None):
        self.vector_store = vector_store or InMemoryVectorStore()

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.vector_store.similarity_search(query, top_k=top_k)
