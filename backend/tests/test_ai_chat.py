import pytest
from app.services.risk_engine import risk_engine_service
from app.services.rag_engine import rag_engine
from app.services.ai_companion import ai_companion_service

def test_distress_keyword_scanner():
    # Test critical self-harm trigger
    is_flagged, severity = risk_engine_service.scan_message_for_distress("I feel like I want to end my life")
    assert is_flagged is True
    assert severity == "CRITICAL"

    # Test high panic trigger
    is_flagged, severity = risk_engine_service.scan_message_for_distress("I am having an extreme panic attack right now")
    assert is_flagged is True
    assert severity == "HIGH"

    # Test normal query
    is_flagged, severity = risk_engine_service.scan_message_for_distress("What time is the library open?")
    assert is_flagged is False
    assert severity == "NONE"

def test_rag_context_retrieval():
    results = rag_engine.retrieve_relevant_context("I feel overwhelmed by exams", top_k=2)
    assert len(results) > 0
    assert "input" in results[0]
    assert "output" in results[0]

@pytest.mark.asyncio
async def test_ai_companion_fallback_generation():
    # Test fallback generation when no Groq key is supplied or API fails
    reply, used_rag = await ai_companion_service.generate_response(
        user_message="I'm feeling very stressed about my grades.",
        chat_history=[],
        phq9_band="Mild",
        gad7_band="Moderate"
    )
    assert reply is not None
    assert len(reply) > 10
