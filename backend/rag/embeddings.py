from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

@lru_cache(maxsize=1)
def _model():
    # Small + fast; good enough for FAQ
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _model()
    emb = model.encode(texts, normalize_embeddings=True)
    return emb.tolist() if isinstance(emb, np.ndarray) else emb
