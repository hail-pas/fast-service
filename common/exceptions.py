from typing import Optional

import ujson
from loguru import logger
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.exceptions import HTTPException

from common.responses import AesResponse, ResponseCodeEnum
from common.constant.messages import ValidationErrorMsgTemplates


class ApiException(Exception):
    """
    非 0 的业务错误
    """

    code: Optional[int] = ResponseCodeEnum.failed.value
    message: Optional[str] = None

    def __init__(
        self, message: str, code: int = ResponseCodeEnum.failed.value
    ):
        self.code = code
        self.message = message


async def api_exception_handler(request: Request, exc: ApiException):
    return AesResponse(
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.bind(json=True).info(
        {
            "request_form": dict(await request.form()),
            # "request_body": await request.json(),
            "request_path_params": request.path_params,
            "request_query_params": request.query_params._dict,
            "request_headers": dict(request.headers),
        }
    )
    return AesResponse(
        content={
            "code": ResponseCodeEnum.internal_error.value,
            "message": str(exc) or ResponseCodeEnum.internal_error.label,
            "data": None,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HttpException 状态码非 200 的错误
    :param request:
    :param exc:
    :return:
    """
    return AesResponse(
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """参数校验错误"""
    try:
        error = exc.raw_errors[0]
        error_exc = error.exc
        error_exc_data = ujson.loads(error_exc.json())
        field_name = error_exc_data[0]["loc"][0]
        model = error_exc.model
        fields: dict = model.__fields__
        if field_name in fields:
            field_name = (
                fields[field_name].field_info.description or field_name
            )
        error_type = error_exc_data[0]["type"]
        ctx = error_exc_data[0].get("ctx") or {}
        msg = (
            ValidationErrorMsgTemplates[error_type].format(**ctx)
            if error_type in ValidationErrorMsgTemplates
            else error_exc_data[0]["msg"]
        )
    except AttributeError:
        error_exc_data = ujson.loads(exc.json())
        field_name = error_exc_data[0]["loc"][0]
        msg = error_exc_data[0]["msg"]

    return AesResponse(
        content={
            "code": ResponseCodeEnum.validation_error.value,
            "message": f"{field_name}: {msg}",
            "data": error_exc_data,
        }
    )


roster = [
    (RequestValidationError, validation_exception_handler),
    (ApiException, api_exception_handler),
    (HTTPException, http_exception_handler),
    (Exception, unexpected_exception_handler),
]
