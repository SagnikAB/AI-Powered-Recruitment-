import os
from sklearn.feature_extraction.text import TfidfVectorizer
from pinecone import Pinecone

vectorizer = TfidfVectorizer(max_features=512)

def get_embedding(text):
    try:
        return vectorizer.fit_transform([text]).toarray()[0].tolist()
    except:
        return [0.0] * 512

# INIT
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("resume-index")

def store_resume(id, text):
    vector = get_embedding(text)

    index.upsert([
        {
            "id": id,
            "values": vector,
            "metadata": {"text": text[:1000]}
        }
    ])

def match_resume(text):
    vector = get_embedding(text)

    result = index.query(
        vector=vector,
        top_k=1,
        include_metadata=True
    )

    if result and "matches" in result and len(result["matches"]) > 0:
        return result["matches"][0]["score"]

    return 0