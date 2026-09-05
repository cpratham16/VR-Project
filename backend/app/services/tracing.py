import json
import time
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracing import TracingSpan

logger = logging.getLogger("app.services.tracing")

class TracingService:
    """Service to create and persist OpenTelemetry-style spans for RAG & AI operations."""

    async def log_span(
        self,
        db: AsyncSession,
        message_id: str,
        span_name: str,
        duration_ms: float,
        metadata: Dict[str, Any]
    ) -> TracingSpan:
        span = TracingSpan(
            message_id=str(message_id),
            span_name=span_name,
            duration_ms=round(duration_ms, 2),
            metadata_json=json.dumps(metadata)
        )
        db.add(span)
        await db.commit()
        await db.refresh(span)
        logger.info("Logged span '%s' for message '%s' (%s ms)", span_name, message_id, duration_ms)
        return span

tracing_service = TracingService()
