"""
vector_store.py  –  Resume embedding store with Pinecone + semantic search
==========================================================================
Embeddings : sentence-transformers  (all-MiniLM-L6-v2, 384-d)
             Falls back to TF-IDF 512-d if sentence-transformers is missing.
Store      : Pinecone  (optional – disabled gracefully if API key is absent)
"""

from __future__ import annotations
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Embedding backend ─────────────────────────────────────────────────────────
_st_model = None
EMBEDDING_DIM = 512          # TF-IDF fallback dimension

try:
    from sentence_transformers import SentenceTransformer
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    EMBEDDING_DIM = 384      # MiniLM output size
    print("sentence-transformers loaded for vector_store")
except Exception as _e:
    print(f"sentence-transformers unavailable ({_e}); TF-IDF embeddings active")


# ── Pinecone (optional) ───────────────────────────────────────────────────────
_pinecone_enabled = False
_index = None

try:
    from pinecone import Pinecone
    _api_key = os.getenv("PINECONE_API_KEY")
    if _api_key:
        pc = Pinecone(api_key=_api_key)
        _index = pc.Index("resume-index")
        _pinecone_enabled = True
        print("Pinecone connected")
    else:
        print("PINECONE_API_KEY not set; vector scoring disabled")
except Exception as e:
    print(f"Pinecone init failed ({e}); vector scoring disabled")


# ── Local TF-IDF corpus (fallback when sentence-transformers is absent) ───────
_corpus: list[str] = []
_tfidf_vectorizer = TfidfVectorizer(max_features=EMBEDDING_DIM, stop_words="english")
_corpus_matrix = None


def _refit_tfidf(texts: list[str]):
    global _corpus_matrix, _tfidf_vectorizer
    _tfidf_vectorizer = TfidfVectorizer(max_features=EMBEDDING_DIM, stop_words="english")
    _corpus_matrix = _tfidf_vectorizer.fit_transform(texts)


# ── Public helpers ────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    """
    Return a fixed-length embedding vector for *text*.

    Uses sentence-transformers if available, otherwise TF-IDF.
    """
    if _st_model is not None:
        try:
            emb = _st_model.encode(text, convert_to_numpy=True)
            return emb.tolist()
        except Exception as e:
            print(f"ST encode error: {e}")

    # TF-IDF fallback
    try:
        if not _corpus:
            _refit_tfidf([text])
            return _corpus_matrix.toarray()[0].tolist()  # type: ignore[union-attr]
        vec = _tfidf_vectorizer.transform([text])
        return vec.toarray()[0].tolist()
    except Exception:
        return [0.0] * EMBEDDING_DIM


def store_resume(doc_id: str, text: str):
    """
    Store a resume's embedding in Pinecone (if connected) and
    keep the raw text in the local corpus for TF-IDF fallback.
    """
    _corpus.append(text)
    if _st_model is None:
        _refit_tfidf(_corpus)   # keep TF-IDF corpus fresh

    if not _pinecone_enabled:
        return

    try:
        vector = get_embedding(text)
        _index.upsert([{                          # type: ignore[union-attr]
            "id":     doc_id,
            "values": vector,
            "metadata": {"text": text[:1000]},
        }])
    except Exception as e:
        print(f"Pinecone upsert error: {e}")


def match_resume(text: str) -> float:
    """
    Return cosine similarity (0-1) between *text* and the best
    matching stored resume.

    Falls back to 0.0 when Pinecone is unavailable.
    """
    if not _pinecone_enabled:
        return 0.0

    try:
        vector = get_embedding(text)
        result = _index.query(              # type: ignore[union-attr]
            vector=vector, top_k=1, include_metadata=True
        )
        if result and result.get("matches"):
            return float(result["matches"][0]["score"])
    except Exception as e:
        print(f"Pinecone query error: {e}")

    return 0.0


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Direct cosine similarity between two texts — useful for scoring
    a resume against a job description without Pinecone.

    Uses sentence-transformers when available, TF-IDF otherwise.
    """
    emb_a = np.array(get_embedding(text_a))
    emb_b = np.array(get_embedding(text_b))

    denom = (np.dot(emb_a, emb_a) ** 0.5) * (np.dot(emb_b, emb_b) ** 0.5)
    if denom == 0:
        return 0.0
    return float(max(0.0, np.dot(emb_a, emb_b) / denom))
