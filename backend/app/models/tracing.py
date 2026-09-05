from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class TracingSpan(Base):
    __tablename__ = "tracing_spans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, index=True) # Linked to chat_message
    span_name = Column(String) # e.g., 'retrieval_dense', 'retrieval_sparse', 'rerank', 'generation'
    start_time = Column(DateTime, default=func.now())
    duration_ms = Column(Float)
    metadata_json = Column(String) # JSON string with doc_ids, status, rerank scores etc.
