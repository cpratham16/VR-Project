import json
import pytest
from app.models.tracing import TracingSpan
from app.services.tracing import tracing_service
from app.core.database import AsyncSessionLocal
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_tracing_logs_and_api():
    message_id = "test-message-trace-123"
    
    async with AsyncSessionLocal() as db:
        # 1. Log spans successfully
        await tracing_service.log_span(
            db,
            message_id=message_id,
            span_name="hybrid_retrieval_rerank",
            duration_ms=45.2,
            metadata={"doc_ids": ["seed-001", "seed-002"]}
        )
        await tracing_service.log_span(
            db,
            message_id=message_id,
            span_name="generation",
            duration_ms=1200.5,
            metadata={"used_rag": True}
        )
        
        # 2. Query spans inside DB
        query = await db.execute(select(TracingSpan).where(TracingSpan.message_id == message_id).order_by(TracingSpan.start_time.asc()))
        spans = query.scalars().all()
        assert len(spans) >= 2
        
        # It may contain spans from previous fast executions that didn't clean up correctly
        retrieval_spans = [s for s in spans if s.span_name == "hybrid_retrieval_rerank"]
        gen_spans = [s for s in spans if s.span_name == "generation"]
        
        assert len(retrieval_spans) >= 1
        assert len(gen_spans) >= 1
        
        assert "seed-001" in retrieval_spans[-1].metadata_json
        
        # Cleanup
        await db.delete(retrieval_spans[-1])
        await db.delete(gen_spans[-1])
        await db.commit()
