from app.schemas import AIAnalysis, Recommendation

def find_alternatives(ai_analysis: AIAnalysis) -> list[Recommendation]:
    if ai_analysis.safety_status == "SAFE":
        return []
    return [
        Recommendation(product_name="Organic Alternative Brand", reason="Free from flagged additives.", image_url=None),
        Recommendation(product_name="Local Clean Label Product", reason="Uses natural preservatives.", image_url=None)
    ]
