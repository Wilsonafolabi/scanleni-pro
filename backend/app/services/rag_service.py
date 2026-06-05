import httpx
import uuid
import logging
from typing import List, Optional, Dict
from app.models.schemas import ChatRequest, ChatResponse
from app.services.vector_store import vector_store
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, provider: str, api_key: Optional[str], base_url: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 30.0

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key or not self.api_key.startswith("gsk_"):
            return "⚠️ AI service not configured. Please add a valid API key to your .env file."

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        # 🔑 Lower max_tokens to 250 to physically prevent long, rambling responses
        payload = {"model": self.model, "messages": messages, "temperature": 0.7, "max_tokens": 250, "top_p": 0.9}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            return "⏳ AI response timed out. Please try again."
        except httpx.HTTPStatusError as e:
            logger.error("LLM API error: %s - %s", e.response.status_code, e.response.text)
            return f"⚠️ AI service error ({e.response.status_code}). Check API key or rate limits."
        except Exception as e:
            logger.error("Unexpected LLM error: %s", e)
            return "⚠️ AI service temporarily unavailable. Please try again later."

class RAGService:
    def __init__(self):
        self.llm = LLMClient(settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_BASE_URL, settings.LLM_MODEL)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.max_memory_turns = 6
        
        # 🔑 ULTRA-STRICT, BREVITY-FOCUSED PROMPT
        self.system_prompt = """You are ScanLeni AI, a helpful, concise, and natural conversational assistant.

STRICT RULES:
1. BE BRIEF. If the user says "ok", "thanks", or asks a simple question, reply with a short, natural 1-2 sentence response. Do NOT write long paragraphs, lists, or unsolicited analyses.
2. NEVER use templates, bullet points, or headers like "Product Guess:", "Ingredient Breakdown:", or "Safety Note:". Just talk like a normal person.
3. Only analyze ingredients or the product if the user explicitly asks about them. Otherwise, just answer their direct question.
4. Silently understand OCR typos (e.g., "Monthol" = Menthol, "Contoins" = Contains) but do not point them out unless it directly answers the user's question.
5. Never hallucinate ingredients. If the scan is unclear, just say it's unclear.
6. Match the user's energy. If they are brief, you be brief."""

    async def chat(self, req: ChatRequest) -> ChatResponse:
        conv_id = req.conversation_id or str(uuid.uuid4())
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []

        context_results = vector_store.search(req.message, top_k=settings.VECTOR_TOP_K)
        context_texts = [text for text, _, _ in context_results]
        context_str = "\n".join(context_texts) if context_texts else "No specific safety data retrieved."

        profile_ctx = ""
        if req.user_profile:
            parts = []
            if req.user_profile.conditions: parts.append(f"Conditions: {', '.join(req.user_profile.conditions)}")
            if req.user_profile.allergies: parts.append(f"Allergies: {', '.join(req.user_profile.allergies)}")
            if req.user_profile.dietary: parts.append(f"Dietary: {', '.join(req.user_profile.dietary)}")
            if req.user_profile.skin_type: parts.append(f"Skin Type: {req.user_profile.skin_type}")
            profile_ctx = " | ".join(parts) if parts else ""

        raw_ctx = req.context_product or ""
        cleaned_ctx = raw_ctx.replace("Scanned ingredients: ", "").strip()
        product_section = f"Scanned OCR Output: {cleaned_ctx}" if cleaned_ctx else ""
        
        system_context = "\n".join(filter(None, [f"Retrieved Safety Knowledge:\n{context_str}", product_section, f"User Profile: {profile_ctx}"]))

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": system_context},
            *self.conversations[conv_id][-self.max_memory_turns:],
            {"role": "user", "content": req.message}
        ]

        reply = await self.llm.generate(messages)
        self.conversations[conv_id].append({"role": "user", "content": req.message})
        self.conversations[conv_id].append({"role": "assistant", "content": reply})
        if len(self.conversations[conv_id]) > self.max_memory_turns * 2:
            self.conversations[conv_id] = self.conversations[conv_id][-self.max_memory_turns * 2:]

        return ChatResponse(
            conversation_id=conv_id,
            reply=reply,
            sources=context_texts,
            confidence=0.85 if context_texts else 0.60
        )

rag_service = RAGService()