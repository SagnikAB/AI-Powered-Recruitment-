import re

def score_resume(text):
    text = text.lower()
    score = 0

    skills = ["python","java","c++","javascript","react","node","flask","sql","mongodb","docker","aws"]

    for s in skills:
        if s in text:
            score += 3

    ai = ["machine learning","deep learning","nlp","tensorflow","pytorch"]

    for a in ai:
        if a in text:
            score += 6

    if "project" in text:
        score += 10

    if "intern" in text or "experience" in text:
        score += 10

    if "achieved" in text or "improved" in text:
        score += 8

    numbers = re.findall(r'\d+', text)
    score += min(len(numbers) * 2, 10)

    if len(text.split()) > 300:
        score += 10

    return min(score, 100)