from typing import Union

from loguru import logger
from pyinstrument import Profiler
from fastapi.responses import HTMLResponse
from starlette_context import request_cycle_context
from starlette.requests import Request, HTTPConnection
from starlette.responses import Response
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette_context.plugins import Plugin
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from conf.config import local_configs
from common.context import (
    RequestIdPlugin,
    RequestProcessInfoPlugin,
    RequestStartTimestampPlugin,
)
from common.decorators import SingletonDecorator


async def contex_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    @SingletonDecorator
    class ContextMiddleware:
        plugins: list[Plugin]

        def __init__(self, plugins: list[Plugin]) -> None:
            self.plugins = plugins

        async def set_context(
            self,
            request: Union[Request, HTTPConnection],
        ) -> dict:
            return {
                plugin.key: await plugin.process_request(request)
                for plugin in self.plugins
            }

        async def enrich_response(self, response: Response) -> None:
            for i in self.plugins:
                await i.enrich_response(response)

        async def __call__(
            self,
            request: Request,
            call_next: RequestResponseEndpoint,
        ) -> Response:
            context = await self.set_context(request)
            with request_cycle_context(context), logger.contextualize(
                request_id=context.get(RequestIdPlugin.key),
            ):
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
                response = await call_next(request)
                await self.enrich_response(response)
                return response

    _context_middleware = ContextMiddleware(
        plugins=[
            RequestStartTimestampPlugin(),
            RequestIdPlugin(),
            RequestProcessInfoPlugin(),
        ],
    )

    return await _context_middleware(request, call_next)


roster = [
    # >>>>> Middleware Func
    contex_middleware,
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
