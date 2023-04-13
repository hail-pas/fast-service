import json
import asyncio
import email.message
from typing import Any, Dict, Type, Union, Callable, Optional, Coroutine
from contextlib import AsyncExitStack

from fastapi import params
from fastapi.utils import is_body_allowed_for_status_code
from fastapi.routing import jsonable_encoder  # serialize_response,
from fastapi.routing import (
    APIRoute,
    run_in_threadpool,
    run_endpoint_function,
    _prepare_response_content,
)
from pydantic.fields import Undefined, ModelField
from fastapi.encoders import SetIntStr, DictIntStrAny
from starlette.routing import Mount as Mount  # noqa
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.exceptions import HTTPException
from fastapi.datastructures import Default, DefaultPlaceholder
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from fastapi.dependencies.utils import solve_dependencies
from fastapi.dependencies.models import Dependant

from common.responses import Resp, PageResp


async def serialize_response(
    *,
    field: Optional[ModelField] = None,
    response_content: Any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    is_coroutine: bool = True,
) -> Any:
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
                response_content, {}, loc=("response",)
            )
        else:
            value, errors_ = await run_in_threadpool(
                field.validate, response_content, {}, loc=("response",)
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
    else:
        return jsonable_encoder(response_content)


class RespSchemaAPIRouter(APIRoute):
    def get_route_handler(self) -> Callable:
        # 兼容 Resp instance 直接返回，避免重复校验响应体
        # 也可以扩展 MsgPack

        def _get_request_handler(
            dependant: Dependant,
            body_field: Optional[ModelField] = None,
            status_code: Optional[int] = None,
            response_class: Union[
                Type[Response], DefaultPlaceholder
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
                body_field.field_info, params.Form
            )
            if isinstance(response_class, DefaultPlaceholder):
                actual_response_class: Type[Response] = response_class.value
            else:
                actual_response_class = response_class

            async def app(request: Request) -> Response:
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
                                    "content-type"
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
                                if json_body != Undefined:
                                    body = json_body
                                else:
                                    body = body_bytes
                except json.JSONDecodeError as e:
                    raise RequestValidationError(
                        [ErrorWrapper(e, ("body", e.pos))], body=e.doc
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
                else:
                    raw_response = await run_endpoint_function(
                        dependant=dependant,
                        values=values,
                        is_coroutine=is_coroutine,
                    )

                    if isinstance(raw_response, Response):
                        if raw_response.background is None:
                            raw_response.background = background_tasks
                        return raw_response

                    response_args: Dict[str, Any] = {
                        "background": background_tasks
                    }
                    # If status_code was set, use it, otherwise use the default from the
                    # response class, in the case of redirect it's 307
                    current_status_code = (
                        status_code
                        if status_code
                        else sub_response.status_code
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
                        response.status_code
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
