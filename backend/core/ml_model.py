"""
ml_model.py  –  Semantic resume ↔ job-description scoring
==========================================================
Primary : sentence-transformers  (all-MiniLM-L6-v2)
Fallback : TF-IDF cosine similarity  (no extra deps beyond sklearn)

Returns
-------
ml_score_resume(resume_text, job_description="") -> int   (0-100)
"""

from __future__ import annotations
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Try to load sentence-transformers once at import time ─────────────────────
_st_model = None

try:
    from sentence_transformers import SentenceTransformer
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ sentence-transformers loaded (semantic scoring active)")
except Exception as _e:
    print(f"⚠️  sentence-transformers unavailable ({_e}) — falling back to TF-IDF")


# ── Default JD used when caller passes nothing ────────────────────────────────
_DEFAULT_JD = (
    "Looking for a software developer with skills in Python, Data Structures, "
    "Algorithms, Machine Learning, SQL, and Web Development."
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _semantic_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity via sentence embeddings (0-1)."""
    emb = _st_model.encode([text_a, text_b], convert_to_numpy=True)
    num = float((emb[0] @ emb[1]))
    denom = (float((emb[0] @ emb[0])) ** 0.5) * (float((emb[1] @ emb[1])) ** 0.5)
    return max(0.0, num / denom) if denom else 0.0


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity via TF-IDF (0-1)."""
    try:
        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform([text_a, text_b])
        return float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
    except Exception:
        return 0.0


def _keyword_boost(resume_text: str, job_description: str) -> int:
    """
    Extra points (0-20) for JD keywords found in the resume.
    Rewards hard-skill matches that pure cosine similarity can miss.
    """
    jd_words = set(re.findall(r'\b[a-z][a-z+#.]{2,}\b', job_description.lower()))
    stopwords = {
        "and", "the", "with", "for", "our", "are", "you", "that",
        "this", "have", "will", "can", "from", "able", "must",
        "has", "been", "also", "who", "their", "your"
    }
    keywords = jd_words - stopwords
    if not keywords:
        return 0

    resume_lower = resume_text.lower()
    hits = sum(1 for kw in keywords if kw in resume_lower)
    ratio = hits / len(keywords)
    return int(ratio * 20)          # up to 20 bonus points


# ── Public API ────────────────────────────────────────────────────────────────

def ml_score_resume(resume_text: str, job_description: str = "") -> int:
    """
    Score a resume against a job description.

    Parameters
    ----------
    resume_text     : raw text extracted from the resume
    job_description : optional JD; falls back to _DEFAULT_JD if empty

    Returns
    -------
    int  0-100
    """
    jd = job_description.strip() if job_description and job_description.strip() else _DEFAULT_JD

    # ── Similarity score (0-80 points) ────────────────────────────────────────
    if _st_model is not None:
        sim = _semantic_similarity(resume_text, jd)
    else:
        sim = _tfidf_similarity(resume_text, jd)

    base_score = int(sim * 80)

    # ── Keyword boost (0-20 points) ───────────────────────────────────────────
    boost = _keyword_boost(resume_text, jd)

    total = min(base_score + boost, 100)
    return total