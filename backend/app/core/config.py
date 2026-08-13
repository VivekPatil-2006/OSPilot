import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "OSPilot Backend"
    DEBUG: bool = True
    
    # Gemini Cloud API Configuration
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # Ollama Local Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_CHAT_MODEL: str = "gemma3:latest"
    FALLBACK_CHAT_MODELS: list[str] = ["qwen3:8b", "qwen2.5-coder:7b"]
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # MongoDB Compass Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "OSPilot"

    # SQLite Database Fallback
    DATABASE_URL: str = "sqlite:///./ospilot.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
