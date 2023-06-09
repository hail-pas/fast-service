import json
import asyncio
import email.message
from enum import Enum
from typing import Any, Union, TypeVar, Callable, Optional
from contextlib import AsyncExitStack
from collections.abc import Sequence, Coroutine

from loguru import logger
from fastapi import FastAPI, params
from pydantic import BaseModel
from fastapi.utils import generate_unique_id, is_body_allowed_for_status_code
from fastapi.routing import (
    APIRoute,
    jsonable_encoder,
    run_in_threadpool,
    run_endpoint_function,
    _prepare_response_content,
)
from pydantic.fields import Undefined, ModelField
from fastapi.encoders import SetIntStr, DictIntStrAny
from starlette.routing import Mount as Mount  # noqa
from starlette.routing import BaseRoute
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.exceptions import HTTPException
from fastapi.datastructures import Default, DefaultPlaceholder
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from fastapi.dependencies.utils import solve_dependencies
from fastapi.dependencies.models import Dependant
from sentry_sdk.integrations.redis import RedisIntegration

from conf.config import LocalConfig
from common.responses import Resp, PageResp, AesResponse
from common.exceptions import setup_exception_handlers


class AuthorizedRequest(Request):
    """add additional attributes to request."""

    _is_super_admin: bool = False

    from storages.relational.models import Role, Account

    def __init__(self, request: Request) -> None:
        super().__init__(
            scope=request.scope,
            receive=request._receive,
            send=request._send,
        )

    @property
    def account(self) -> Account:
        assert (
            "user" in self.scope
        ), "Authentication Dependency must be installed to access request.account"
        return self.scope["user"]

    @property
    def role(self) -> Role:
        assert (
            "role" in self.scope
        ), "Authentication Dependency must be installed to access request.role"
        return self.scope["role"]

    @property
    def is_super_admin(self) -> bool:
        return self._is_super_admin


