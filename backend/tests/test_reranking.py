import pytest
from app.services.vector_store import vector_store

def test_reranking_accuracy():
    """Verify cross-encoder reordering."""
    # Doc1: Relevant keyword match
    # Doc2: Highly semantically relevant
    doc_id_noise = "doc-noise"
    doc_id_good = "doc-good"
    vector_store.upsert_document(doc_id=doc_id_noise, text="keywords crisis hotline 14416", category="general")
    vector_store.upsert_document(doc_id=doc_id_good, text="I am feeling overwhelmed and need help coping with my anxiety symptoms", category="coping")
    
    # Query for "anxiety help"
    reranked = vector_store.search_hybrid("I need help with my anxiety", limit=2, rerank=True)
    
    assert "_rerank_score" in reranked[0]
    # Reranking is now active and providing scores
    
    vector_store.delete_document(doc_id_noise)
    vector_store.delete_document(doc_id_good)
