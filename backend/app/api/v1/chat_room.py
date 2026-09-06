"""Chat room API with WebSocket support for real-time messaging."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.chat_room import ChatRoom, ChatRoomParticipant, ChatRoomMessage, ChatRoomType
from app.api.deps import get_current_user
from app.schemas.chat_room import (
    ChatRoomCreate, ChatRoomUpdate, ChatRoomResponse, ChatRoomListResponse,
    ChatRoomParticipantResponse, ChatRoomMessageCreate, ChatRoomMessageUpdate,
    ChatRoomMessageResponse, ChatRoomMessagesResponse, ChatRoomType
)
from app.services.websocket_manager import manager
from app.core.security import verify_password, get_password_hash

router = APIRouter(prefix="/chat", tags=["chat_rooms"])

# ========== Room Management ==========

@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(
    room_in: ChatRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat room (admin/doctor only)."""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Only admins and doctors can create chat rooms")
    
    # Check if room type already exists
    existing = await db.execute(
        select(ChatRoom).where(ChatRoom.room_type == room_in.room_type)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Chat room type already exists")
    
    room = ChatRoom(**room_in.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    
    return room

@router.get("/rooms", response_model=ChatRoomListResponse)
async def list_chat_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available chat rooms for the user."""
    query = select(ChatRoom).where(ChatRoom.is_active == True)
    result = await db.execute(query)
    rooms = result.scalars().all()
    
    # Get participant counts and unread counts
    room_ids = [r.id for r in rooms]
    participant_counts = {}
    unread_counts = {}
    
    if room_ids:
        # Get participant counts
        pc_query = await db.execute(
            select(ChatRoomParticipant.room_id, func.count(ChatRoomParticipant.id))
            .where(ChatRoomParticipant.room_id.in_(room_ids))
            .group_by(ChatRoomParticipant.room_id)
        )
        participant_counts = {row[0]: row[1] for row in pc_query.all()}
        
        # Get unread counts for current user
        uc_query = await db.execute(
            select(ChatRoomMessage.room_id, func.count(ChatRoomMessage.id))
            .join(ChatRoomParticipant, ChatRoomMessage.room_id == ChatRoomParticipant.room_id)
            .where(
                ChatRoomParticipant.user_id == current_user.id,
                ChatRoomMessage.sender_id != current_user.id,
                ChatRoomMessage.created_at > ChatRoomParticipant.last_read_at
            )
            .group_by(ChatRoomMessage.room_id)
        )
        unread_counts = {row[0]: row[1] for row in uc_query.all()}
    
    result = []
    for room in rooms:
        result.append(ChatRoomResponse(
            **room.__dict__,
            participant_count=participant_counts.get(room.id, 0),
            unread_count=unread_counts.get(room.id, 0)
        ))
    
    return ChatRoomListResponse(rooms=result)

@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat room."""
    room = await db.get(ChatRoom, room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    # Get participant count
    pc = await db.execute(
        select(func.count(ChatRoomParticipant.id))
        .where(ChatRoomParticipant.room_id == room_id)
    )
    participant_count = pc.scalar() or 0
    
    # Get unread count for current user
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    participant = participant.scalars().first()
    
    unread = 0
    if participant and participant.last_read_at:
        uc = await db.execute(
            select(func.count(ChatRoomMessage.id))
            .where(
                ChatRoomMessage.room_id == room_id,
                ChatRoomMessage.sender_id != current_user.id,
                ChatRoomMessage.created_at > participant.last_read_at
            )
        )
        unread = uc.scalar() or 0
    elif participant:
        uc = await db.execute(
            select(func.count(ChatRoomMessage.id))
            .where(
                ChatRoomMessage.room_id == room_id,
                ChatRoomMessage.sender_id != current_user.id
            )
        )
        unread = uc.scalar() or 0
    
    return ChatRoomResponse(
        **room.__dict__,
        participant_count=participant_count,
        unread_count=unread
    )

@router.post("/rooms/{room_id}/join")
async def join_chat_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join a chat room."""
    room = await db.get(ChatRoom, room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    # Check if already a participant
    existing = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    if existing.scalars().first():
        return {"message": "Already a member", "room_id": str(room_id)}
    
    participant = ChatRoomParticipant(
        room_id=room_id,
        user_id=current_user.id,
        role="member"
    )
    db.add(participant)
    await db.commit()
    
    return {"message": "Joined room successfully", "room_id": str(room_id)}

@router.delete("/rooms/{room_id}/leave")
async def leave_chat_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Leave a chat room."""
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    participant = participant.scalars().first()
    if not participant:
        raise HTTPException(status_code=404, detail="Not a member of this room")
    
    await db.delete(participant)
    await db.commit()
    
    return {"message": "Left room successfully"}

# ========== Message Management ==========

@router.post("/rooms/{room_id}/messages", response_model=ChatRoomMessageResponse)
async def send_message(
    room_id: UUID,
    message_in: ChatRoomMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a chat room."""
    # Verify room exists and user is participant
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    if not participant.scalars().first():
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    # Check if muted
    participant_obj = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    participant_obj = participant_obj.scalars().first()
    if participant_obj and participant_obj.is_muted:
        raise HTTPException(status_code=403, detail="You are muted in this room")
    
    # Validate reply_to if provided
    if message_in.reply_to_id:
        reply_msg = await db.get(ChatRoomMessage, message_in.reply_to_id)
        if not reply_msg or reply_msg.room_id != room_id:
            raise HTTPException(status_code=400, detail="Invalid reply_to_id")
    
    message = ChatRoomMessage(
        room_id=room_id,
        sender_id=current_user.id,
        content=message_in.content,
        message_type=message_in.message_type,
        reply_to_id=message_in.reply_to_id
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Update participant's last_read_at
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    p = participant.scalars().first()
    if p:
        p.last_read_at = datetime.utcnow()
        await db.commit()
    
    return ChatRoomMessageResponse(
        **message.__dict__,
        sender_pseudonym="You"
    )

@router.get("/rooms/{room_id}/messages", response_model=ChatRoomMessagesResponse)
async def get_messages(
    room_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a chat room with pagination."""
    # Verify participant
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == current_user.id)
    )
    if not participant.scalars().first():
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    query = select(ChatRoomMessage).where(
        ChatRoomMessage.room_id == room_id,
        ChatRoomMessage.is_deleted == False
    )
    
    if before:
        query = query.where(ChatRoomMessage.created_at < before)
    
    query = query.order_by(desc(ChatRoomMessage.created_at)).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()
    messages.reverse()  # Return in chronological order
    
    # Get sender pseudonyms
    sender_ids = set(m.sender_id for m in messages)
    pseudonyms = {}
    if sender_ids:
        from app.models.user import User
        users = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(sender_ids))
        )
        pseudonyms = {str(u[0]): u[1] or f"User {str(u[0])[:8]}" for u in users.all()}
    
    result_messages = []
    for msg in messages:
        result_messages.append(ChatRoomMessageResponse(
            **msg.__dict__,
            sender_pseudonym=pseudonyms.get(str(msg.sender_id), "Anonymous")
        ))
    
    # Next cursor for pagination
    next_cursor = messages[0].created_at.isoformat() if messages else None
    
    return ChatRoomMessagesResponse(messages=result_messages, next_cursor=next_cursor)

