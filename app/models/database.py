"""
DocuMind AI — Database Models (SQLAlchemy)
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    Float, DateTime, Boolean, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

from app.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    """Uploaded document metadata."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    num_chunks = Column(Integer, default=0)
    num_pages = Column(Integer, default=0)
    upload_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="processing")  # processing, ready, error
    collection_name = Column(String(255), nullable=False)

    queries = relationship("QueryLog", back_populates="document")


class QueryLog(Base):
    """Log of all user queries and responses."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, default="[]")  # JSON list of source chunks
    retrieval_score = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    feedback = Column(String(10), default=None)  # thumbs_up, thumbs_down, None
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    document = relationship("Document", back_populates="queries")


class EvaluationResult(Base):
    """Evaluation harness results."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(255), nullable=False)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    retrieval_accuracy = Column(Float, default=0.0)
    answer_faithfulness = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    details = Column(Text, default="{}")  # JSON with per-question results
    run_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
