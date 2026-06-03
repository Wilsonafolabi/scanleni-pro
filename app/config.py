from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ocr_device: str = "cpu"
    ocr_confidence_threshold: float = 0.75
    log_level: str = "info"

    class Config:
        env_file = ".env.local"

settings = Settings()
