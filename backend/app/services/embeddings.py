import logging
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("app.services.embeddings")

GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"

MAX_GEMINI_BATCH = 32

provider_cache: Optional["EmbeddingProvider"] = None


class EmbeddingProvider:
    """Base embeddings provider with a stable embed() interface."""

    name = "generic"

    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Free-tier Google Gemini embeddings via plain httpx (matches Groq integration style)."""

    name = "gemini"

    def __init__(self, api_key: str, model: str, dimension: int, timeout: float = 20.0) -> None:
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.timeout = timeout

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        url = GEMINI_EMBED_URL.format(model=self.model)
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        for start in range(0, len(texts), MAX_GEMINI_BATCH):
            batch = texts[start : start + MAX_GEMINI_BATCH]
            payload = {
                "requests": [
                    {
                        "model": f"models/{self.model}",
                        "content": {"parts": [{"text": text}]},
                        "outputDimensionality": self.dimension,
                    }
                    for text in batch
                ]
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            for emb in resp.json().get("embeddings", []):
                vectors.append(emb["values"])
        return vectors


class FastEmbedProvider(EmbeddingProvider):
    """Local ONNX embeddings via fastembed. Used for offline/hermetic runs and tests."""

    name = "fastembed"

    def __init__(self, model_name: str, dimension: int) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)
        self.dimension = dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [v.tolist() for v in self._model.embed(list(texts))]


def _build_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER
    if provider == "gemini" and not settings.GEMINI_API_KEY:
        raise ValueError("EMBEDDING_PROVIDER=gemini but GEMINI_API_KEY is empty")
    if provider in ("auto", "gemini") and settings.GEMINI_API_KEY:
        logger.info("Using Gemini embedding provider (%s)", settings.GEMINI_EMBEDDING_MODEL)
        return GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    logger.info("Using local fastembed provider (%s)", settings.FASTEMBED_MODEL)
    return FastEmbedProvider(
        model_name=settings.FASTEMBED_MODEL,
        dimension=settings.EMBEDDING_DIMENSION,
    )


def get_provider() -> EmbeddingProvider:
    global provider_cache
    if provider_cache is None:
        provider_cache = _build_provider()
    return provider_cache


def reset_provider() -> None:
    global provider_cache
    provider_cache = None


def embed_documents(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    return get_provider().embed(texts)


def embed_documents_async(texts: List[str]):
    """Async wrapper around embed_documents so service callers can await it."""
    import asyncio

    future = asyncio.get_event_loop().run_in_executor(None, embed_documents, texts)
    return future


asyncio_embed_documents = embed_documents_async