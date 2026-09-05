import pytest
from unittest.mock import AsyncMock, patch
from app.services.risk_engine import risk_engine_service

def test_comment_parent_id_none_for_top_level():
    """Verify top-level comments have parent_id=None by default."""
    from app.schemas.community import CommunityCommentCreate
    comment = CommunityCommentCreate(content="Hello world")
    assert comment.parent_id is None

def test_comment_parent_id_set_for_reply():
    """Verify reply comments carry parent_id."""
    from app.schemas.community import CommunityCommentCreate
    import uuid
    parent = uuid.uuid4()
    comment = CommunityCommentCreate(content="Reply text", parent_id=parent)
    assert comment.parent_id == parent

def test_distress_flag_propagates_to_reply():
    """Verify that distress scanning works on reply content independently."""
    flagged, severity = risk_engine_service.scan_message_for_distress("I want to kill myself")
    assert flagged is True
    assert severity in ["HIGH", "MEDIUM", "CRITICAL"]

def test_distress_clean_reply_not_flagged():
    """Verify clean reply content is not flagged."""
    flagged, severity = risk_engine_service.scan_message_for_distress("Thanks for the support!")
    assert flagged is False
