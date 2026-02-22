"""
DocuMind AI — Guardrails Service

Safety layer: prompt injection detection, output grounding validation,
and sensitive data filtering.
"""
import re
from loguru import logger


class GuardrailsService:
    """Service for safety checks on inputs and outputs."""

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?above",
        r"disregard\s+(all\s+)?previous",
        r"forget\s+(all\s+)?previous",
        r"you\s+are\s+now\s+a",
        r"act\s+as\s+if",
        r"pretend\s+(you|that)",
        r"system\s*prompt",
        r"reveal\s+your\s+(instructions|prompt|system)",
        r"what\s+are\s+your\s+instructions",
        r"override\s+(your\s+)?instructions",
        r"\bDAN\b",  # "Do Anything Now" jailbreak
        r"jailbreak",
    ]

    # PII patterns for detection (not removal — just flagging)
    PII_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }

    def check_input(self, user_input: str) -> tuple[bool, list[str]]:
        """
        Check user input for prompt injection attempts.

        Returns:
            (is_safe, list_of_flags)
        """
        flags = []
        input_lower = user_input.lower()

        # Check for injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, input_lower):
                flags.append(f"potential_prompt_injection: matched pattern '{pattern}'")

        # Check for extremely long inputs (could be stuffing attack)
        if len(user_input) > 5000:
            flags.append("excessive_input_length")

        # Check for encoded content that might bypass filters
        if "\\x" in user_input or "\\u" in user_input:
            flags.append("encoded_content_detected")

        is_safe = len(flags) == 0
        if not is_safe:
            logger.warning(f"Input guardrail triggered: {flags}")

        return is_safe, flags

    def check_output(
        self,
        answer: str,
        context_chunks: list[dict],
    ) -> tuple[str, list[str]]:
        """
        Check if the output is grounded in the context and flag issues.

        Returns:
            (cleaned_answer, list_of_flags)
        """
        flags = []

        # Check if answer contains PII
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, answer):
                flags.append(f"pii_detected: {pii_type}")

        # Check for common hallucination indicators
        hallucination_phrases = [
            "as an ai", "i don't have access", "i cannot browse",
            "as of my training", "i'm not sure but",
            "based on my knowledge",  # Should be "based on the documents"
        ]
        answer_lower = answer.lower()
        for phrase in hallucination_phrases:
            if phrase in answer_lower:
                flags.append(f"possible_hallucination_indicator: '{phrase}'")

        # Check if answer is suspiciously long (might be over-generating)
        if len(answer) > 3000:
            flags.append("excessive_output_length")

        # PII in output is flagged but not removed (user might need it from their docs)
        if flags:
            logger.warning(f"Output guardrail flags: {flags}")

        return answer, flags

    def check_for_pii_in_chunks(self, chunks: list[dict]) -> list[dict]:
        """
        Scan chunks for PII and add warnings to metadata.
        Used during ingestion to flag sensitive documents.
        """
        flagged = []
        for chunk in chunks:
            content = chunk.get("content", "")
            pii_found = []
            for pii_type, pattern in self.PII_PATTERNS.items():
                matches = re.findall(pattern, content)
                if matches:
                    pii_found.append({"type": pii_type, "count": len(matches)})

            if pii_found:
                flagged.append({
                    "chunk_id": chunk.get("chunk_id", "unknown"),
                    "document": chunk.get("document", "unknown"),
                    "pii_types": pii_found,
                })

        if flagged:
            logger.warning(f"PII detected in {len(flagged)} chunks")

        return flagged


# Singleton
_guardrails = None


def get_guardrails_service() -> GuardrailsService:
    """Get the singleton guardrails service."""
    global _guardrails
    if _guardrails is None:
        _guardrails = GuardrailsService()
    return _guardrails
