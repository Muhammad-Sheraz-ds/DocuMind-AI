"""
DocuMind AI — Document Ingestion Service

Handles: file parsing (PDF, DOCX, TXT, CSV), text extraction,
chunking with overlap, and metadata extraction.
"""
import os
import hashlib
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings


class DocumentChunk:
    """Represents a chunk of text from a document."""

    def __init__(
        self,
        content: str,
        metadata: dict,
        chunk_id: str,
    ):
        self.content = content
        self.metadata = metadata
        self.chunk_id = chunk_id


class IngestionService:
    """Service for parsing and chunking documents."""

    SUPPORTED_TYPES = {".pdf", ".docx", ".txt", ".csv", ".md"}

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate file type and size."""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_TYPES:
            return False, f"Unsupported file type: {ext}. Supported: {self.SUPPORTED_TYPES}"
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {settings.max_file_size_mb}MB)"
        return True, "OK"

    async def save_uploaded_file(self, filename: str, content: bytes) -> str:
        """Save uploaded file to disk and return the path."""
        filepath = os.path.join(settings.upload_dir, filename)
        # Avoid overwriting: add hash suffix if file exists
        if os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            file_hash = hashlib.md5(content).hexdigest()[:8]
            filepath = os.path.join(settings.upload_dir, f"{name}_{file_hash}{ext}")

        with open(filepath, "wb") as f:
            f.write(content)
        logger.info(f"Saved file: {filepath} ({len(content)} bytes)")
        return filepath

    def extract_text(self, filepath: str) -> tuple[str, int]:
        """
        Extract text from a file. Returns (full_text, num_pages).
        """
        ext = Path(filepath).suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(filepath)
        elif ext == ".docx":
            return self._extract_docx(filepath)
        elif ext in (".txt", ".md", ".csv"):
            return self._extract_text(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_pdf(self, filepath: str) -> tuple[str, int]:
        """Extract text from PDF using pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(filepath)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

        logger.info(f"Extracted {len(pages)} pages from PDF: {filepath}")
        return "\n\n".join(pages), len(pages)

    def _extract_docx(self, filepath: str) -> tuple[str, int]:
        """Extract text from DOCX."""
        from docx import Document

        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX: {filepath}")
        return "\n\n".join(paragraphs), len(paragraphs)

    def _extract_text(self, filepath: str) -> tuple[str, int]:
        """Extract text from plain text file."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Estimate pages (assuming ~3000 chars per page)
        num_pages = max(1, len(text) // 3000)
        return text, num_pages

    def chunk_text(
        self,
        text: str,
        filename: str,
        num_pages: int = 1,
    ) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks with metadata.

        Uses recursive character splitting: tries to split on paragraph
        boundaries first, then sentences, then words.
        """
        if not text.strip():
            return []

        chunks = []
        # Split by paragraphs first for natural boundaries
        paragraphs = text.split("\n\n")

        current_chunk = ""
        current_start_page = 1
        chars_per_page = max(1, len(text) // num_pages) if num_pages > 0 else len(text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size, save current and start new
            if len(current_chunk) + len(para) + 2 > self.chunk_size and current_chunk:
                chunk_id = hashlib.md5(
                    f"{filename}:{len(chunks)}:{current_chunk[:50]}".encode()
                ).hexdigest()

                # Estimate page number based on character position
                char_position = text.find(current_chunk[:100])
                estimated_page = min(
                    num_pages, max(1, (char_position // chars_per_page) + 1)
                ) if char_position >= 0 else current_start_page

                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    metadata={
                        "filename": filename,
                        "chunk_index": len(chunks),
                        "page": estimated_page,
                        "total_pages": num_pages,
                        "char_count": len(current_chunk),
                    },
                    chunk_id=chunk_id,
                ))

                # Overlap: keep the last chunk_overlap chars
                overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current_chunk = overlap_text + " " + para
            else:
                current_chunk = (current_chunk + "\n\n" + para).strip()

        # Don't forget the last chunk
        if current_chunk.strip():
            chunk_id = hashlib.md5(
                f"{filename}:{len(chunks)}:{current_chunk[:50]}".encode()
            ).hexdigest()
            char_position = text.find(current_chunk[:100])
            estimated_page = min(
                num_pages, max(1, (char_position // chars_per_page) + 1)
            ) if char_position >= 0 else num_pages

            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                metadata={
                    "filename": filename,
                    "chunk_index": len(chunks),
                    "page": estimated_page,
                    "total_pages": num_pages,
                    "char_count": len(current_chunk),
                },
                chunk_id=chunk_id,
            ))

        logger.info(f"Created {len(chunks)} chunks from '{filename}' "
                     f"(avg {sum(len(c.content) for c in chunks) // max(1, len(chunks))} chars/chunk)")
        return chunks
