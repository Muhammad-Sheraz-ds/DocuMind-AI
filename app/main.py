"""
DocuMind AI — FastAPI Application Entry Point

Run with: uvicorn app.main:app --reload
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from app.config import settings
from app.models.database import init_db
from app.api.routes import router

# Path to built React frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="")


from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
async def detailed_health():
    """Detailed health check with service status."""
    from app.services.llm import get_llm_service
    llm = get_llm_service()
    return {
        "status": "healthy",
        "services": {
            "llm": "connected" if llm.client else "not_configured",
            "vector_store": "connected",
            "database": "connected",
        }
    }

