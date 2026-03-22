def recommend_skills(missing_skills):
    recommendations = []

    for skill in missing_skills:
        recommendations.append(f"Improve your {skill} skills")

    return recommendations