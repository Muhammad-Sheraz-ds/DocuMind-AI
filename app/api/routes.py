"""
DocuMind AI — API Routes (FastAPI)

Endpoints: /upload, /ask, /documents, /evaluate, /analytics, /feedback
"""
import json
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.config import settings
from app.models.database import Document, QueryLog, get_db
from app.models.schemas import (
    DocumentUploadResponse, DocumentInfo, AskRequest, AskResponse,
    SourceChunk, EvalRequest, EvalResponse, AnalyticsResponse,
    FeedbackRequest,
)
from app.services.ingestion import IngestionService
from app.services.retrieval import get_retrieval_service
from app.services.llm import get_llm_service
from app.services.guardrails import get_guardrails_service
from app.services.evaluation import get_evaluation_service

router = APIRouter()

# Default collection for all documents
DEFAULT_COLLECTION = "documind_docs"


# ═══════════════════════════════════════════════
# DOCUMENT UPLOAD
# ═══════════════════════════════════════════════

@router.post("/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document (PDF, DOCX, TXT, CSV, MD).
    The document will be parsed, chunked, embedded, and indexed.
    """
    ingestion = IngestionService()

    # Validate file
    content = await file.read()
    is_valid, msg = ingestion.validate_file(file.filename, len(content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # Save file
    filepath = await ingestion.save_uploaded_file(file.filename, content)

    # Extract text
    try:
        text, num_pages = ingestion.extract_text(filepath)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this file.")

    # Chunk the text
    chunks = ingestion.chunk_text(text, file.filename, num_pages)

    # Index chunks into vector store
    retrieval = get_retrieval_service()
    num_indexed = retrieval.index_chunks(chunks, DEFAULT_COLLECTION)

    # Save document record to database
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "unknown"
    doc = Document(
        filename=file.filename,
        file_type=ext,
        file_size=len(content),
        num_chunks=num_indexed,
        num_pages=num_pages,
        status="ready",
        collection_name=DEFAULT_COLLECTION,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"Document uploaded: {file.filename} → {num_indexed} chunks")

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        num_chunks=doc.num_chunks,
        num_pages=doc.num_pages,
        status=doc.status,
        message=f"Successfully processed: {num_indexed} chunks indexed.",
    )


# ═══════════════════════════════════════════════
# ASK QUESTIONS
# ═══════════════════════════════════════════════

@router.post("/ask", response_model=AskResponse, tags=["Chat"])
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question about your uploaded documents.
    Uses hybrid search (semantic + keyword) + Groq LLM for answers.
    """
    start_time = time.time()

    # Input guardrails
    guardrails = get_guardrails_service()
    is_safe, input_flags = guardrails.check_input(request.question)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected by safety filter: {', '.join(input_flags)}"
        )

    # Determine document filter
    doc_filter = None
    if request.document_id:
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if doc:
            doc_filter = doc.filename

    # Retrieve relevant chunks
    retrieval = get_retrieval_service()
    search_results = retrieval.search(
        query=request.question,
        collection_name=DEFAULT_COLLECTION,
        top_k=request.top_k,
        document_filter=doc_filter,
    )

    if not search_results:
        return AskResponse(
            answer="I couldn't find any relevant information in your documents. Please upload documents first or rephrase your question.",
            sources=[],
            confidence=0.0,
            tokens_used=0,
            latency_ms=round((time.time() - start_time) * 1000, 1),
            guardrail_flags=[],
        )

    # Format context for LLM
    context_chunks = [
        {
            "content": r["content"],
            "document": r["document"],
            "page": r.get("page"),
            "score": r["score"],
        }
        for r in search_results
    ]

    # Generate answer via Groq
    llm = get_llm_service()
    llm_result = llm.generate_answer(request.question, context_chunks)

    # Output guardrails
    cleaned_answer, output_flags = guardrails.check_output(
        llm_result["answer"], context_chunks
    )

    # Calculate confidence (avg retrieval score)
    avg_score = sum(r["score"] for r in search_results) / len(search_results)

    latency_ms = round((time.time() - start_time) * 1000, 1)

    # Build source chunks
    sources = [
        SourceChunk(
            content=r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
            document=r["document"],
            page=r.get("page"),
            relevance_score=round(r["score"], 4),
            chunk_id=r["chunk_id"],
        )
        for r in search_results
    ]

    # Log query
    query_log = QueryLog(
        question=request.question,
        answer=cleaned_answer,
        sources=json.dumps([s.model_dump() for s in sources[:3]]),
        retrieval_score=round(avg_score, 4),
        latency_ms=latency_ms,
        tokens_used=llm_result["tokens_used"],
        document_id=request.document_id,
    )
    db.add(query_log)
    db.commit()
    db.refresh(query_log)

    return AskResponse(
        answer=cleaned_answer,
        sources=sources,
        confidence=round(min(1.0, avg_score), 4),
        tokens_used=llm_result["tokens_used"],
        latency_ms=latency_ms,
        guardrail_flags=input_flags + output_flags,
    )


