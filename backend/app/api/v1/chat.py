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

    # 3. Retrieve latest patient screening scores for context
    scr_query = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == current_user.id)
        .order_by(ScreeningResult.created_at.desc())
    )
    latest_scr = scr_query.scalars().first()
    phq9_band = latest_scr.phq9_severity if latest_scr else "Not Screened"
    gad7_band = latest_scr.gad7_severity if latest_scr else "Not Screened"

    # 4. Fetch recent chat history
    h_query = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_records = h_query.scalars().all()
    chat_history = [{"sender": m.sender, "content": m.content} for m in history_records[-6:]]

    # 5. Generate AI response
    # --- Retrieving context ---
    context_chunks = vector_store.search_hybrid(
        query=msg_in.message.strip(),
        limit=5,
        rerank=True
    )
    
    assistant_text, used_rag = await ai_companion_service.generate_response(
        user_message=msg_in.message.strip(),
        chat_history=chat_history,
        context_chunks=context_chunks,
        phq9_band=phq9_band,
        gad7_band=gad7_band
    )

    # Save Assistant message
    asst_msg = ChatMessage(
        session_id=session.id,
        sender="assistant",
        content=assistant_text,
        risk_flag=False,
        rag_context_used=used_rag
    )
    db.add(asst_msg)
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
