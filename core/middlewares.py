import time

from loguru import logger
from fastapi import Response
from starlette.requests import Request
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from conf.config import local_configs
from common.utils import get_or_set_request_id
from common.loguru import InfoLoggerNameEnum
from common.responses import ResponseCodeEnum


# 执行顺序：从上到下
async def add_process_time_header(
    request: Request, call_next: RequestResponseEndpoint
):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(int(process_time * 1000))
    response_code = response.headers["x-response-code"]
    info_dict = {
        "method": request.method,
        "url": request.url.path,
        # "request_id": get_request_id(),
        "process_time": response.headers["X-Process-Time"],
    }
    if response_code != str(ResponseCodeEnum.success.value):
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        info_dict["response_data"] = response_body[0].decode("utf-8")
    logger.bind(
        name=InfoLoggerNameEnum.info_request_logger.value, json=True
    ).info(info_dict)
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
    request_id = get_or_set_request_id()
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
