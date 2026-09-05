from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.screening import ScreeningResult
from app.models.alert import RiskAlert
from app.api.deps import get_current_user
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse
from app.services.ai_companion import ai_companion_service
from app.services.risk_engine import risk_engine_service
from app.services.vector_store import vector_store
from app.services.tracing import tracing_service
from app.services.notification_service import (
    resolve_assigned_doctor,
    attach_sla,
    dispatch_critical_notifications,
)
import time
from typing import Set

router = APIRouter()

@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    msg_in: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not msg_in.message or not msg_in.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 1. Resolve or create active session
    session = None
    if msg_in.session_id:
        s_query = await db.execute(
            select(ChatSession).where(
                ChatSession.id == msg_in.session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = s_query.scalars().first()

    if not session:
        # Fetch or create default session
        s_query = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.created_at.desc())
        )
        session = s_query.scalars().first()

    if not session:
        session = ChatSession(user_id=current_user.id, title="Supportive Session")
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # 2. Scan message for distress signals
    is_flagged, severity = risk_engine_service.scan_message_for_distress(msg_in.message)
    if is_flagged:
        alert = RiskAlert(
            user_id=current_user.id,
            severity=severity,
            trigger_source="chat_distress",
            details=f"AI Chat Flagged Message: '{msg_in.message}'"
        )
        db.add(alert)

    # Save User message
    user_msg = ChatMessage(
        session_id=session.id,
        sender="user",
        content=msg_in.message.strip(),
        risk_flag=is_flagged,
        rag_context_used=False
    )
    db.add(user_msg)
    await db.commit()

    # 2b. CRITICAL signals: assign doctor, start SLA window, dispatch crisis notifications (G6)
    if is_flagged and severity == "CRITICAL":
        alert.assigned_doctor_id = await resolve_assigned_doctor(db, current_user)
        attach_sla(alert)
        await db.commit()
        await db.refresh(alert)
        await dispatch_critical_notifications(db, alert, current_user)

    # 3. Retrieve latest patient screening scores for context
    phq9_query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id, ScreeningResult.screening_type == "PHQ-9")
        .order_by(ScreeningResult.created_at.desc())
    )
    latest_phq9 = phq9_query.scalars().first()
    phq9_band = latest_phq9.severity_band if latest_phq9 else "Not Screened"

    gad7_query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id, ScreeningResult.screening_type == "GAD-7")
        .order_by(ScreeningResult.created_at.desc())
    )
    latest_gad7 = gad7_query.scalars().first()
    gad7_band = latest_gad7.severity_band if latest_gad7 else "Not Screened"

    # 4. Fetch recent chat history
    h_query = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_records = h_query.scalars().all()
    chat_history = [{"sender": m.sender, "content": m.content} for m in history_records[-6:]]

    # 5. Generate AI response + Tracing
    # --- Retrieval & Reranking ---
    start = time.perf_counter()
    context_chunks = vector_store.search_hybrid(
        query=msg_in.message.strip(),
        limit=5,
        rerank=True
    )
    retrieval_duration = (time.perf_counter() - start) * 1000
    
    # Save partial Assistant message to get ID for tracing
    asst_msg = ChatMessage(
        session_id=session.id,
        sender="assistant",
        content="Thinking...",
        risk_flag=False,
        rag_context_used=False
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)
    
    # Log Retrieval Trace
    await tracing_service.log_span(db, asst_msg.id, "hybrid_retrieval_rerank", retrieval_duration, {
        "doc_ids": [c["doc_id"] for c in context_chunks],
        "reranked_scores": [c.get("_rerank_score") for c in context_chunks]
    })
    
    # --- Generation ---
    start_gen = time.perf_counter()
    assistant_text, used_rag = await ai_companion_service.generate_response(
        user_message=msg_in.message.strip(),
        chat_history=chat_history,
        context_chunks=context_chunks,
        phq9_band=phq9_band,
        gad7_band=gad7_band
    )
    gen_duration = (time.perf_counter() - start_gen) * 1000
    
    # Log Generation Trace
    await tracing_service.log_span(db, asst_msg.id, "generation", gen_duration, {
        "used_rag": used_rag
    })
    
    # Update Assistant message stub
    asst_msg.content = assistant_text
    asst_msg.rag_context_used = used_rag
    await db.commit()
    await db.refresh(asst_msg)
    
    return asst_msg

@router.get("/history", response_model=ChatSessionResponse)
async def get_chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s_query = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    session = s_query.scalars().first()

    if not session:
        session = ChatSession(user_id=current_user.id, title="Supportive Session")
        db.add(session)
        await db.commit()
        await db.refresh(session)

    m_query = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = m_query.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "messages": messages
    }
