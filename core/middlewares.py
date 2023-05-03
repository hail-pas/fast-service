import time

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
from common.utils import get_or_set_request_id
from common.loguru import log_info_request


# 执行顺序：从上到下
async def base_request_middleware(
    request: Request, call_next: RequestResponseEndpoint
):
    start_time = time.time()
    request_id = get_or_set_request_id()
    with logger.contextualize(request_id=request_id):
        # 请求id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # 请求处理时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(int(process_time * 1000))

        # 请求相关信息
        await log_info_request(request, response)

        return response


class LoggingReqRespMiddleware(BaseHTTPMiddleware):
    """logging middleware."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 未使用

        # logger.info()  # 请求内容
        response = await call_next(request)
        # logger.info(response)
        return response  # 响应内容


roster = [
    # Middleware Func
    base_request_middleware,
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
