from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.ocr_engine import ocr_engine
from app.ai_engine import analyze_ingredients
from app.gamification import calculate_gamification
from app.recommender import find_alternatives
from app.schemas import ARScanResponse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="scanleni-pro Master Gateway", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "master-gateway"}

@app.post("/scan", response_model=ARScanResponse)
async def scan_product(file: UploadFile = File(...)):
    logger.info("Received scan request: %s", file.filename)
    contents = await file.read()
    try:
        ocr_data = ocr_engine.process_image(contents)
    except Exception as e:
        logger.error("OCR failed: %s", str(e))
        raise HTTPException(status_code=500, detail="OCR processing failed")
        
    if not ocr_data:
        raise HTTPException(status_code=400, detail="No text detected in image.")

    ai_analysis = analyze_ingredients(ocr_data)
    gamification = calculate_gamification(ai_analysis)
    recommendations = find_alternatives(ai_analysis)

    return ARScanResponse(
        status="success",
        ocr_data=ocr_data,
        ai_analysis=ai_analysis,
        gamification=gamification,
        recommendations=recommendations
    )
