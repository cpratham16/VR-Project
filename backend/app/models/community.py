import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_pseudonym = Column(String, nullable=False, default="Anonymous Student")
    category = Column(String, nullable=False, default="General Wellness")
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)
    moderation_status = Column(String, default="approved", nullable=False)  # "approved", "flagged_pending", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")

class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_pseudonym = Column(String, nullable=False, default="Anonymous Student")
    content = Column(Text, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)
    moderation_status = Column(String, default="approved", nullable=False)  # "approved", "flagged_pending", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("CommunityPost", back_populates="comments")
