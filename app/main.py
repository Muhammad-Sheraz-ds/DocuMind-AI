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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api/v1")


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
        },
        "config": {
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "top_k": settings.top_k,
        },
    }


# ─── Serve React Frontend (for HuggingFace Spaces / Docker) ───
if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_frontend(request: Request, full_path: str):
        """Serve React frontend for all non-API routes."""
        # If it's a static file that exists, serve it
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html (SPA routing)
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/", tags=["Health"])
    async def health_check():
        """Health check (no frontend build found)."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "1.0.0",
            "message": "API is running. Frontend not built — run 'cd frontend && npm run build'",
        }

