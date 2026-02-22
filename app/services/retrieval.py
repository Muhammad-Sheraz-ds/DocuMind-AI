"""
DocuMind AI — Retrieval Service

Hybrid search: ChromaDB semantic search + BM25 keyword search + score fusion.
"""
import json
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from rank_bm25 import BM25Okapi

from app.config import settings
from app.services.embedding import get_embedding_service
from app.services.ingestion import DocumentChunk


class RetrievalService:
    """Service for storing and retrieving document chunks using hybrid search."""

    def __init__(self):
        self.embedding_service = get_embedding_service()

        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info(f"ChromaDB initialized at: {settings.chroma_persist_dir}")

        # BM25 indexes per collection (in-memory, rebuilt on startup)
        self._bm25_indexes: dict[str, tuple[BM25Okapi, list[dict]]] = {}

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        collection = self.chroma_client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        return collection

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        collection_name: str,
    ) -> int:
        """
        Index document chunks into ChromaDB + BM25.

        Returns the number of chunks indexed.
        """
        if not chunks:
            return 0

        collection = self.get_or_create_collection(collection_name)

        # Prepare data for ChromaDB
        texts = [c.content for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Generate embeddings
        embeddings = self.embedding_service.embed_batch(texts)

        # Upsert into ChromaDB
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        # Build BM25 index for this collection
        self._rebuild_bm25_index(collection_name)

        logger.info(f"Indexed {len(chunks)} chunks into collection '{collection_name}'")
        return len(chunks)

    def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = None,
        document_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Hybrid search: combine semantic search + BM25, then fuse scores.

        Returns list of dicts with: content, document, page, score, chunk_id
        """
        top_k = top_k or settings.top_k

        # 1. Semantic search (ChromaDB)
        semantic_results = self._semantic_search(
            query, collection_name, top_k=top_k * 2, document_filter=document_filter
        )

        # 2. BM25 keyword search
        bm25_results = self._bm25_search(
            query, collection_name, top_k=top_k * 2, document_filter=document_filter
        )

        # 3. Reciprocal Rank Fusion (combine both result sets)
        fused = self._reciprocal_rank_fusion(semantic_results, bm25_results, k=60)

        # Return top_k results
        results = fused[:top_k]
        logger.info(
            f"Hybrid search for '{query[:50]}...' → "
            f"{len(semantic_results)} semantic + {len(bm25_results)} BM25 → "
            f"{len(results)} fused results"
        )
        return results

    def _semantic_search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        document_filter: Optional[str] = None,
    ) -> list[dict]:
        """Semantic search using ChromaDB."""
        collection = self.get_or_create_collection(collection_name)

        if collection.count() == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Build where filter if document_filter is provided
        where_filter = None
        if document_filter:
            where_filter = {"filename": document_filter}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        parsed = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns cosine distance, convert to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = max(0.0, 1.0 - distance)

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                parsed.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i],
                    "document": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page", None),
                    "score": similarity,
                    "source": "semantic",
                })

        return parsed

    def _bm25_search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        document_filter: Optional[str] = None,
    ) -> list[dict]:
        """BM25 keyword search."""
        if collection_name not in self._bm25_indexes:
            self._rebuild_bm25_index(collection_name)

        if collection_name not in self._bm25_indexes:
            return []

        bm25, corpus_data = self._bm25_indexes[collection_name]

        # Filter by document if needed
        if document_filter:
            filtered_indices = [
                i for i, d in enumerate(corpus_data)
                if d.get("filename") == document_filter
            ]
            if not filtered_indices:
                return []
        else:
            filtered_indices = list(range(len(corpus_data)))

        # Tokenize query
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Get top results from filtered indices
        scored_results = [
            (idx, scores[idx]) for idx in filtered_indices if scores[idx] > 0
        ]
        scored_results.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_results[:top_k]:
            data = corpus_data[idx]
            # Normalize BM25 score to 0-1 range
            max_score = scored_results[0][1] if scored_results else 1
            normalized_score = score / max_score if max_score > 0 else 0

            results.append({
                "chunk_id": data.get("chunk_id", f"bm25_{idx}"),
                "content": data["content"],
                "document": data.get("filename", "Unknown"),
                "page": data.get("page", None),
                "score": normalized_score,
                "source": "bm25",
            })

        return results

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[dict],
        bm25_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion (RRF) to combine two result lists.
        Score = sum(1 / (k + rank)) across all lists.
        """
        fused_scores: dict[str, dict] = {}

        for rank, result in enumerate(semantic_results):
            chunk_id = result["chunk_id"]
            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = {**result, "score": 0.0, "source": "hybrid"}
            fused_scores[chunk_id]["score"] += 1.0 / (k + rank + 1)

        for rank, result in enumerate(bm25_results):
            chunk_id = result["chunk_id"]
            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = {**result, "score": 0.0, "source": "hybrid"}
            fused_scores[chunk_id]["score"] += 1.0 / (k + rank + 1)

        # Sort by fused score
        fused_list = sorted(
            fused_scores.values(), key=lambda x: x["score"], reverse=True
        )
        return fused_list

    def _rebuild_bm25_index(self, collection_name: str):
        """Rebuild the BM25 index from ChromaDB data."""
        collection = self.get_or_create_collection(collection_name)

        if collection.count() == 0:
            return

        # Get all documents from ChromaDB
        all_data = collection.get(include=["documents", "metadatas"])

        if not all_data["documents"]:
            return

        corpus_data = []
        tokenized_corpus = []

        for i, doc_text in enumerate(all_data["documents"]):
            metadata = all_data["metadatas"][i] if all_data["metadatas"] else {}
            corpus_data.append({
                "content": doc_text,
                "chunk_id": all_data["ids"][i],
                "filename": metadata.get("filename", "Unknown"),
                "page": metadata.get("page", None),
            })
            tokenized_corpus.append(doc_text.lower().split())

        bm25 = BM25Okapi(tokenized_corpus)
        self._bm25_indexes[collection_name] = (bm25, corpus_data)
        logger.info(f"BM25 index rebuilt for '{collection_name}' ({len(corpus_data)} docs)")

    def get_collection_stats(self, collection_name: str) -> dict:
        """Get statistics for a collection."""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "num_chunks": collection.count(),
        }

    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        try:
            self.chroma_client.delete_collection(collection_name)
            if collection_name in self._bm25_indexes:
                del self._bm25_indexes[collection_name]
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")


# Singleton
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """Get the singleton retrieval service."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
