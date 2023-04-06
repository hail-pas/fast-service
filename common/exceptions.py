from typing import Optional

import ujson
from loguru import logger
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.exceptions import HTTPException

from common.responses import AesResponse, ResponseCodeEnum


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
    return AesResponse(
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )


# ?? 配置 pydantic config未生效
error_msg_template = {
    "value_error.missing": "缺少必填字段",
    "value_error.any_str.max_length": "最长不超过{limit_value}个字符",
    "value_error.any_str.min_length": "至少{limit_value}个字符",
}


async def validation_exception_handler(request, exc):
    """参数校验错误"""
    try:
        error = ujson.loads(exc.json())[0]
        field = error["loc"][0]
        error_type = error["type"]
        ctx = error["ctx"]
        # error['loc'][-1], error['msg']
        # errors = exc.raw_errors[0].exc
        # model = errors.model
        # errors = errors.errors()
        # fields: dict = model.Config.fields
        # field = errors[0]["loc"][0]
        # if field in fields:
        #     field = fields[field].get("description") or field
        # error_type = errors[0]["type"]
        # ctx = errors[0].get("ctx") or {}
        msg = (
            error_msg_template[error_type].format(**ctx)
            if error_type in error_msg_template
            else error["msg"]
        )
    except AttributeError:
        errors = exc.errors()
        field = errors[0]["loc"][0]
        msg = errors[0]["msg"]

    return AesResponse(
        content={
            "code": ResponseCodeEnum.validation_error.value,
            "message": f"{field}: {msg}",
            "data": None,
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
