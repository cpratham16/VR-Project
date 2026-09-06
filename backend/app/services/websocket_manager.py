"""WebSocket connection manager for chat rooms."""
from typing import Dict, List, Set
from uuid import UUID
from fastapi import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for chat rooms."""
    
    def __init__(self):
        # room_id -> {user_id: websocket}
        self.room_connections: Dict[UUID, Dict[UUID, WebSocket]] = {}
        # websocket -> (room_id, user_id)
        self.websocket_info: Dict[WebSocket, tuple] = {}
        # user_id -> set of room_ids they're connected to
        self.user_rooms: Dict[UUID, Set[UUID]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: UUID, user_id: UUID):
        """Accept a new WebSocket connection for a room."""
        await websocket.accept()
        
        if room_id not in self.room_connections:
            self.room_connections[room_id] = {}
        self.room_connections[room_id][user_id] = websocket
        self.websocket_info[websocket] = (room_id, user_id)
        
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room_id)
        
        logger.info(f"User {user_id} connected to room {room_id}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket not in self.websocket_info:
            return
            
        room_id, user_id = self.websocket_info[websocket]
        del self.websocket_info[websocket]
        
        if room_id in self.room_connections and user_id in self.room_connections[room_id]:
            del self.room_connections[room_id][user_id]
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]
                
        logger.info(f"User {user_id} disconnected from room {room_id}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            
    async def broadcast_to_room(self, room_id: UUID, message: dict, exclude_user: UUID = None):
        """Broadcast a message to all connected users in a room."""
        if room_id not in self.room_connections:
            return
            
        message_text = json.dumps(message)
        disconnected = []
        
        for user_id, websocket in self.room_connections[room_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                disconnected.append((room_id, user_id))
                
        # Clean up disconnected websockets
        for room_id, user_id in disconnected:
            self.disconnect_user(room_id, user_id)
            
    def disconnect_user(self, room_id: UUID, user_id: UUID):
        """Disconnect a specific user from a room."""
        if room_id in self.room_connections and user_id in self.room_connections[room_id]:
            ws = self.room_connections[room_id].pop(user_id)
            if ws in self.websocket_info:
                del self.websocket_info[ws]
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
            
    def get_room_participants(self, room_id: UUID) -> List[UUID]:
        """Get list of connected user IDs in a room."""
        if room_id in self.room_connections:
            return list(self.room_connections[room_id].keys())
        return []
        
    def is_user_in_room(self, user_id: UUID, room_id: UUID) -> bool:
        """Check if a user is connected to a room."""
        return room_id in self.room_connections and user_id in self.room_connections[room_id]

manager = ConnectionManager()