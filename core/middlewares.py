import time
import uuid

from loguru import logger
from fastapi import Response
from starlette.requests import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from conf.config import local_configs

# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware


async def add_process_time_header(
    request: Request, call_next: RequestResponseEndpoint
):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


class LoggingReqRespMiddleware(BaseHTTPMiddleware):
    """logging middleware."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # logger.info()  # 请求内容
        response = await call_next(request)
        # logger.info(response)
        return response  # 响应内容


async def request_id_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    with logger.contextualize(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


roster = [
    # Middleware Func
    add_process_time_header,
    request_id_middleware,
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
    [
        TrustedHostMiddleware,
        {
            "allowed_hosts": local_configs.SERVER.ALLOW_HOSTS,
        },
    ],
    # [LoggingReqRespMiddleware, {}],
]
