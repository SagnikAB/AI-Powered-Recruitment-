import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_SKILLS = [
    "python", "java", "c++", "javascript",
    "react", "node", "flask", "django",
    "sql", "mongodb", "docker", "aws"
]

AI_KEYWORDS = [
    "machine learning", "deep learning",
    "nlp", "tensorflow", "pytorch"
]


def score_resume(text: str, job_description: str = "") -> tuple:
    text = text.lower()
    score = 0
    matched = []
    missing = []

    # ── If job description provided: extract keywords from it ────────────────
    if job_description and job_description.strip():
        jd_lower = job_description.lower()

        # TF-IDF similarity bonus (0-30 points)
        try:
            docs = [jd_lower, text]
            vec = TfidfVectorizer(stop_words="english")
            tfidf = vec.fit_transform(docs)
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            score += int(sim * 30)
        except Exception:
            pass

        # Extract words from JD to use as dynamic skill set
        jd_words = re.findall(r'\b[a-z][a-z+#.]{2,}\b', jd_lower)
        dynamic_skills = list(set(jd_words) - {
            "and","the","with","for","our","are","you","that","this",
            "have","will","can","from","able","must","has","been","also"
        })

        for skill in dynamic_skills[:20]:   # cap at 20
            if skill in text:
                score += 2
                if skill not in matched:
                    matched.append(skill)
            else:
                if skill not in missing:
                    missing.append(skill)

    else:
        # ── Default keyword scoring ──────────────────────────────────────────
        for skill in DEFAULT_SKILLS:
            if skill in text:
                score += 3
                matched.append(skill)
            else:
                missing.append(skill)

        for word in AI_KEYWORDS:
            if word in text:
                score += 6
                matched.append(word)

    # ── Universal bonus points ────────────────────────────────────────────────
    if "project" in text:
        score += 10
    if "intern" in text or "experience" in text:
        score += 10
    if "achieved" in text or "improved" in text or "reduced" in text:
        score += 8

    numbers = re.findall(r'\d+', text)
    score += min(len(numbers) * 2, 10)

    if len(text.split()) > 300:
        score += 10

    score = max(0, min(score, 100))
    return score, matched, missing