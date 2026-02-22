"""
DocuMind AI — Evaluation Harness Service

Run golden Q&A test sets against the RAG pipeline.
Measures: retrieval accuracy, answer faithfulness, latency.
"""
import json
import time
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.orm import Session

from app.models.database import EvaluationResult
from app.models.schemas import EvalQuestion, EvalResultItem
from app.services.retrieval import get_retrieval_service
from app.services.llm import get_llm_service


class EvaluationService:
    """Service for evaluating RAG pipeline quality."""

    def __init__(self):
        self.retrieval = get_retrieval_service()
        self.llm = get_llm_service()

    def run_evaluation(
        self,
        test_name: str,
        questions: list[EvalQuestion],
        collection_name: str,
        db: Session,
    ) -> dict:
        """
        Run a full evaluation against the RAG pipeline.

        For each question:
        1. Retrieve chunks (check if expected answer is in retrieved context)
        2. Generate answer
        3. Score faithfulness (using LLM as judge)
        4. Measure latency
        """
        results = []
        total_retrieval_hits = 0
        total_faithfulness = 0.0
        total_latency = 0.0

        logger.info(f"Running evaluation '{test_name}' with {len(questions)} questions")

        for i, q in enumerate(questions):
            start_time = time.time()

            # 1. Retrieve context
            search_results = self.retrieval.search(
                query=q.question,
                collection_name=collection_name,
                top_k=5,
            )

            # 2. Check if expected answer content is in retrieved chunks
            retrieved_text = " ".join([r["content"] for r in search_results])
            retrieval_hit = self._check_retrieval_hit(
                q.expected_answer, retrieved_text
            )

            # 3. Generate answer
            context_chunks = [
                {
                    "content": r["content"],
                    "document": r["document"],
                    "page": r.get("page"),
                    "score": r["score"],
                }
                for r in search_results
            ]
            llm_result = self.llm.generate_answer(q.question, context_chunks)
            actual_answer = llm_result["answer"]

            # 4. Score faithfulness
            faithfulness = self.llm.evaluate_faithfulness(
                q.question, actual_answer, retrieved_text
            )

            # 5. Measure latency
            latency_ms = (time.time() - start_time) * 1000

            # Track totals
            if retrieval_hit:
                total_retrieval_hits += 1
            total_faithfulness += faithfulness
            total_latency += latency_ms

            results.append(EvalResultItem(
                question=q.question,
                expected_answer=q.expected_answer,
                actual_answer=actual_answer,
                retrieval_hit=retrieval_hit,
                faithfulness_score=faithfulness,
                latency_ms=round(latency_ms, 1),
            ))

            logger.info(
                f"  [{i+1}/{len(questions)}] "
                f"retrieval={'✓' if retrieval_hit else '✗'} "
                f"faithfulness={faithfulness:.2f} "
                f"latency={latency_ms:.0f}ms"
            )

        # Calculate aggregates
        n = len(questions)
        retrieval_accuracy = total_retrieval_hits / n if n > 0 else 0
        avg_faithfulness = total_faithfulness / n if n > 0 else 0
        avg_latency = total_latency / n if n > 0 else 0

        # Save to database
        eval_record = EvaluationResult(
            test_name=test_name,
            total_questions=n,
            correct_answers=total_retrieval_hits,
            retrieval_accuracy=round(retrieval_accuracy, 4),
            answer_faithfulness=round(avg_faithfulness, 4),
            avg_latency_ms=round(avg_latency, 1),
            details=json.dumps([r.model_dump() for r in results]),
            run_time=datetime.now(timezone.utc),
        )
        db.add(eval_record)
        db.commit()
        db.refresh(eval_record)

        summary = {
            "id": eval_record.id,
            "test_name": test_name,
            "total_questions": n,
            "retrieval_accuracy": round(retrieval_accuracy, 4),
            "avg_faithfulness": round(avg_faithfulness, 4),
            "avg_latency_ms": round(avg_latency, 1),
            "results": results,
        }

        logger.info(
            f"Evaluation '{test_name}' complete: "
            f"retrieval={retrieval_accuracy:.1%}, "
            f"faithfulness={avg_faithfulness:.2f}, "
            f"latency={avg_latency:.0f}ms"
        )

        return summary

    def _check_retrieval_hit(
        self,
        expected_answer: str,
        retrieved_text: str,
    ) -> bool:
        """
        Check if key information from the expected answer appears
        in the retrieved context. Uses keyword overlap.
        """
        # Tokenize and compare
        expected_keywords = set(expected_answer.lower().split())
        retrieved_lower = retrieved_text.lower()

        # Remove common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "up", "about", "into", "through", "during", "before", "after",
            "and", "but", "or", "nor", "not", "so", "yet", "both",
            "this", "that", "these", "those", "it", "its",
        }
        meaningful_keywords = expected_keywords - stop_words

        if not meaningful_keywords:
            return True

        # Check how many keywords appear in retrieved text
        found = sum(1 for kw in meaningful_keywords if kw in retrieved_lower)
        overlap_ratio = found / len(meaningful_keywords)

        # Consider it a hit if >50% of keywords are found
        return overlap_ratio > 0.5

    def get_evaluation_history(self, db: Session) -> list[dict]:
        """Get all past evaluation results."""
        results = db.query(EvaluationResult).order_by(
            EvaluationResult.run_time.desc()
        ).all()

        return [
            {
                "id": r.id,
                "test_name": r.test_name,
                "total_questions": r.total_questions,
                "retrieval_accuracy": r.retrieval_accuracy,
                "answer_faithfulness": r.answer_faithfulness,
                "avg_latency_ms": r.avg_latency_ms,
                "run_time": r.run_time.isoformat(),
            }
            for r in results
        ]


# Singleton
_eval_service = None


def get_evaluation_service() -> EvaluationService:
    """Get the singleton evaluation service."""
    global _eval_service
    if _eval_service is None:
        _eval_service = EvaluationService()
    return _eval_service
