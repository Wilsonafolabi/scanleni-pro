from pydantic import BaseModel, Field
from typing import List, Optional

class BBox(BaseModel):
    points: List[List[float]]

class TextBlock(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BBox
    is_harmful: bool = False
    harm_reason: Optional[str] = None

class AIAnalysis(BaseModel):
    summary: str
    safety_status: str
    chat_response: str
    retrieved_context: List[str] = []

class GamificationUpdate(BaseModel):
    health_score: int = Field(ge=0, le=100)
    points_earned: int
    badges_unlocked: List[str]
    streak_days: int

class Recommendation(BaseModel):
    product_name: str
    reason: str
    image_url: Optional[str] = None

class ARScanResponse(BaseModel):
    status: str
    ocr_data: List[TextBlock] = []
    ai_analysis: AIAnalysis
    gamification: GamificationUpdate
    recommendations: List[Recommendation] = []
