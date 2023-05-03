from contextlib import asynccontextmanager

from loguru import logger
from fastapi import FastAPI, APIRouter
from tortoise import Tortoise
from fastapi_cache import FastAPICache
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_cache.backends.redis import RedisBackend

from conf.config import LocalConfig, local_configs
from common.loguru import init_loguru
from common.fastapi import RespSchemaAPIRouter, setup_sentry
from storages.redis import AsyncRedisUtil, keys
from common.responses import AesResponse
from common.exceptions import setup_exception_handlers
from common.constant.tags import TagsEnum

init_loguru()


class MainApp(FastAPI):
    plugins = {}

    @property
    def settings(self) -> LocalConfig:
        return local_configs


def amount_apps(main_app: FastAPI):
    from apis import roster

    for app_or_router, prefix_path, name in roster:
        assert prefix_path == "" or prefix_path.startswith(
            "/"
        ), "Routed paths must start with '/'"
        if isinstance(app_or_router, FastAPI):
            main_app.mount(prefix_path, app_or_router, name)
        elif isinstance(app_or_router, APIRouter):
            main_app.include_router(app_or_router)


def setup_middleware(main_app: FastAPI):
    """
    ./middlewares 文件中的定义中间件
    :param main_app:
    :return:
    """
    from inspect import isclass, isfunction

    from core.middlewares import roster

    for middle_fc in roster:
        try:
            if isfunction(middle_fc):
                main_app.add_middleware(BaseHTTPMiddleware, dispatch=middle_fc)
            # elif isinstance(middle_fc, list):
            else:
                if isclass(middle_fc[0]):
                    if isinstance(middle_fc[1], dict):
                        main_app.add_middleware(middle_fc[0], **middle_fc[1])
                    else:
                        raise RuntimeError(
                            f"Require Dict as kwargs for middleware class, Got {type(middle_fc[1])}"
                        )
                else:
                    raise RuntimeError(
                        f"Require Class, But Got {type(middle_fc[0])}"
                    )
        except Exception as e:
            logger.error(f"Set Middleware Failed: {middle_fc}, Encounter {e}")


def setup_static_app(main_app: FastAPI, current_settings: LocalConfig):
    """
    init static app
    :param main_app:
    :param current_settings:
    :return:
    """
    static_files_app = StaticFiles(
        directory=current_settings.SERVER.STATIC_DIR
    )
    main_app.mount(
        path=local_configs.SERVER.STATIC_PATH,
        app=static_files_app,
        name="static",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化及退出清理
    # redis
    AsyncRedisUtil.init()
    # cache
    FastAPICache.init(
        RedisBackend(AsyncRedisUtil.get_redis()),
        prefix=f"{keys.RedisKeyPrefix}FastapiCache",
    )

    # tortoise
    await Tortoise.init(config=local_configs.RELATIONAL.tortoise_orm_config)

    yield

    await Tortoise.close_connections()
    await FastAPICache.clear()
    await AsyncRedisUtil.close()


# def init_apps(main_app: FastAPI):
#     # replace with lifespan
#     @main_app.on_event("startup")
#     async def init() -> None:
#         # 初始化redis
#         AsyncRedisUtil.init()
#         # cache
#         FastAPICache.init(RedisBackend(AsyncRedisUtil.get_redis()), prefix=f"{keys.RedisKeyPrefix}FastapiCache")

#     @main_app.on_event("shutdown")
#     async def close() -> None:
#         # 关闭redis
#         await AsyncRedisUtil.close()


def create_app(current_settings: LocalConfig):
    main_app = MainApp(
        debug=current_settings.PROJECT.DEBUG,
        title=current_settings.PROJECT.NAME,
        description=current_settings.PROJECT.DESCRIPTION,
        default_response_class=AesResponse,
        docs_url=local_configs.SERVER.DOCS_URL
        if current_settings.PROJECT.DEBUG
        else None,
        redoc_url=local_configs.SERVER.REDOC_URL,
        version=local_configs.PROJECT.VERSION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": name, "description": description}
            for name, description in TagsEnum.choices
        ],
    )
    main_app.router.route_class = RespSchemaAPIRouter
    main_app.logger = logger
    main_app.servers = [
        {
            "url": f"http://127.0.0.1:{local_configs.SERVER.PORT}",
            "description": "Development environment",
        },
    ] + local_configs.PROJECT.SWAGGER_SERVERS or []
    # thread local just flask like g
    # main_app.add_middleware(GlobalsMiddleware)
    # 挂载apps下的路由 以及 静态资源路由
    amount_apps(main_app)
    setup_static_app(main_app, current_settings)
    # 初始化全局 middleware
    setup_middleware(main_app)
    # 初始化全局 error handling
    setup_exception_handlers(main_app)
    # 初始化 sentry
    if local_configs.PROJECT.SENTRY_DSN:
        setup_sentry(current_settings)

    return main_app


logger.bind(json=True).info(
    {**local_configs.PROJECT.dict(), **local_configs.SERVER.dict()}
)
app = create_app(current_settings=local_configs)
