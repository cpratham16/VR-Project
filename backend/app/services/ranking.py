import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("app.services.ranking")

DEFAULT_RRF_K = 60


class RankingService:
    """Service for post-retrieval reranking and fusion algorithms."""

    def __init__(self, default_k: int = DEFAULT_RRF_K) -> None:
        self.default_k = default_k
        self._reranker: Any = None

    def _get_reranker(self):
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(settings.RERANKER_MODEL)
            except ImportError:
                logger.error("sentence-transformers missing")
                raise
        return self._reranker

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank fused candidates using a cross-encoder model."""
        if not documents:
            return []
            
        reranker = self._get_reranker()
        # Pair query with each document text
        pairs = [(query, doc.get("text", "")) for doc in documents]
        # CrossEncoder.predict returns relevance scores
        scores = reranker.predict(pairs)
        
        # Zip scores back to docs
        for i, doc in enumerate(documents):
            doc["_rerank_score"] = float(scores[i])
            
        # Re-sort by cross-encoder score
        reranked = sorted(documents, key=lambda x: x["_rerank_score"], reverse=True)
        return reranked[:top_k]

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        limit: int = 5,
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Combine dense (semantic) and sparse (keyword) search results using Reciprocal Rank Fusion (RRF).

        Formula: RRF_score(d) = sum(1 / (k + rank_m(d))) for all retrieval lists m.
        """
        k_val = k if k is not None else self.default_k
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Process dense results ranking
        for rank, doc in enumerate(dense_results, start=1):
            key = f"{doc.get('doc_id')}:{doc.get('chunk_index', 0)}"
            scores[key] = scores.get(key, 0.0) + (1.0 / (k_val + rank))
            if key not in doc_map:
                doc_map[key] = doc

        # Process sparse results ranking
        for rank, doc in enumerate(sparse_results, start=1):
            key = f"{doc.get('doc_id')}:{doc.get('chunk_index', 0)}"
            scores[key] = scores.get(key, 0.0) + (1.0 / (k_val + rank))
            if key not in doc_map:
                doc_map[key] = doc

        # Sort documents by fused RRF score descending
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        fused: List[Dict[str, Any]] = []
        for key in sorted_keys[:limit]:
            item = doc_map[key].copy()
            item["_rrf_score"] = round(scores[key], 6)
            fused.append(item)

        logger.info(
            "RRF Fusion completed: merged %d dense & %d sparse candidates into top %d results",
            len(dense_results),
            len(sparse_results),
            len(fused),
        )
        return fused


ranking_service = RankingService()
