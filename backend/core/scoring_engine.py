from core.skill_engine import extract_skills
from core.ml_model import ml_score_resume

def score_resume(text):
    total_skills = [
        "python", "java", "c", "sql",
        "machine learning", "data structures",
        "algorithms", "flask", "django"
    ]

    found_skills = extract_skills(text)

    matched = [s for s in total_skills if s in found_skills]
    missing = [s for s in total_skills if s not in found_skills]

    # 🔥 ML SCORE
    ml_score = ml_score_resume(text)

    # Combine scores
    keyword_score = int((len(matched) / len(total_skills)) * 100)

    final_score = int((0.6 * ml_score) + (0.4 * keyword_score))

    return final_score, matched, missing