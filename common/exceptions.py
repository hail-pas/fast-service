from typing import Optional

import ujson
from loguru import logger
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.exceptions import HTTPException

from common.responses import AesResponse, ResponseCodeEnum
from common.constant.messages import ValidationErrorMsgTemplates


async def unexpected_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return AesResponse(
        content={
            "code": ResponseCodeEnum.internal_error.value,
            "message": str(exc) or ResponseCodeEnum.internal_error.label,
            "data": None,
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HttpException 状态码非 200 的错误
    :param request:
    :param exc:
    :return:
    """
    logger.bind(json=True).warning(
        {"code": exc.status_code, "message": exc.detail}
    )
    return AesResponse(
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )


async def validation_exception_handler(request, exc):
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

    logger.bind(json=True).warning(
        {
            "code": ResponseCodeEnum.validation_error.value,
            "field": field_name,
            "message": msg,
        }
    )
    return AesResponse(
        content={
            "code": ResponseCodeEnum.validation_error.value,
            "message": f"{field_name}: {msg}",
            "data": error_exc_data,
        }
    )


class ApiException(Exception):
    """
    非 0 的业务错误
    """

    code: Optional[int] = ResponseCodeEnum.failed.value
    message: Optional[str] = None

    def __init__(
        self, message: str, code: int = ResponseCodeEnum.failed.value
    ):
        logger.bind(json=True).warning({"code": code, "message": message})
        self.code = code
        self.message = message

    def to_result(self):
        return AesResponse(
            content={"code": self.code, "message": self.message, "data": None}
        )


roster = [
    (HTTPException, http_exception_handler),
    (Exception, unexpected_exception_handler),
    (RequestValidationError, validation_exception_handler),
]
