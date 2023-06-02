import asyncio
from typing import Any

from loguru import logger
from fastapi import WebSocket
from starlette.endpoints import WebSocketEndpoint

from storages.redis import AsyncRedisUtil


class WebSocketTicks(WebSocketEndpoint):
    encoding = "json"

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.ticker_task = asyncio.create_task(self.tick(websocket))
        logger.info(
            '{} - "WebSocket {}" [accepted]'.format(
                websocket.scope["client"],
                websocket.scope["root_path"] + websocket.scope["path"],
            ),
        )
        await AsyncRedisUtil.incrby("total_ws_conn")
        logger.info(
            f"Current Total Conn: {int(await AsyncRedisUtil.get('total_ws_conn'))}",
        )

    async def on_disconnect(
        self,
        websocket: WebSocket,
        close_code: int,
    ) -> None:
        self.ticker_task.cancel()
        logger.info(
            '{} - "WebSocket {}" [disconnected]'.format(
                websocket.scope["client"],
                websocket.scope["root_path"] + websocket.scope["path"],
            ),
        )
        await AsyncRedisUtil.incrby("total_ws_conn", -1)

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        await websocket.send_json({"Message: ": data})

    async def tick(self, websocket: WebSocket) -> None:
        counter = 0
        while True:
            # logger.info(counter)
            await websocket.send_json({"counter": counter})
            counter += 1
            await asyncio.sleep(1)
