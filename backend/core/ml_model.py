from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Sample job description (you can later make dynamic)
JOB_DESCRIPTION = """
Looking for a software developer with skills in Python, Data Structures,
Algorithms, Machine Learning, SQL, and Web Development.
"""

def ml_score_resume(resume_text):
    docs = [JOB_DESCRIPTION, resume_text]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform(docs)

    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

    score = int(similarity * 100)

    return score