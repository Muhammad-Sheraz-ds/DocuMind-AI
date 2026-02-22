"""
DocuMind AI — Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # App
    app_name: str = "DocuMind AI"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    port: int = 8000  # Railway uses PORT env var
    debug: bool = True

    # Groq API
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"

    # Embeddings (Free, local)
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"

    # Upload
    max_file_size_mb: int = 50
    upload_dir: str = "./data/uploads"

    # Database
    database_url: str = "sqlite:///./data/documind.db"

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 5
    rerank_top_k: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

# Ensure directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
