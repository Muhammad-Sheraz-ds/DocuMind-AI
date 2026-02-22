"""
DocuMind AI — LLM Service (Groq API)

Uses Groq's free tier with Llama 3.3 70B — fast inference, no cost.
Free tier: 14,400 requests/day, 6,000 tokens/min.
"""
from groq import Groq
from loguru import logger

from app.config import settings


SYSTEM_PROMPT = """You are DocuMind AI, an intelligent document assistant. Your role is to answer questions based ONLY on the provided context from the user's documents.

CRITICAL RULES:
1. ONLY answer based on the provided context. If the answer is not in the context, say "I couldn't find this information in your documents."
2. ALWAYS cite which source document and page the information came from.
3. Be concise and accurate. Use bullet points for clarity when appropriate.
4. If the context is ambiguous, acknowledge the ambiguity.
5. NEVER make up information or hallucinate facts not in the context.
6. Format your response in clear, readable markdown.

Response format:
- Start with a direct answer
- Support with specific details from the context
- End with source references"""


class LLMService:
    """Service for generating answers using Groq API (Llama 3.3 70B)."""

    def __init__(self):
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY not set! LLM features will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=settings.groq_api_key)
            logger.info(f"Groq client initialized (model: {settings.llm_model})")

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict],
        conversation_history: list[dict] = None,
    ) -> dict:
        """
        Generate an answer based on retrieved context chunks.

        Args:
            question: The user's question
            context_chunks: List of dicts with 'content', 'document', 'page', 'score'
            conversation_history: Optional previous messages for multi-turn

        Returns:
            dict with 'answer', 'tokens_used', 'model'
        """
        if not self.client:
            return {
                "answer": "⚠️ LLM service not configured. Please set GROQ_API_KEY in your .env file.",
                "tokens_used": 0,
                "model": "none",
            }

        # Build context string from retrieved chunks
        context_str = self._format_context(context_chunks)

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history if provided (for multi-turn)
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 turns

        # Add current question with context
        user_message = f"""Based on the following context from the user's documents, answer the question.

=== CONTEXT ===
{context_str}
=== END CONTEXT ===

Question: {question}

Remember: ONLY use information from the context above. Cite sources."""

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.1,  # Low temp for factual accuracy
                max_tokens=1024,
                top_p=0.9,
            )

            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            return {
                "answer": answer,
                "tokens_used": tokens_used,
                "model": settings.llm_model,
            }

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return {
                "answer": f"⚠️ Error generating answer: {str(e)}",
                "tokens_used": 0,
                "model": settings.llm_model,
            }

    def evaluate_faithfulness(
        self,
        question: str,
        answer: str,
        context: str,
    ) -> float:
        """
        Score how faithful the answer is to the context (0.0 - 1.0).
        Used in the evaluation harness.
        """
        if not self.client:
            return 0.0

        eval_prompt = f"""You are an evaluation judge. Score how faithful the answer is to the provided context.

Context: {context[:2000]}

Question: {question}

Answer: {answer}

Score the faithfulness from 0.0 to 1.0:
- 1.0 = Answer is completely supported by the context
- 0.5 = Answer is partially supported
- 0.0 = Answer contains information not in the context (hallucination)

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            score_text = response.choices[0].message.content.strip()
            return max(0.0, min(1.0, float(score_text)))
        except Exception:
            return 0.5  # Default to neutral on error

    def _format_context(self, chunks: list[dict]) -> str:
        """Format context chunks into a readable string."""
        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("document", "Unknown")
            page = chunk.get("page", "?")
            score = chunk.get("score", 0.0)
            content = chunk.get("content", "")
            parts.append(
                f"[Source {i}: {source}, Page {page} (relevance: {score:.2f})]\n{content}"
            )
        return "\n\n---\n\n".join(parts)


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get the singleton LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