@router.put("/messages/{message_id}", response_model=ChatRoomMessageResponse)
async def update_message(
    message_id: UUID,
    message_in: ChatRoomMessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit a message."""
    message = await db.get(ChatRoomMessage, message_id)
    if not message or message.sender_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")
    
    if message_in.content is not None:
        message.content = message_in.content
        message.edited_at = datetime.utcnow()
        message.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return ChatRoomMessageResponse(**message.__dict__, sender_pseudonym="You")

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a message."""
    message = await db.get(ChatRoomMessage, message_id)
    if not message or message.sender_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")
    
    message.is_deleted = True
    message.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Message deleted"}

# ========== Moderation (Admin/Moderator) ==========

@router.delete("/rooms/{room_id}/messages/{message_id}")
async def moderate_delete_message(
    room_id: UUID,
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Moderator/admin delete any message in a room."""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Moderator or admin only")
    
    message = await db.get(ChatRoomMessage, message_id)
    if not message or message.room_id != room_id:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.is_deleted = True
    message.updated_at = datetime.utcnow()
    await db.commit()
    
    # Broadcast deletion
    await manager.broadcast_to_room(room_id, {
        "type": "message_deleted",
        "message_id": str(message_id)
    })
    
    return {"message": "Message deleted by moderator"}

@router.post("/rooms/{room_id}/mute/{user_id}")
async def mute_user(
    room_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mute a user in a room (moderator/admin only)."""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Moderator or admin only")
    
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == user_id)
    )
    participant = participant.scalars().first()
    if not participant:
        raise HTTPException(status_code=404, detail="User not in this room")
    
    if participant.role in ["moderator", "doctor"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot mute moderator/doctor")
    
    participant.is_muted = True
    await db.commit()
    
    # Notify
    await manager.broadcast_to_room(room_id, {
        "type": "user_muted",
        "user_id": str(user_id)
    })
    
    return {"message": "User muted"}

@router.post("/rooms/{room_id}/unmute/{user_id}")
async def unmute_user(
    room_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unmute a user in a room (moderator/admin only)."""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Moderator or admin only")
    
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == user_id)
    )
    participant = participant.scalars().first()
    if not participant:
        raise HTTPException(status_code=404, detail="User not in this room")
    
    participant.is_muted = False
    await db.commit()
    
    await manager.broadcast_to_room(room_id, {
        "type": "user_unmuted",
        "user_id": str(user_id)
    })
    
    return {"message": "User unmuted"}

@router.get("/rooms/{room_id}/participants", response_model=List[ChatRoomParticipantResponse])
async def list_participants(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all participants in a room (moderator/admin only)."""
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(status_code=403, detail="Moderator or admin only")
    
    result = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id)
    )
    participants = result.scalars().all()
    
    return [ChatRoomParticipantResponse.model_validate(p) for p in participants]