# ═══════════════════════════════════════════════
# DOCUMENTS LIST
# ═══════════════════════════════════════════════

@router.get("/documents", response_model=list[DocumentInfo], tags=["Documents"])
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.upload_time.desc()).all()
    return docs


@router.delete("/documents/{doc_id}", tags=["Documents"])
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' deleted", "id": doc_id}


# ═══════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════

@router.post("/evaluate", response_model=EvalResponse, tags=["Evaluation"])
async def run_evaluation(
    request: EvalRequest,
    db: Session = Depends(get_db),
):
    """
    Run evaluation against the RAG pipeline with a set of Q&A pairs.
    Measures retrieval accuracy, answer faithfulness, and latency.
    """
    eval_service = get_evaluation_service()
    result = eval_service.run_evaluation(
        test_name=request.test_name,
        questions=request.questions,
        collection_name=DEFAULT_COLLECTION,
        db=db,
    )
    return EvalResponse(**result)


@router.get("/evaluate/history", tags=["Evaluation"])
async def evaluation_history(db: Session = Depends(get_db)):
    """Get past evaluation results."""
    eval_service = get_evaluation_service()
    return eval_service.get_evaluation_history(db)


# ═══════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════

@router.get("/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics(db: Session = Depends(get_db)):
    """Get usage analytics and statistics."""
    # Total counts
    total_docs = db.query(Document).count()
    total_queries = db.query(QueryLog).count()
    total_chunks = db.query(func.sum(Document.num_chunks)).scalar() or 0

    # Averages
    avg_latency = db.query(func.avg(QueryLog.latency_ms)).scalar() or 0.0
    avg_retrieval = db.query(func.avg(QueryLog.retrieval_score)).scalar() or 0.0

    # Today's queries
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    queries_today = db.query(QueryLog).filter(QueryLog.timestamp >= today).count()

    # Feedback counts
    thumbs_up = db.query(QueryLog).filter(QueryLog.feedback == "thumbs_up").count()
    thumbs_down = db.query(QueryLog).filter(QueryLog.feedback == "thumbs_down").count()

    # Top 5 most asked questions (by similarity — simplified as exact match)
    top_questions_raw = (
        db.query(QueryLog.question, func.count(QueryLog.id).label("count"))
        .group_by(QueryLog.question)
        .order_by(func.count(QueryLog.id).desc())
        .limit(5)
        .all()
    )
    top_questions = [{"question": q, "count": c} for q, c in top_questions_raw]

    # Queries per day (last 7 days)
    queries_over_time = []
    for i in range(7):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = db.query(QueryLog).filter(
            QueryLog.timestamp >= day,
            QueryLog.timestamp < next_day,
        ).count()
        queries_over_time.append({
            "date": day.strftime("%Y-%m-%d"),
            "count": count,
        })
    queries_over_time.reverse()

    return AnalyticsResponse(
        total_documents=total_docs,
        total_queries=total_queries,
        total_chunks=total_chunks,
        avg_latency_ms=round(avg_latency, 1),
        avg_retrieval_score=round(avg_retrieval, 4),
        queries_today=queries_today,
        thumbs_up=thumbs_up,
        thumbs_down=thumbs_down,
        top_questions=top_questions,
        queries_over_time=queries_over_time,
    )


# ═══════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════

@router.post("/feedback", tags=["Feedback"])
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """Submit thumbs up/down feedback on a query response."""
    query = db.query(QueryLog).filter(QueryLog.id == request.query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    query.feedback = request.feedback
    db.commit()
    return {"message": "Feedback recorded", "query_id": request.query_id}
