"""
fixer.ai — WebSocket endpoint for live sensor streaming

One WebSocket connection per machine per frontend client.
The simulator calls broadcast_to_machine() on each tick.
Multiple clients can connect to the same machine simultaneously (for demo).

URL: ws://localhost:8000/ws/sensors/{machine_id}
"""
import asyncio
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.simulation.simulator import set_ws_broadcast_callback

router = APIRouter()

# machine_id → set of connected WebSocket clients
_connections: dict[str, set[WebSocket]] = defaultdict(set)


async def broadcast_to_machine(machine_id: str, payload: str):
    """Called by simulator on each tick to push readings to all connected clients."""
    dead = set()
    for ws in _connections.get(machine_id, set()):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections[machine_id].discard(ws)



@router.websocket("/ws/sensors/{machine_id}")
async def sensor_stream(websocket: WebSocket, machine_id: str):
    """
    WebSocket endpoint for live sensor data.
    Frontend connects here; receives JSON sensor readings each simulator tick.
    """
    await websocket.accept()
    _connections[machine_id].add(websocket)

    try:
        # Keep connection alive; client can also send messages (e.g. ping)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong from frontend
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_text('{"type":"keepalive"}')
    except WebSocketDisconnect:
        pass
    finally:
        _connections[machine_id].discard(websocket)
