from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from ..utils.security import _now, get_session_from_db, create_user_read_from_orm
from ..database import get_db

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, [])
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        conns = self.active_connections.get(user_id) or []
        if websocket in conns:
            conns.remove(websocket)
        if not conns and user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: str, message: Dict[str, Any]):
        conns = self.active_connections.get(user_id) or []
        for ws in conns:
            await ws.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(user_id, message)


ws_manager = ConnectionManager()

router_ws = APIRouter(prefix="/ws", tags=["ws"])

@router_ws.websocket("/notifications")
async def notifications_ws(websocket: WebSocket):
    # WebSocket doesn't have access to dependency injection the same way, 
    # so we manually parse and get DB session
    session_id = websocket.query_params.get("session_id")
    if not session_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Create a temporary DB session for checking auth
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        session = get_session_from_db(db, session_id)
        if not session:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user = create_user_read_from_orm(session.user)
    finally:
        db.close()

    user_id = str(user.id)

    await ws_manager.connect(user_id, websocket)
    try:
        # Send initial welcome + permissions
        await websocket.send_json({
            "type": "WELCOME",
            "message": f"Connected as {user.email}",
            "user_id": user.id,
            "permissions": user.permissions,
            "time": _now().isoformat(),
        })
        while True:
            data = await websocket.receive_text()
            # Echo message back and broadcast a fake NEW_TX event
            await websocket.send_json({
                "type": "ECHO",
                "payload": data,
                "time": _now().isoformat(),
            })
            await ws_manager.send_personal_message(user_id, {
                "type": "NEW_TX",
                "message": "New transaction received (demo).",
                "time": _now().isoformat(),
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
