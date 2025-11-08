import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from .embeddings import embed_texts

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = os.getenv("QDRANT_COLLECTION", "clinic_faq")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def ensure_collection(vec_size: int = 384):
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=qm.VectorParams(size=vec_size, distance=qm.Distance.COSINE),
    )

def upsert_faq(items: list[dict]):
    texts = [i["text"] for i in items]
    vecs = embed_texts(texts)
    points = [
        qm.PointStruct(id=idx, vector=vec, payload=items[idx])
        for idx, vec in enumerate(vecs)
    ]
    client.upsert(collection_name=COLLECTION, points=points)

def search(query: str, top_k: int = 5):
    qv = embed_texts([query])[0]
    res = client.search(
        collection_name=COLLECTION,
        query_vector=qv,
        limit=top_k,
        with_payload=True
    )
    return [(r.payload.get("text", ""), r.payload.get("source", "")) for r in res]