async def serialize_response(
    *,
    field: Optional[ModelField] = None,
    response_content: any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    is_coroutine: bool = True,
) -> any:
    if isinstance(response_content, (Resp, PageResp)):
        # 兼容 Resp 和 PageResp
        value = response_content.dict()
        return jsonable_encoder(
            value,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=response_content.Config.json_encoders,
        )

    if field:
        errors = []
        response_content = _prepare_response_content(
            response_content,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if is_coroutine:
            value, errors_ = field.validate(
                response_content,
                {},
                loc=("response",),
            )
        else:
            value, errors_ = await run_in_threadpool(
                field.validate,
                response_content,
                {},
                loc=("response",),
            )
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        if errors:
            raise ValidationError(errors, field.type_)
        return jsonable_encoder(
            value,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
    return jsonable_encoder(response_content)


BaseModelType = TypeVar("BaseModelType", bound=BaseModel)


class RespSchemaAPIRouter(APIRoute):
    # default

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: BaseModelType = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[list[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[dict[Union[int, str], dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        name: Optional[str] = None,
        methods: Optional[Union[set[str], list[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[
            Union[SetIntStr, DictIntStrAny]
        ] = None,
        response_model_exclude: Optional[
            Union[SetIntStr, DictIntStrAny]
        ] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[type[Response], DefaultPlaceholder] = Default(
            JSONResponse,
        ),
        dependency_overrides_provider: Optional[Any] = None,
        callbacks: Optional[list[BaseRoute]] = None,
        openapi_extra: Optional[dict[str, Any]] = None,
        generate_unique_id_function: Union[
            Callable[["APIRoute"], str],
            DefaultPlaceholder,
        ] = Default(generate_unique_id),
    ) -> None:
        super().__init__(
            path,
            endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=responses,
            deprecated=deprecated,
            name=name,
            methods=methods,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema,
            response_class=response_class,
            dependency_overrides_provider=dependency_overrides_provider,
            callbacks=callbacks,
            openapi_extra=openapi_extra,
            generate_unique_id_function=generate_unique_id_function,
        )
        if response_model:
            self.responses.update(
                {
                    "default": {
                        "model": response_model,
                        "description": "Successful Response",
                    },
                },
            )

    def get_route_handler(self) -> Callable:
        # 兼容 Resp instance 直接返回，避免重复校验响应体
        # 也可以扩展 MsgPack

        def _get_request_handler(
            dependant: Dependant,
            body_field: Optional[ModelField] = None,
            status_code: Optional[int] = None,
            response_class: Union[
                type[Response],
                DefaultPlaceholder,
            ] = Default(JSONResponse),
            response_field: Optional[ModelField] = None,
            response_model_include: Optional[
                Union[SetIntStr, DictIntStrAny]
            ] = None,
            response_model_exclude: Optional[
                Union[SetIntStr, DictIntStrAny]
            ] = None,
            response_model_by_alias: bool = True,
            response_model_exclude_unset: bool = False,
            response_model_exclude_defaults: bool = False,
            response_model_exclude_none: bool = False,
            dependency_overrides_provider: Optional[Any] = None,
        ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
            assert (
                dependant.call is not None
            ), "dependant.call must be a function"
            is_coroutine = asyncio.iscoroutinefunction(dependant.call)
            is_body_form = body_field and isinstance(
                body_field.field_info,
                params.Form,
            )
            if isinstance(response_class, DefaultPlaceholder):
                actual_response_class: type[Response] = response_class.value
            else:
                actual_response_class = response_class

            async def app(request: Request) -> Response:
                request = AuthorizedRequest(request)
                try:
                    body: Any = None
                    if body_field:
                        if is_body_form:
                            body = await request.form()
                            stack = request.scope.get("fastapi_astack")
                            assert isinstance(stack, AsyncExitStack)
                            stack.push_async_callback(body.close)
                        else:
                            body_bytes = await request.body()
                            if body_bytes:
                                json_body: Any = Undefined
                                content_type_value = request.headers.get(
                                    "content-type",
                                )
                                if not content_type_value:
                                    json_body = await request.json()
                                else:
                                    message = email.message.Message()
                                    message[
                                        "content-type"
                                    ] = content_type_value
                                    if (
                                        message.get_content_maintype()
                                        == "application"
                                    ):
                                        subtype = message.get_content_subtype()
                                        if (
                                            subtype == "json"
                                            or subtype.endswith("+json")
                                        ):
                                            json_body = await request.json()
                                body = (
                                    json_body
                                    if json_body != Undefined
                                    else body_bytes
                                )
                except json.JSONDecodeError as e:
                    raise RequestValidationError(
                        [ErrorWrapper(e, ("body", e.pos))],
                        body=e.doc,
                    ) from e
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail="There was an error parsing the body",
                    ) from e
                solved_result = await solve_dependencies(
                    request=request,
                    dependant=dependant,
                    body=body,
                    dependency_overrides_provider=dependency_overrides_provider,
                )
                (
                    values,
                    errors,
                    background_tasks,
                    sub_response,
                    _,
                ) = solved_result
                if errors:
                    raise RequestValidationError(errors, body=body)
                raw_response = await run_endpoint_function(
                    dependant=dependant,
                    values=values,
                    is_coroutine=is_coroutine,
                )

                if isinstance(raw_response, Response):
                    if raw_response.background is None:
                        raw_response.background = background_tasks
                    return raw_response

                response_args: dict[str, Any] = {
                    "background": background_tasks,
                }
                # If status_code was set, use it, otherwise use the default from the
                # response class, in the case of redirect it's 307
                current_status_code = (
                    status_code if status_code else sub_response.status_code
                )
                if current_status_code is not None:
                    response_args["status_code"] = current_status_code
                if sub_response.status_code:
                    response_args["status_code"] = sub_response.status_code
                if isinstance(raw_response, Response):
                    content = raw_response.body
                else:
                    content = await serialize_response(
                        field=response_field,
                        response_content=raw_response,
                        include=response_model_include,
                        exclude=response_model_exclude,
                        by_alias=response_model_by_alias,
                        exclude_unset=response_model_exclude_unset,
                        exclude_defaults=response_model_exclude_defaults,
                        exclude_none=response_model_exclude_none,
                        is_coroutine=is_coroutine,
                    )
                response = actual_response_class(content, **response_args)
                if not is_body_allowed_for_status_code(
                    response.status_code,
                ):
                    response.body = b""
                response.headers.raw.extend(sub_response.headers.raw)
                return response

            return app

        return _get_request_handler(
            dependant=self.dependant,
            body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class,
            response_field=self.secure_cloned_response_field,
            response_model_include=self.response_model_include,
            response_model_exclude=self.response_model_exclude,
            response_model_by_alias=self.response_model_by_alias,
            response_model_exclude_unset=self.response_model_exclude_unset,
            response_model_exclude_defaults=self.response_model_exclude_defaults,
            response_model_exclude_none=self.response_model_exclude_none,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )


def setup_sub_app(app: FastAPI, app_prefix: str) -> None:
    from conf.config import local_configs

    app.router.route_class = RespSchemaAPIRouter
    app.logger = logger
    setup_exception_handlers(app)
    for server in local_configs.PROJECT.SWAGGER_SERVERS or []:
        app.servers.append(
            {
                "url": f"{server['url']}/{app_prefix}",
                "description": server["description"],
            },
        )
    app.debug = local_configs.PROJECT.DEBUG
    app.default_response_class = AesResponse
    app.version = local_configs.PROJECT.VERSION
    return app


def setup_sentry(current_settings: LocalConfig) -> None:
    """Init sentry
    :param current_settings:
    :return:
    """
    import sentry_sdk

    sentry_sdk.init(
        dsn=current_settings.PROJECT.SENTRY_DSN,
        environment=current_settings.PROJECT.ENVIRONMENT,
        integrations=[RedisIntegration()],
        traces_sample_rate=0.2,
        _experiments={
            "profiles_sample_rate": 0.1,
        },
    )
