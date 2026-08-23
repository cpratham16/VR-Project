import re
import uuid
import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
from app.services.embeddings import embed_documents

logger = logging.getLogger("app.services.vector_store")

CHUNK_KINDS = ("qa", "statement", "post", "intent")

_DOC_UUID_NS = uuid.UUID("6f1f3a2e-4b6c-4f8e-9a1d-2c3e4d5f6a7b")


def chunk_text(text: str, max_chars: Optional[int] = None, overlap_chars: Optional[int] = None) -> List[str]:
    """Split a document into overlapping chunks on sentence/paragraph boundaries.

    Records shorter than max_chars stay as a single chunk. Long texts are split
    paragraph-first, then by sentence, falling back to a hard character split.
    """
    max_chars = max_chars or settings.CHUNK_SIZE_CHARS
    overlap_chars = overlap_chars or settings.CHUNK_OVERLAP_CHARS
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    hard_split = max_chars - overlap_chars
    if hard_split <= 0:
        raise ValueError("CHUNK_OVERLAP_CHARS must be smaller than CHUNK_SIZE_CHARS")

    def chunk_paragraph(paragraph: str) -> List[str]:
        if len(paragraph) <= max_chars:
            return [paragraph]
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks: List[str] = []
        current = ""
        for sentence in sentences:
            if len(sentence) > max_chars:
                if current:
                    chunks.append(current.strip())
                    current = ""
                for start in range(0, len(sentence), hard_split):
                    piece = sentence[start : start + max_chars]
                    if piece.strip():
                        chunks.append(piece.strip())
                continue
            if current and len(current) + len(sentence) + 1 > max_chars:
                chunks.append(current.strip())
                current = (current[-overlap_chars:] + " " + sentence) if overlap_chars else sentence
            else:
                current = current + " " + sentence if current else sentence
        if current.strip():
            chunks.append(current.strip())
        return chunks

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    if len(paragraphs) <= 1:
        return chunk_paragraph(text)

    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 1 > max_chars:
            chunks.append(current.strip())
            current = ""
        current = current + " " + paragraph if current else paragraph
        while len(current) > max_chars:
            pieces = chunk_paragraph(current)
            chunks.append(pieces[0])
            current = pieces[-1]
    for piece in chunk_paragraph(current):
        chunks.append(piece)
    return [c for c in chunks if c]


class VectorStoreService:
    """Qdrant-backed store for knowledge base chunks with dense embeddings."""

    def __init__(self, client: Optional[QdrantClient] = None) -> None:
        self._client = client or self._build_client()
        self.collection_name = settings.QDRANT_COLLECTION
        self.dimension = settings.EMBEDDING_DIMENSION

    @staticmethod
    def _build_client() -> QdrantClient:
        if settings.QDRANT_URL == ":memory:":
            return QdrantClient(":memory:")
        return QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=20,
        )

    def ensure_collection(self) -> None:
        if not self._collection_exists():
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self.dimension,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            for field in ("doc_id", "kind", "category", "status"):
                self._client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
            logger.info(
                "Created collection '%s' (dim %d, cosine)",
                self.collection_name,
                self.dimension,
            )

    def upsert_document(
        self,
        doc_id: str,
        text: str,
        kind: str = "statement",
        category: str = "general",
        status: str = "",
    ) -> int:
        """Chunk, embed, and store a document. Returns number of chunks written."""
        if kind not in CHUNK_KINDS:
            raise ValueError(f"kind must be one of {CHUNK_KINDS}, got '{kind}'")
        chunks = chunk_text(text)
        if not chunks:
            return 0
        vectors = embed_documents(chunks)
        if len(vectors) != len(chunks):
            raise ValueError("Embedding count does not match chunk count")

        self.ensure_collection()
        points = []
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = str(uuid.uuid5(_DOC_UUID_NS, f"{doc_id}:{index}"))
            points.append(
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "doc_id": doc_id,
                        "kind": kind,
                        "category": category,
                        "status": status,
                        "chunk_index": index,
                        "total_chunks": len(chunks),
                        "text": chunk,
                        "created_at": "now",
                    },
                )
            )
        self._client.upsert(collection_name=self.collection_name, points=points)
        logger.info(
            "Upserted document '%s' (%d chunks, kind=%s, category=%s, status='%s')",
            doc_id,
            len(chunks),
            kind,
            category,
            status,
        )
        return len(chunks)

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve all chunks belonging to a document by its source ID."""
        if not self._collection_exists():
            return {"doc_id": doc_id, "chunks": []}
        result = self._client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="doc_id",
                        match=qdrant_models.MatchValue(value=doc_id),
                    )
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        chunks = result[0]
        return {
            "doc_id": doc_id,
            "chunks": [p.payload for p in chunks],
        }

    def delete_document(self, doc_id: str) -> bool:
        if not self._collection_exists():
            return False
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="doc_id",
                            match=qdrant_models.MatchValue(value=doc_id),
                        )
                    ]
                )
            ),
        )
        return True

    def count(self) -> int:
        if not self._collection_exists():
            return 0
        return self._client.count(collection_name=self.collection_name).count

    def _collection_exists(self) -> bool:
        return any(
            c.name == self.collection_name
            for c in self._client.get_collections().collections
        )


vector_store = VectorStoreService()