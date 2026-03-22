def get_rank(score):
    if score >= 90:
        return "Elite 🏆"
    elif score >= 75:
        return "Gold ⭐⭐⭐"
    elif score >= 60:
        return "Silver ⭐⭐"
    else:
        return "Bronze ⭐"