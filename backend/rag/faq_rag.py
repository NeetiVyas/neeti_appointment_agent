# backend/rag/faq_rag.py
"""
This file connects everything:
- Loads FAQs from data/clinic_info.json
- Generates embeddings for them using SentenceTransformer
- Uploads to Qdrant Cloud
- Finds the best answer using similarity search
"""

import os
import json
import numpy as np
from .embeddings import SentenceEmbedding
from . import vector_store

DATA_PATH = "data/clinic_info.json"

# Step 1: Load FAQs
if os.path.exists(DATA_PATH):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        FAQS = json.load(f)
else:
    FAQS = []

# Step 2: Create embeddings for FAQ questions + answers
embedder = SentenceEmbedding()
DOCS = [f"{f['question']} {f['answer']}" for f in FAQS]
if DOCS:
    VECTORS = embedder.embed_texts(DOCS)
else:
    VECTORS = np.array([])

# Step 3: Try uploading to Qdrant Cloud (optional)
QDRANT_AVAILABLE = False
if len(DOCS) > 0:
    try:
        client = vector_store.get_qdrant_client()
        vector_store.create_collection(client, embedder.dim)
        payloads = [{"question": f["question"], "answer": f["answer"]} for f in FAQS]
        vector_store.upsert_embeddings(client, VECTORS, payloads)
        QDRANT_AVAILABLE = True
        print("✅ Uploaded FAQ embeddings to Qdrant Cloud.")
    except Exception as e:
        print("⚠️ Qdrant not configured or upload failed:", e)
        QDRANT_AVAILABLE = False


# Step 4: Function to answer questions
def answer_faq(query, top_k=3):
    """
    Returns top similar FAQs from Qdrant Cloud (if available),
    otherwise does local cosine similarity.
    """
    if len(DOCS) == 0:
        return [{"answer": "No FAQs found."}]

    q_vec = embedder.embed_text(query)

    if QDRANT_AVAILABLE:
        try:
            results = vector_store.search_embeddings(client, q_vec, top_k=top_k)
            return [{"question": r["payload"]["question"], "answer": r["payload"]["answer"], "score": r["score"]} for r in results]
        except Exception as e:
            print("⚠️ Qdrant search failed, using local search:", e)

    # Local fallback: cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(q_vec.reshape(1, -1), VECTORS).flatten()
    top_idx = sims.argsort()[-top_k:][::-1]
    results = []
    for i in top_idx:
        results.append({
            "question": FAQS[i]["question"],
            "answer": FAQS[i]["answer"],
            "score": float(sims[i])
        })
    return results

def answer_faq_best(query):
    """
    Returns only the best answer (highest score).
    """
    res = answer_faq(query, top_k=1)
    return res[0]["answer"] if res else "Sorry, I couldn't find an answer."
