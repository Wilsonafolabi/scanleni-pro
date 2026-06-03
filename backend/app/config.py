from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "scanleni-pro"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    OCR_CONFIDENCE_THRESHOLD: float = 0.45
    OCR_MAX_DIM: int = 1500
    
    LLM_PROVIDER: str = "openai"  # openai | gemini | claude | local
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_TOP_K: int = 4
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/scanleni"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
