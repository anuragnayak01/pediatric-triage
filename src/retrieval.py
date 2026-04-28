"""
Retrieval-Augmented Generation (RAG) layer for pediatric symptom triage.

This module provides:
- ChromaDB-backed vector indexing of pediatric safety chunks
- Multilingual semantic search (English + Arabic)
- Evidence retrieval with metadata preservation
"""

import json
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer


# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
INDEX_DIR = PROJECT_ROOT / "data" / "indexes"


class PediatricTriageRetriever:
    """Semantic search over pediatric safety guidance."""

    def __init__(
        self,
        embedding_model: str = "intfloat/multilingual-e5-base",
        index_dir: Optional[Path] = None,
    ):
        """
        Initialize the retriever.

        Args:
            embedding_model: Hugging Face model ID for multilingual embeddings.
            index_dir: Directory for ChromaDB persistence.
        """
        self.embedding_model_name = embedding_model
        self.index_dir = index_dir or INDEX_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model (lazy load)
        self._embedder = None
        self._client = None
        self._collection = None

        # Load or create index
        self._initialize_index()

    @property
    def embedder(self):
        """Lazy-load embedding model."""
        if self._embedder is None:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder

    @property
    def client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.index_dir / "chroma")
            )
        return self._client

    @property
    def collection(self):
        """Get or create collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="pediatric_safety",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _initialize_index(self):
        """Build ChromaDB index from chunks.jsonl if not already done."""
        # Check if index already populated
        if self.collection.count() > 0:
            print(f"Index already initialized with {self.collection.count()} chunks.")
            return

        print(f"Building index from {CHUNKS_PATH}...")
        if not CHUNKS_PATH.exists():
            raise FileNotFoundError(f"Chunks file not found: {CHUNKS_PATH}")

        # Load all chunks
        chunks = []
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))

        print(f"Loaded {len(chunks)} chunks. Embedding and indexing...")

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        batch_size = 32
        for i, chunk in enumerate(chunks):
            if (i + 1) % 100 == 0:
                print(f"  Processing {i + 1}/{len(chunks)}...")

            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])

            # Preserve metadata
            metadata = {
                "source_name": chunk.get("source_name", ""),
                "source_file": chunk.get("source_file", ""),
                "source_url": chunk.get("source_url", ""),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "section_title": chunk.get("section_title", ""),
                "severity_relevance": chunk.get("severity_relevance", ""),
                "topic": chunk.get("topic", ""),
                "keywords": "|".join(chunk.get("keywords", [])),
            }
            metadatas.append(metadata)

            # Embed text (multilingual model handles both EN and AR)
            embedding = self.embedder.encode(
                chunk["text"], convert_to_tensor=False
            ).tolist()
            embeddings.append(embedding)

            # Batch insert for efficiency
            if (i + 1) % batch_size == 0:
                self.collection.add(
                    ids=ids[-batch_size:],
                    documents=documents[-batch_size:],
                    metadatas=metadatas[-batch_size:],
                    embeddings=embeddings[-batch_size:],
                )

        # Insert remaining
        if ids[-batch_size:]:
            self.collection.add(
                ids=ids[-batch_size:],
                documents=documents[-batch_size:],
                metadatas=metadatas[-batch_size:],
                embeddings=embeddings[-batch_size:],
            )

        print(f"[OK] Index built with {self.collection.count()} chunks.")

    def search(
        self,
        query: str,
        k: int = 6,
        severity_filter: Optional[str] = None,
        age_months: Optional[int] = None,
        minimum_relevance_threshold: float = 0.3,
        max_context_chunks: int = 4,
    ) -> tuple[list[dict], bool]:
        """
        Semantic search with metadata filtering and relevance thresholding.

        Args:
            query: Natural language query (English or Arabic).
            k: Number of candidates to retrieve before filtering.
            severity_filter: Filter by severity_relevance (HIGH/MODERATE/GENERAL).
            age_months: Child's age for age-group filtering.
            minimum_relevance_threshold: Minimum similarity score to keep chunk.
            max_context_chunks: Maximum chunks to return after filtering.

        Returns:
            Tuple of (evidence_list, is_weak_retrieval)
            is_weak_retrieval=True if < 2 relevant chunks found
        """
        # Embed query (multilingual model handles EN and AR)
        query_embedding = self.embedder.encode(query, convert_to_tensor=False).tolist()

        # Retrieve more candidates than needed, will filter below
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        # Format and filter results
        candidates = []
        if results and results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]

                # Convert distance to similarity score (0-1)
                similarity = 1 - distance if distance is not None else 0.5

                # Build candidate record
                candidate = {
                    "chunk_id": results["ids"][0][i] if results.get("ids") else "",
                    "text": doc,
                    "source_name": metadata.get("source_name", ""),
                    "source_file": metadata.get("source_file", ""),
                    "source_url": metadata.get("source_url", ""),
                    "page_start": metadata.get("page_start"),
                    "page_end": metadata.get("page_end"),
                    "section_title": metadata.get("section_title", ""),
                    "severity_relevance": metadata.get("severity_relevance", ""),
                    "topic": metadata.get("topic", ""),
                    "age_group": metadata.get("age_group", ""),
                    "similarity_score": round(similarity, 3),
                }
                candidates.append(candidate)

        # Apply filters: relevance threshold, severity preference, age preference
        filtered = []
        for candidate in candidates:
            # Hard filter: relevance threshold
            if candidate["similarity_score"] < minimum_relevance_threshold:
                continue
            
            # Soft boost: prefer severity_relevance if specified
            if severity_filter and candidate["severity_relevance"] == severity_filter:
                candidate["match_quality"] = candidate["similarity_score"] + 0.2
            else:
                candidate["match_quality"] = candidate["similarity_score"]
            
            # Soft boost: prefer age-group if specified
            if age_months is not None and candidate.get("age_group"):
                age_group = candidate["age_group"]
                # Simple heuristic: check if age_group matches
                if ("infant" in age_group.lower() and age_months < 12) or \
                   ("toddler" in age_group.lower() and 12 <= age_months < 36) or \
                   ("child" in age_group.lower() and age_months >= 36):
                    candidate["match_quality"] += 0.15
            
            filtered.append(candidate)

        # Sort by match quality (boosted scores)
        filtered = sorted(filtered, key=lambda x: x["match_quality"], reverse=True)
        
        # Limit to max_context_chunks
        evidence = filtered[:max_context_chunks]

        # Detect weak retrieval
        is_weak = len(evidence) < 2

        # Clean up match_quality field (internal only)
        for item in evidence:
            item.pop("match_quality", None)

        return evidence, is_weak

    def search_by_keywords(
        self,
        keywords: list[str],
        k: int = 6,
        age_months: Optional[int] = None,
        minimum_relevance_threshold: float = 0.3,
    ) -> tuple[list[dict], bool]:
        """
        Search by keywords (for deterministic matching during triage).

        Args:
            keywords: List of symptom keywords.
            k: Number of results per keyword.
            age_months: Child's age for age-group filtering.
            minimum_relevance_threshold: Minimum similarity score.

        Returns:
            Tuple of (evidence_list, is_weak_retrieval)
        """
        all_evidence = {}

        for keyword in keywords:
            results, _ = self.search(
                keyword, 
                k=k, 
                age_months=age_months,
                minimum_relevance_threshold=minimum_relevance_threshold,
                max_context_chunks=10  # Get more to aggregate
            )
            for result in results:
                chunk_id = result["chunk_id"]
                if chunk_id not in all_evidence:
                    all_evidence[chunk_id] = result
                else:
                    # Update score to max if this appeared multiple times
                    all_evidence[chunk_id]["similarity_score"] = max(
                        all_evidence[chunk_id]["similarity_score"],
                        result["similarity_score"],
                    )

        # Sort by similarity
        sorted_evidence = sorted(
            all_evidence.values(),
            key=lambda x: x["similarity_score"],
            reverse=True,
        )

        final_evidence = sorted_evidence[:k]
        is_weak = len(final_evidence) < 2

        return final_evidence, is_weak


def get_retriever() -> PediatricTriageRetriever:
    """Get or create the global retriever instance."""
    if not hasattr(get_retriever, "_instance"):
        get_retriever._instance = PediatricTriageRetriever()
    return get_retriever._instance
