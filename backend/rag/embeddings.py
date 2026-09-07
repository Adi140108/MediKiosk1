import math
import re
import zlib
from typing import List

class LightweightEmbeddings:
    """
    Deterministic clinical term frequency & n-gram embedding generator
    for local zero-dependency RAG execution.
    """
    def embed_query(self, text: str) -> List[float]:
        tokens = re.findall(r'\w+', text.lower())
        vec = [0.0] * 64
        for token in tokens:
            h = zlib.crc32(token.encode('utf-8')) % 64
            vec[h] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm if norm > 0 else 0.0 for x in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]
