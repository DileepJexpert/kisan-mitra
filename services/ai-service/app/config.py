from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    db_url: str = "postgresql://admin:password@localhost:5432/kisanmitra"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # AI Models
    ollama_host: str = "http://localhost:11434"
    ollama_model_default: str = "qwen3:7b"
    chroma_host: str = "http://localhost:8000"

    # External AI APIs
    claude_api_key: str = ""
    gemini_api_key: str = ""
    bhashini_api_key: str = ""
    sarvam_api_key: str = ""

    # App Config
    log_level: str = "INFO"
    app_env: str = "development"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
