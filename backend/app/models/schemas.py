from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BBox(BaseModel):
    points: List[List[float]]

class TextBlock(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BBox
    is_harmful: bool = False
    harm_reason: Optional[str] = None
    category: Optional[str] = None

class RiskAnalysis(BaseModel):
    health_score: int = Field(..., ge=0, le=100)
    risk_level: str
    flagged_ingredients: List[str] = []
    allergens_detected: List[str] = []
    ultra_processed_score: float = Field(..., ge=0.0, le=1.0)
    summary: str

class Recommendation(BaseModel):
    product_name: str
    reason: str
    match_score: float
    image_url: Optional[str] = None
    category: str

class GamificationState(BaseModel):
    streak_days: int = 0
    points: int = 0
    badges: List[str] = []
    level: int = 1
    next_level_points: int = 100

class UserProfile(BaseModel):
    user_id: str = "anonymous"
    allergies: List[str] = []
    conditions: List[str] = []
    dietary: List[str] = []
    skin_type: Optional[str] = None

class ARScanResponse(BaseModel):
    status: str
    ocr_data: List[TextBlock] = []
    risk_analysis: RiskAnalysis
    recommendations: List[Recommendation] = []
    gamification: GamificationState
    ai_summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # 🔑 NEW: Product Identification Fields
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    context_product: Optional[str] = None
    conversation_id: Optional[str] = None
    user_profile: Optional[UserProfile] = None

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    sources: List[str] = []
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)