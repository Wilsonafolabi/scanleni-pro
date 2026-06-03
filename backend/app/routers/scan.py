from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from app.services.ocr_service import ocr_service
from app.services.gamification_service import calculate_gamification
from app.services.recommendation_service import find_alternatives
from app.models.schemas import ARScanResponse, RiskAnalysis, GamificationState
import logging

router = APIRouter(prefix="/scan", tags=["Scanning"])
logger = logging.getLogger(__name__)

# Lightweight fallback keywords for immediate flagging.
# The AI/RAG engine will replace this with dynamic, profile-aware analysis in Phase 3.
HARMFUL_KEYWORDS = [
    "paraben", "sulfate", "phthalate", "formaldehyde", "fragrance", "parfum",
    "high fructose corn syrup", "red 40", "yellow 5", "sodium benzoate", "msg",
    "alcohol denat", "mineral oil", "retinol"
]

@router.post("/", response_model=ARScanResponse)
async def scan_product(file: UploadFile = File(...), conditions: str = Query(default="")):
    logger.info("Scan request received: %s", file.filename)
    contents = await file.read()

    # 1. Run OCR Pipeline
    try:
        ocr_data = ocr_service.extract(contents)
    except Exception as e:
        logger.error("OCR processing failed: %s", str(e))
        raise HTTPException(status_code=500, detail="OCR processing failed. Please try a clearer image.")

    if not ocr_data:
        raise HTTPException(status_code=400, detail="No text detected in the uploaded image.")

    # 2. Flag harmful ingredients & attach reasons
    flagged = []
    for block in ocr_data:
        text_lower = block.text.lower()
        if any(keyword in text_lower for keyword in HARMFUL_KEYWORDS):
            block.is_harmful = True
            block.harm_reason = "Contains potentially harmful or controversial ingredient."
            flagged.append(block.text)

    # 3. Calculate health score & risk level
    health_score = max(0, 100 - (len(flagged) * 15))
    if health_score > 80:
        risk_level = "SAFE"
    elif health_score > 50:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    # 4. Build RiskAnalysis (ALL required schema fields included)
    risk = RiskAnalysis(
        health_score=health_score,
        risk_level=risk_level,
        flagged_ingredients=flagged,
        allergens_detected=[],          # Required by schema. AI engine will populate later.
        ultra_processed_score=0.0,      # Required by schema. AI engine will calculate later.
        summary=f"Detected {len(flagged)} flagged ingredients. Health score: {health_score}/100."
    )

    # 5. Run Gamification & Recommendation Engines
    gamification = calculate_gamification(risk, GamificationState())
    recommendations = find_alternatives(risk)

    logger.info("Scan complete. Risk: %s, Score: %d, Flagged: %d", risk_level, health_score, len(flagged))

    # 6. Return unified AR-ready payload
    return ARScanResponse(
        status="success",
        ocr_data=ocr_data,
        risk_analysis=risk,
        recommendations=recommendations,
        gamification=gamification,
        ai_summary=risk.summary
    )