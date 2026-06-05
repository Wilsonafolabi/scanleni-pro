import httpx
import json
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from app.services.ocr_service import ocr_service
from app.services.gamification_service import calculate_gamification
from app.services.recommendation_service import find_alternatives
from app.models.schemas import ARScanResponse, RiskAnalysis, GamificationState
from app.config import settings

router = APIRouter(prefix="/scan", tags=["Scanning"])
logger = logging.getLogger(__name__)

HARMFUL_KEYWORDS = [
    "paraben", "sulfate", "phthalate", "formaldehyde", "fragrance", "parfum",
    "high fructose corn syrup", "red 40", "yellow 5", "sodium benzoate", "msg",
    "alcohol denat", "mineral oil", "retinol"
]

async def identify_product(ocr_text: str) -> dict:
    """Uses the LLM to identify the product name, brand, and category from OCR text."""
    if not settings.LLM_API_KEY or not settings.LLM_BASE_URL:
        return {"product_name": None, "brand": None, "category": None}
    
    prompt = f"""You are a product identification AI. 
Based on the following OCR text extracted from a product label, identify:
1. The exact product name (e.g., "Nutella Hazelnut Spread")
2. The brand (e.g., "Ferrero")
3. The product category (e.g., "Food & Beverages", "Skincare", "Household")

OCR Text: "{ocr_text}"

Return ONLY a valid JSON object with keys: "product_name", "brand", "category". 
If you cannot identify something, use null.
Example: {{"product_name": "CeraVe Moisturizing Cream", "brand": "CeraVe", "category": "Skincare"}}"""

    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 150,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{settings.LLM_BASE_URL}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception as e:
        logger.warning("Product identification failed: %s", e)
        return {"product_name": None, "brand": None, "category": None}

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

    # 🔑 NEW: Identify Product using LLM
    ocr_text_blob = " ".join([block.text for block in ocr_data])
    product_info = await identify_product(ocr_text_blob)

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

    # 4. Build RiskAnalysis
    risk = RiskAnalysis(
        health_score=health_score,
        risk_level=risk_level,
        flagged_ingredients=flagged,
        allergens_detected=[],
        ultra_processed_score=0.0,
        summary=f"Detected {len(flagged)} flagged ingredients. Health score: {health_score}/100."
    )

    # 5. Run Gamification & Recommendation Engines
    gamification = calculate_gamification(risk, GamificationState())
    recommendations = find_alternatives(risk)

    logger.info("Scan complete. Product: %s | Risk: %s | Score: %d", 
                product_info.get("product_name"), risk_level, health_score)

    # 6. Return unified AR-ready payload with Product ID
    return ARScanResponse(
        status="success",
        ocr_data=ocr_data,
        risk_analysis=risk,
        recommendations=recommendations,
        gamification=gamification,
        ai_summary=risk.summary,
        product_name=product_info.get("product_name"),
        brand=product_info.get("brand"),
        category=product_info.get("category")
    )