@router.patch("/rooms/{room_id}/participants/{user_id}/role")
async def update_participant_role(
    room_id: UUID,
    user_id: UUID,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a participant's role (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    if role not in ["member", "moderator", "doctor"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    participant = await db.execute(
        select(ChatRoomParticipant)
        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == user_id)
    )
    participant = participant.scalars().first()
    if not participant:
        raise HTTPException(status_code=404, detail="User not in this room")
    
    participant.role = role
    await db.commit()
    
    return {"message": f"Role updated to {role}"}

# ========== WebSocket ==========

@router.websocket("/rooms/{room_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time chat."""
    # Verify token and get user
    from app.core.security import decode_token
    from app.models.user import User
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify user exists and is participant
    async with AsyncSessionLocal() as db_session:
        participant = await db_session.execute(
            select(ChatRoomParticipant)
            .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == UUID(user_id))
        )
        if not participant.scalars().first():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Connect
    await manager.connect(websocket, room_id, UUID(user_id))
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            msg_type = message_data.get("type", "message")
            
            if msg_type == "message":
                # Send new message
                content = message_data.get("content", "").strip()
                reply_to_id = message_data.get("reply_to_id")
                
                if not content:
                    continue
                
                async with AsyncSessionLocal() as db_session:
                    # Verify still participant
                    part = await db_session.execute(
                        select(ChatRoomParticipant)
                        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == UUID(user_id))
                    )
                    if not part.scalars().first():
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        return
                    
                    # Check mute
                    part = await db_session.execute(
                        select(ChatRoomParticipant)
                        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == UUID(user_id))
                    )
                    p_obj = part.scalars().first()
                    if p_obj and p_obj.is_muted:
                        await manager.send_personal_message({"error": "You are muted"}, websocket)
                        continue
                    
                    # Create message
                    message = ChatRoomMessage(
                        room_id=room_id,
                        sender_id=UUID(user_id),
                        content=message_data.get("content", "").strip(),
                        message_type="text",
                        reply_to_id=UUID(reply_to_id) if reply_to_id else None
                    )
                    db_session.add(message)
                    await db_session.commit()
                    await db_session.refresh(message)
                    
                    # Update last_read_at
                    part = await db_session.execute(
                        select(ChatRoomParticipant)
                        .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == UUID(user_id))
                    )
                    p = part.scalars().first()
                    if p:
                        p.last_read_at = datetime.utcnow()
                        await db_session.commit()
                    
                    # Broadcast to room
                    await manager.broadcast_to_room(room_id, {
                        "type": "new_message",
                        "message": {
                            "id": str(message.id),
                            "room_id": str(room_id),
                            "sender_id": str(current_user.id),
                            "content": message.content,
                            "message_type": message.message_type,
                            "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
                            "created_at": message.created_at.isoformat(),
                            "sender_pseudonym": "You"  # Will be replaced by client
                        }
                    }, exclude_user=UUID(user_id))
                    
            elif msg_type == "read_receipt":
                # Mark messages as read
                message_ids = message_data.get("message_ids", [])
                if message_ids:
                    async with AsyncSessionLocal() as db_session:
                        part = await db_session.execute(
                            select(ChatRoomParticipant)
                            .where(ChatRoomParticipant.room_id == room_id, ChatRoomParticipant.user_id == UUID(user_id))
                        )
                        p = part.scalars().first()
                        if p:
                            p.last_read_at = datetime.utcnow()
                            await db_session.commit()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)