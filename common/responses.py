from math import ceil
from typing import Generic, TypeVar, Optional
from datetime import datetime
from collections.abc import Sequence

from pydantic import Field, BaseModel
from pydantic.generics import GenericModel
from starlette_context import context
from starlette.responses import JSONResponse

from common.enums import ResponseCodeEnum
from common.utils import DATETIME_FORMAT_STRING, datetime_now
from common.context import ContextKeyEnum
from common.schemas import Pager
from common.pydantic import DateTimeFormatConfig


class AesResponse(JSONResponse):
    """响应：
    res = {
        "code": 0,
        "response_time": "datetime",
        "message": "message",  # 可选信息
        "data": "data"    # 当code等于0表示正常调用，该字段返回正常结果
        "trace_id": "trace_id"  # 请求唯一标识
        }
    不直接使用该Response， 使用下面的响应Model - 具有校验/生成文档的功能.
    """

    def __init__(
        self,
        content: dict = None,
        status_code: int = 200,
        **kwargs,
    ) -> None:
        code = content.get("code", ResponseCodeEnum.success.value)
        context[ContextKeyEnum.response_code.value] = code
        if code != ResponseCodeEnum.success.value:
            context[ContextKeyEnum.response_data.value] = content
        super().__init__(
            content,
            status_code=status_code,
            **kwargs,
        )

    def render(self, content: dict) -> bytes:
        # update response_time
        content["response_time"] = datetime_now().strftime(
            DATETIME_FORMAT_STRING,
        )
        content["trace_id"] = context.get(ContextKeyEnum.request_id.value)
        # if not get_settings().DEBUG:
        #     content = AESUtil(local_configs.AES.SECRET).encrypt_data(ujson.dumps(content))
        return super().render(content)


DataT = TypeVar("DataT")


class Resp(GenericModel, Generic[DataT]):
    """响应Model."""

    code: int = Field(
        default=ResponseCodeEnum.success.value,
        description=f"业务响应代码, {ResponseCodeEnum.dict}",
    )
    response_time: datetime = Field(default=None, description="响应时间")
    message: Optional[str] = Field(default=None, description="响应提示信息")
    data: Optional[DataT] = Field(default=None, description="响应数据格式")
    trace_id: Optional[str] = Field(default=None, description="请求唯一标识")

    # def __init__(__pydantic_self__, **data: Any):
    #     super().__init__(**data)

    # @validator("data", always=True)
    # def check_consistency(cls, v, values):
    #     if (
    #         values.get("message") is None
    #         and values.get("code") != ResponseCodeEnum.success.value
    #     ):
    #         raise ValueError(
    #             f"Must provide a message when code is not {ResponseCodeEnum.success.value}!"
    #         )
    #     return v

    @classmethod
    def fail(
        cls,
        message: str,
        code: int = ResponseCodeEnum.failed.value,
    ) -> "Resp":
        return cls(code=code, message=message)

    class Config(DateTimeFormatConfig):
        ...


class SimpleSuccess(Resp):
    """简单响应成功."""


class PageInfo(BaseModel):
    """翻页相关信息."""

    total_page: int
    total_count: int
    size: int
    page: int


class PageResp(Resp, Generic[DataT]):
    page_info: PageInfo = None
    data: Optional[list[DataT]] = None

    __params_type__ = Pager

    @classmethod
    def create(
        cls,
        items: Sequence[DataT],
        total: int,
        pager: Pager,
    ) -> "PageResp[DataT]":
        return cls[DataT](
            data=items,
            page_info=generate_page_info(total, pager),
        )


def generate_page_info(total_count: int, pager: Pager) -> PageInfo:
    return PageInfo(
        total_page=ceil(total_count / pager.limit),
        total_count=total_count,
        size=pager.limit,
        page=pager.offset // pager.limit + 1,
    )
