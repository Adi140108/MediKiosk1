from typing import List, Dict, Any
from rag.retriever import RAGRetriever

class RAGContextBuilder:
    def __init__(self, retriever: RAGRetriever = None):
        self.retriever = retriever or RAGRetriever()

    def build_context_string(self, query: str) -> str:
        docs = self.retriever.retrieve(query)
        if not docs:
            return ""
        context_snippets = [f"[{doc.get('category', 'general').upper()}]: {doc.get('content')}" for doc in docs]
        return "\n".join(context_snippets)
