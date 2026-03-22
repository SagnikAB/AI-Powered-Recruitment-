def recommend_skills(text):
    text = text.lower()
    missing = []

    if "machine learning" not in text:
        missing.append("Add Machine Learning")

    if "project" not in text:
        missing.append("Add Projects")

    if "intern" not in text:
        missing.append("Add Experience")

    return missing