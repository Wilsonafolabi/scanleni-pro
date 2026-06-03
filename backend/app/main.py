from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scan, chat
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(scan.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
