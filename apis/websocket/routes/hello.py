from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from apis.websocket.manage import ws_manager

# @ws_app.websocket("/example")


async def func_websocket_route(websocket: WebSocket, client_id: int):
    await ws_manager.connect(websocket)
    try:
        await ws_manager.send_privete_json(
            {"msg": "Hello WebSocket"},
            websocket,
        )
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_private_message(
                f"You wrote: {data}",
                websocket,
            )
            await ws_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await ws_manager.broadcast(f"Client #{client_id} left the chat")
