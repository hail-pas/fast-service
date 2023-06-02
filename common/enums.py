from enum import unique

from common.types import IntEnumMore, StrEnumMore
from common.constant.messages import (
    FailedMsg,
    SuccessMsg,
    FrobiddenMsg,
    UnauthorizedMsg,
    ParameterErrorMsg,
    InternalServerErrorMsg,
)


@unique
class ResponseCodeEnum(IntEnumMore):
    """业务响应代码, 除了500之外都在200的前提下返回对应code."""

    # 唯一成功响应
    success = (0, SuccessMsg)

    # custom error code
    failed = (-1, FailedMsg)
    unauthorized = (-2, UnauthorizedMsg)
    validation_error = (-3, ParameterErrorMsg)

    # http error code
    internal_error = (500, InternalServerErrorMsg)
    forbidden = (403, FrobiddenMsg)


@unique
class ResponseHeaderKeyEnum(StrEnumMore):
    """响应头key"""

    request_id = ("X-Request-Id", "请求唯一ID")
    process_time = ("X-Process-Time", "请求处理时间")  # ms


@unique
class InfoLoggerNameEnum(StrEnumMore):
    """统计数据相关日志名称."""

    # 请求相关日志
    info_request_logger = ("_info.request", "请求数据统计日志")


@unique
class ContextKeyEnum(StrEnumMore):
    """上下文变量key."""

    # plugins
    request_id = ("request_id", "请求ID")
    request_start_timestamp = ("request_start_timestamp", "请求开始时间")
    process_time = ("process_time", "请求处理时间/ms")

    # custom
    response_code = ("response_code", "响应code")
    response_data = ("response_data", "响应数据")  #  只记录code != 0 的
