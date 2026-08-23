import pytest
from qdrant_client import QdrantClient

from app.services.embeddings import _build_provider, reset_provider
from app.services.vector_store import VectorStoreService, chunk_text


@pytest.fixture(autouse=True)
def _reset_provider():
    reset_provider()
    yield
    reset_provider()


@pytest.fixture(scope="module")
def memory_client():
    return QdrantClient(":memory:")


@pytest.fixture
def vector_store_factory():
    from app.core.config import settings

    original_url = settings.QDRANT_URL
    settings.QDRANT_URL = ":memory:"
    try:
        def make_store():
            return VectorStoreService()  # builds :memory: client via settings
        yield make_store
    finally:
        settings.QDRANT_URL = original_url
        reset_provider()


def test_chunk_text_short_document_stays_single():
    assert chunk_text("Short statement.", max_chars=1000) == ["Short statement."]


def test_chunk_text_long_document_splits_and_keeps_order():
    long_text = ". ".join(f"This is running sentence number {i}." for i in range(1, 60))
    chunks = chunk_text(long_text, max_chars=120, overlap_chars=20)
    assert len(chunks) > 1
    assert all(len(c) <= 140 for c in chunks)
    assert all(len(c) > 40 for c in chunks)


def test_round_trip_document_in_memory(vector_store_factory):
    doc_id = "test-doc-001"
    text = "I feel incredibly anxious about my upcoming exams and cannot focus on anything else."
    store = vector_store_factory()
    written = store.upsert_document(
        doc_id=doc_id,
        text=text,
        kind="qa",
        category="exam_stress",
        status="Anxiety",
    )
    assert written == 1
    assert store.count() == 1

    doc = store.get_document(doc_id)
    assert doc["chunks"], "Document should be retrievable by ID"
    chunk = doc["chunks"][0]
    assert chunk["doc_id"] == doc_id
    assert chunk["kind"] == "qa"
    assert chunk["category"] == "exam_stress"
    assert chunk["status"] == "Anxiety"
    assert chunk["text"] == text
    assert chunk["total_chunks"] == 1
    assert store.count() == 1


def test_repeated_upsert_is_idempotent(vector_store_factory):
    store = vector_store_factory()
    doc_id = "test-doc-002"
    store.upsert_document(doc_id=doc_id, text="A short statement without status.")
    store.upsert_document(doc_id=doc_id, text="A short statement without status.")
    assert store.count() == 1


def test_delete_document(vector_store_factory):
    store = vector_store_factory()
    store.upsert_document(doc_id="doc-to-delete", text="Content to be deleted.")
    assert store.count() == 1
    assert store.delete_document("doc-to-delete") is True
    assert store.count() == 0


def test_embed_dimension_is_configured():
    from app.core.config import settings

    provider = _build_provider()
    vectors = provider.embed(["hello world"])
    assert len(vectors) == 1
    assert len(vectors[0]) == settings.EMBEDDING_DIMENSION