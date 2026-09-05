import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.tracing import TracingSpan
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/trace/{message_id}", response_model=List[Dict[str, Any]])
async def get_message_trace(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return all execution spans (Retrieval, Reranking, Generation) for a given message ID formatted for UI visualization."""
    query = await db.execute(
        select(TracingSpan)
        .where(TracingSpan.message_id == message_id)
        .order_by(TracingSpan.start_time.asc())
    )
    spans = query.scalars().all()
    
    if not spans:
        return []
        
    result = []
    for span in spans:
        meta = {}
        if span.metadata_json:
            try:
                meta = json.loads(span.metadata_json)
            except Exception:
                meta = {"raw": span.metadata_json}
                
        result.append({
            "id": span.id,
            "message_id": span.message_id,
            "span_name": span.span_name,
            "duration_ms": span.duration_ms,
            "start_time": span.start_time.isoformat() if span.start_time else None,
            "telemetry": meta
        })
        
    return result
