from typing import List

from loguru import logger
from fastapi import WebSocket


class WSConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            '%s - "WebSocket %s" [accepted]'
            % (
                websocket.scope["client"],
                websocket.scope["root_path"] + websocket.scope["path"],
            )
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(
            '%s - "WebSocket %s" [disconnected]'
            % (
                websocket.scope["client"],
                websocket.scope["root_path"] + websocket.scope["path"],
            )
        )

    async def send_private_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_privete_json(
        self, data: dict, websocket: WebSocket, mode: str = "text"
    ):
        await websocket.send_json(data, mode)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


ws_manager = WSConnectionManager()
