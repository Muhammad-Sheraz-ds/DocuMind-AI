"""
DocuMind AI — FastAPI Application Entry Point

Run with: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.models.database import init_db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info(f"{settings.app_name} shutting down")


app = FastAPI(
    title=settings.app_name,
    description=(
        "📚 Enterprise RAG Platform — Upload documents, ask questions with "
        "citations, evaluate accuracy, and track analytics.\n\n"
        "**Features:**\n"
        "- 📄 Multi-format document ingestion (PDF, DOCX, TXT, CSV)\n"
        "- 🔍 Hybrid search (semantic + BM25 + reranking)\n"
        "- 💬 AI answers with source citations\n"
        "- 🛡️ Guardrails (prompt injection detection, PII flagging)\n"
        "- 📊 Evaluation harness with golden Q&A test sets\n"
        "- 📈 Usage analytics dashboard\n\n"
        "**Powered by:** Groq (Llama 3.3 70B) + HuggingFace Embeddings + ChromaDB"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }


@app.get("/health", tags=["Health"])
async def detailed_health():
    """Detailed health check with service status."""
    from app.services.llm import get_llm_service
    from app.services.retrieval import get_retrieval_service

    llm = get_llm_service()
    retrieval = get_retrieval_service()

    return {
        "status": "healthy",
        "services": {
            "llm": "connected" if llm.client else "not_configured",
            "vector_store": "connected",
            "database": "connected",
        },
        "config": {
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "top_k": settings.top_k,
        },
    }
