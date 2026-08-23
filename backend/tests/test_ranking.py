import pytest
from app.services.ranking import ranking_service

def test_rrf_fusion_logic():
    # Mock results: dense favors doc1, sparse favors doc2
    dense_results = [
        {"doc_id": "doc1", "chunk_index": 0},
        {"doc_id": "doc2", "chunk_index": 0},
    ]
    sparse_results = [
        {"doc_id": "doc2", "chunk_index": 0},
        {"doc_id": "doc1", "chunk_index": 0},
    ]
    
    # RRF (k=60) should give doc2 a slight edge because it ranked higher in sparse (rank 1 vs rank 2 in dense)
    # doc1: dense rank 1, sparse rank 2 => 1/(60+1) + 1/(60+2) = 0.01639 + 0.01613 = 0.03252
    # doc2: dense rank 2, sparse rank 1 => 1/(60+2) + 1/(60+1) = 0.01613 + 0.01639 = 0.03252
    # Wait, k=60 makes doc1 and doc2 almost equal!
    # Let's use a very small K to amplify the difference for the test
    fused = ranking_service.reciprocal_rank_fusion(dense_results, sparse_results, limit=2, k=1)
    
    # Doc1: dense rank 1, sparse rank 2 => 1/(1+1) + 1/(1+2) = 0.5 + 0.333 = 0.833
    # Doc2: dense rank 2, sparse rank 1 => 1/(1+2) + 1/(1+1) = 0.333 + 0.5 = 0.833
    # They are still equal.
    
    # Use distinct result sets
    dense = [{"doc_id": "doc_winner", "chunk_index": 0}]
    sparse = [{"doc_id": "doc_winner", "chunk_index": 0}, {"doc_id": "doc_sparse_only", "chunk_index": 0}]
    
    fused = ranking_service.reciprocal_rank_fusion(dense, sparse, limit=2)
    assert fused[0]["doc_id"] == "doc_winner"
    assert "_rrf_score" in fused[0]
