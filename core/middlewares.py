import time

from loguru import logger
from fastapi import Response
from starlette.requests import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.middleware.cors import CORSMiddleware

from conf.config import local_configs


async def add_process_time_header(
    request: Request, call_next: RequestResponseEndpoint
):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """logging middleware."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        logger.info()  # 请求内容
        response = await call_next(request)
        logger.info(response)
        return response  # 响应内容


roster = [
    # Middleware Func
    add_process_time_header,
    # Middleware Class
    [
        CORSMiddleware,
        {
            "allow_origins": local_configs.SERVER.CORS.ALLOW_ORIGIN,
            "allow_credentials": local_configs.SERVER.CORS.ALLOW_CREDENTIAL,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
    ],
    # [LoggingMiddleware, {}],
]
