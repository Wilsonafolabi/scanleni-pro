from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import rag_service
import json

router = APIRouter(prefix="/agent", tags=["AI Agent"])

@router.post("/", response_model=ChatResponse)
async def run_agent(req: ChatRequest):
    intent_prompt = f"""Classify this request into one category ONLY:
    - skincare_routine
    - product_comparison
    - health_analysis
    - general_qa
    Request: "{req.message}"
    Return ONLY the category name."""
    
    intent_resp = await rag_service.llm.generate([{"role": "system", "content": intent_prompt}])
    category = intent_resp.strip().lower()

    if "comparison" in category:
        steps = "1. Identify products\n2. Fetch profiles\n3. Calculate diff scores\n4. Output recommendation"
    elif "routine" in category:
        steps = "1. Identify skin type/budget\n2. Match products to profile\n3. Order steps (cleanse→treat→moisturize)\n4. Add warnings"
    elif "health" in category:
        steps = "1. Scan history analysis\n2. Exposure trend check\n3. Predict risk\n4. Suggest intervention"
    else:
        steps = "1. Retrieve safety context\n2. Personalize to profile\n3. Generate structured answer\n4. Provide next steps"

    plan_msg = f"Agent Plan ({category}): [{steps}]\nExecute step-by-step and output final recommendation."
    req.message = f"{req.message}\n\n{plan_msg}"
    
    return await rag_service.chat(req)