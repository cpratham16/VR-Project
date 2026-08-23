import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_companion import ai_companion_service

@pytest.mark.asyncio
async def test_generation_pipeline_with_citations_and_stripping():
    # Mock context chunks
    mock_chunks = [
        {"doc_id": "seed-001", "text": "Grounding technique 5-4-3-2-1 helps with panic."},
        {"doc_id": "seed-002", "text": "Call 14416 for crisis."},
    ]
    
    # 1. Test validation: hallucinated citation gets stripped
    reply_with_hallucination = "Use the grounding technique [seed-001]. For crisis help, call [ghost-id] or [seed-002]."
    # Expected: [ghost-id] should be stripped by response_processor
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Mock successful Groq response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": reply_with_hallucination}}]
        }
        
        reply, used_rag = await ai_companion_service.generate_response(
            user_message="I'm panicking",
            chat_history=[],
            context_chunks=mock_chunks
        )
        
        assert used_rag is True
        assert "[seed-001]" in reply
        assert "[seed-002]" in reply
        assert "[ghost-id]" not in reply
        assert "call  or" in reply # The ghost citation was stripped
