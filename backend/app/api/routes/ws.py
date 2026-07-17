from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.ws_manager import connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/activity")
async def activity_stream(websocket: WebSocket) -> None:
    await connection_manager.connect(websocket)
    try:
        while True:
            # Dashboard clients don't need to send anything; this just keeps
            # the connection open and detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
