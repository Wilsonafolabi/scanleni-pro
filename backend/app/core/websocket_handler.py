import asyncio
import time
from fastapi import WebSocket
from app.services.ocr_service import ocr_service
from app.services.predictive_engine import track_exposure, get_user_trends
from app.services.graph_store import graph_store
import logging

logger = logging.getLogger(__name__)

class ScanWebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.debounce_seconds = 1.2
        self.last_scan_time: dict[str, float] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WS connected: %s", user_id)

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        self.last_scan_time.pop(user_id, None)
        logger.info("WS disconnected: %s", user_id)

    async def send_json(self, user_id: str, data: dict):
        if ws := self.active_connections.get(user_id):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(user_id)

    async def process_frame(self, user_id: str, image_bytes: bytes, profile: dict):
        now = time.time()
        last = self.last_scan_time.get(user_id, 0)
        if now - last < self.debounce_seconds:
            return

        self.last_scan_time[user_id] = now
        try:
            ocr_data = ocr_service.extract(image_bytes)
            harmful_count = sum(1 for b in ocr_data if b.is_harmful)
            health_score = max(0, 100 - (harmful_count * 12))

            # Predictive & Graph enrichment
            track_exposure(user_id, ocr_data)
            trends = get_user_trends(user_id)
            graph_insights = {}
            for b in ocr_data:
                if b.is_harmful:
                    related = graph_store.get_related(b.text.lower().replace(" ", "_"), depth=1)
                    if related:
                        graph_insights[b.text] = related

            await self.send_json(user_id, {
                "type": "scan_update",
                "ocr_data": [b.model_dump() for b in ocr_data],
                "health_score": health_score,
                "trends": trends,
                "graph_insights": graph_insights,
                "timestamp": now
            })
        except Exception as e:
            logger.error("WS OCR failed for %s: %s", user_id, e)
            await self.send_json(user_id, {"type": "error", "message": "Processing failed. Hold steady."})

ws_manager = ScanWebSocketManager()