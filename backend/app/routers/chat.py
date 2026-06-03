from fastapi import APIRouter, HTTPException
from app.services.rag_service import rag_service
from app.models.schemas import ChatRequest, ChatResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Assistant"])

@router.post("/", response_model=ChatResponse)
async def chat_with_ai(req: ChatRequest):
    try:
        logger.info("Chat request: conv_id=%s, msg=%s", req.conversation_id, req.message[:50])
        response = await rag_service.chat(req)
        return response
    except Exception as e:
        logger.error("Chat endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail="AI chat service failed. Please try again.")