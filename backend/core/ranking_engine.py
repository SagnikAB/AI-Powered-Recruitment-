def get_rank(score):
    if score >= 85:
        return "Elite"
    elif score >= 70:
        return "Gold"
    elif score >= 50:
        return "Silver"
    else:
        return "Bronze"
