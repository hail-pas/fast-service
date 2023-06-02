from loguru import logger
from pyinstrument import Profiler
from starlette.types import Send, Scope, Message, Receive
from fastapi.responses import HTMLResponse
from starlette_context import request_cycle_context

# from fastapi import Response
from starlette.requests import Request
from starlette.responses import Response
from starlette_context.errors import MiddleWareValidationError
from starlette.middleware.base import (
    RequestResponseEndpoint,
)  # BaseHTTPMiddleware,
from starlette.middleware.cors import CORSMiddleware
from starlette_context.middleware import RawContextMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from conf.config import local_configs
from common.context import (
    RequestIdPlugin,
    RequestProcessInfoPlugin,
    RequestStartTimestampPlugin,
)


class LogWithContextMiddleware(RawContextMiddleware):
    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return None

        async def send_wrapper(message: Message) -> None:
            for plugin in self.plugins:
                await plugin.enrich_response(message)
            await send(message)

        request = self.get_request_object(scope, receive, send)

        try:
            context = await self.set_context(request)
        except MiddleWareValidationError as e:
            error_response = e.error_response or self.error_response
            return await self.send_response(error_response, send)

        with request_cycle_context(context), logger.contextualize(
            request_id=context.get(RequestIdPlugin.key),
        ):
            await self.app(scope, receive, send_wrapper)
            return None


async def profile_request(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    need_profile = request.query_params.get("profile", False)
    secret = request.query_params.get("secret", "")
    if need_profile and secret == local_configs.PROFILING.SECRET:
        profiler = Profiler(
            interval=local_configs.PROFILING.INTERVAL,
            async_mode="enabled",
        )
        profiler.start()
        await call_next(request)
        profiler.stop()
        return HTMLResponse(profiler.output_html())
    return await call_next(request)


roster = [
    # >>>>> Middleware Func
    [
        LogWithContextMiddleware,
        {
            "plugins": (
                RequestStartTimestampPlugin(),
                RequestIdPlugin(),
                RequestProcessInfoPlugin(),
            ),
        },
    ],
    # profile_request,
    # >>>>> Middleware Class
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
