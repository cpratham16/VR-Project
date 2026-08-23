import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("app.services.ranking")

DEFAULT_RRF_K = 60


class RankingService:
    """Service for post-retrieval reranking and fusion algorithms."""

    def __init__(self, default_k: int = DEFAULT_RRF_K) -> None:
        self.default_k = default_k

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
