from app.models.schemas import RiskAnalysis, GamificationState

def calculate_gamification(risk: RiskAnalysis, current_state: GamificationState) -> GamificationState:
    points = 10
    if risk.risk_level == "HIGH":
        points += 5
    elif risk.risk_level == "SAFE":
        points += 15

    current_state.points += points
    current_state.streak_days += 1
    current_state.level = max(1, current_state.points // 100 + 1)
    current_state.next_level_points = (current_state.level * 100) - current_state.points

    if risk.health_score >= 90 and "Clean Choice" not in current_state.badges:
        current_state.badges.append("Clean Choice")
    if current_state.streak_days >= 7 and "Weekly Warrior" not in current_state.badges:
        current_state.badges.append("Weekly Warrior")
    if current_state.points >= 500 and "Ingredient Detective" not in current_state.badges:
        current_state.badges.append("Ingredient Detective")

    return current_state
