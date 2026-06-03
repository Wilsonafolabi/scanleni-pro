from app.models.schemas import RiskAnalysis, Recommendation

def find_alternatives(risk: RiskAnalysis, category: str = "general") -> list[Recommendation]:
    if risk.risk_level == "SAFE":
        return []
    return [
        Recommendation(product_name="PureGlow Serum", reason="Fragrance-free, paraben-free, niacinamide-rich.", match_score=0.92, category="skincare"),
        Recommendation(product_name="CleanBite Snacks", reason="No HFCS, whole grain, low sodium.", match_score=0.88, category="food"),
        Recommendation(product_name="EcoHome Cleaner", reason="Plant-based, no phthalates, biodegradable.", match_score=0.85, category="household")
    ]
