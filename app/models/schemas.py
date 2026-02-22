"""
DocuMind AI — Pydantic Schemas (Request/Response Models)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Document Schemas ───────────────────────────────────

class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: int
    filename: str
    file_type: str
    file_size: int
    num_chunks: int
    num_pages: int
    status: str
    message: str


class DocumentInfo(BaseModel):
    """Document information."""
    id: int
    filename: str
    file_type: str
    file_size: int
    num_chunks: int
    num_pages: int
    status: str
    upload_time: datetime

    model_config = {"from_attributes": True}


# ─── Query Schemas ──────────────────────────────────────

class AskRequest(BaseModel):
    """Request to ask a question."""
    question: str = Field(..., min_length=3, max_length=1000, description="The question to ask")
    document_id: Optional[int] = Field(None, description="Optional: limit search to a specific document")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")


class SourceChunk(BaseModel):
    """A source chunk from the document."""
    content: str
    document: str
    page: Optional[int] = None
    relevance_score: float
    chunk_id: str


class AskResponse(BaseModel):
    """Response to a question."""
    answer: str
    sources: list[SourceChunk]
    confidence: float = Field(ge=0.0, le=1.0)
    tokens_used: int
    latency_ms: float
    guardrail_flags: list[str] = []


# ─── Evaluation Schemas ─────────────────────────────────

class EvalQuestion(BaseModel):
    """A question-answer pair for evaluation."""
    question: str
    expected_answer: str
    document_id: Optional[int] = None


class EvalRequest(BaseModel):
    """Request to run evaluation."""
    test_name: str = "default"
    questions: list[EvalQuestion]


class EvalResultItem(BaseModel):
    """Result for a single evaluation question."""
    question: str
    expected_answer: str
    actual_answer: str
    retrieval_hit: bool
    faithfulness_score: float
    latency_ms: float


class EvalResponse(BaseModel):
    """Full evaluation report."""
    test_name: str
    total_questions: int
    retrieval_accuracy: float
    avg_faithfulness: float
    avg_latency_ms: float
    results: list[EvalResultItem]


# ─── Analytics Schemas ──────────────────────────────────

class AnalyticsResponse(BaseModel):
    """Analytics summary."""
    total_documents: int
    total_queries: int
    total_chunks: int
    avg_latency_ms: float
    avg_retrieval_score: float
    queries_today: int
    thumbs_up: int
    thumbs_down: int
    top_questions: list[dict]
    queries_over_time: list[dict]


# ─── Feedback Schema ────────────────────────────────────

class FeedbackRequest(BaseModel):
    """Feedback on a query response."""
    query_id: int
    feedback: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
