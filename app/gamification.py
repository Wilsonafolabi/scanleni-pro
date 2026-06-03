from app.schemas import AIAnalysis, GamificationUpdate

def calculate_gamification(ai_analysis: AIAnalysis, user_current_streak: int = 5) -> GamificationUpdate:
    base_score = 100
    points = 10
    if ai_analysis.safety_status == "DANGER":
        base_score -= 40
        points += 5
    elif ai_analysis.safety_status == "WARNING":
        base_score -= 20
        points += 10
        
    badges = []
    if ai_analysis.safety_status == "SAFE":
        badges.append("Clean Choice")
    if user_current_streak >= 7:
        badges.append("Weekly Warrior")

    return GamificationUpdate(
        health_score=max(0, base_score),
        points_earned=points,
        badges_unlocked=badges,
        streak_days=user_current_streak
    )
