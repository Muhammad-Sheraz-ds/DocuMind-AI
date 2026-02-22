"""
DocuMind AI — Embedding Service

Uses HuggingFace sentence-transformers (FREE, runs locally).
No API costs, no rate limits.
"""
from functools import lru_cache

from loguru import logger
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings using HuggingFace models."""

    _instance = None
    _model = None

    def __new__(cls):
        """Singleton: only load the model once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info(f"Embedding model loaded (dim={self._model.get_sentence_embedding_dimension()})")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed a batch of texts efficiently."""
        if not texts:
            return []

        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service."""
    return EmbeddingService()
