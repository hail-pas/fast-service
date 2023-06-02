import time
import uuid
from typing import Any, Union, Optional
from contextvars import ContextVar

from loguru import logger
from starlette.types import Message
from starlette_context import context
from starlette.requests import Request, HTTPConnection
from starlette.responses import Response
from starlette.datastructures import MutableHeaders
from starlette_context.plugins import Plugin

from common.enums import (
    ContextKeyEnum,
    ResponseCodeEnum,
    InfoLoggerNameEnum,
    ResponseHeaderKeyEnum,
)

request_id_var: ContextVar[str] = ContextVar(
    ContextKeyEnum.request_id.value,
)
response_code_var: ContextVar[int] = ContextVar(
    ContextKeyEnum.response_code.value,
)
response_data_var: ContextVar[dict] = ContextVar(
    ContextKeyEnum.response_data.value,
)


# enrich response 会触发两次 http.response.start、http.response.body
class RequestIdPlugin(Plugin):
    key = ContextKeyEnum.request_id.value

    async def process_request(
        self,
        request: Union[Request, HTTPConnection],
    ) -> Optional[Any]:
        return str(uuid.uuid4())

    async def enrich_response(
        self,
        response: Union[Response, Message],
    ) -> None:
        value = context.get(self.key)
        # for ContextMiddleware
        if isinstance(response, Response):
            response.headers[ResponseHeaderKeyEnum.request_id.value] = value
        # for ContextPureMiddleware
        else:
            if response["type"] == "http.response.start":
                headers = MutableHeaders(scope=response)
                headers.append(ResponseHeaderKeyEnum.request_id.value, value)


class RequestStartTimestampPlugin(Plugin):
    key = ContextKeyEnum.request_start_timestamp.value

    async def process_request(
        self,
        request: Union[Request, HTTPConnection],
    ) -> Optional[Any]:
        return time.time()


class RequestProcessInfoPlugin(Plugin):
    """请求、响应相关的日志"""

    key = ContextKeyEnum.process_time.value

    async def process_request(
        self,
        request: HTTPConnection,
    ) -> Optional[Any]:
        return {
            "method": request.scope["method"],
            "uri": request.scope["path"],
            "client": request.scope.get("client", ("", ""))[0],
        }

    async def enrich_response(
        self,
        response: Union[Response, Message],
    ) -> None:
        process_time = (
            time.time() - context.get(RequestStartTimestampPlugin.key)
        ) * 1000  # ms
        if response["type"] == "http.response.start":
            # for ContextMiddleware
            if isinstance(response, Response):
                response.headers[
                    ResponseHeaderKeyEnum.process_time.value
                ] = str(process_time)
            # for ContextPureMiddleware
            else:
                headers = MutableHeaders(scope=response)
                headers.append(
                    ResponseHeaderKeyEnum.process_time.value,
                    str(process_time),
                )
            return
        info_dict = context.get(self.key)
        info_dict["process_time"] = process_time
        code = context.get(ContextKeyEnum.response_code.value)
        if code is not None and code != ResponseCodeEnum.success.value:
            data = context.get(ContextKeyEnum.response_data.value)
            info_dict["response_data"] = data

        logger.bind(
            name=InfoLoggerNameEnum.info_request_logger.value,
            json=True,
        ).info(info_dict)
