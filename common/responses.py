import logging
from enum import unique
from math import ceil
from typing import Any, List, Generic, TypeVar, Optional, Sequence
from datetime import datetime

from pydantic import Field, BaseModel, validator
from pydantic.generics import GenericModel
from starlette.responses import JSONResponse

from common.types import IntEnumMore
from common.utils import DATETIME_FORMAT_STRING, datetime_now
from common.schemas import Pager
from common.pydantic import DateTimeFormatConfig

logger = logging.getLogger(__name__)


@unique
class ResponseCodeEnum(IntEnumMore):
    """
    业务响应代码, 除了500之外都在200的前提下返回对应code
    """

    # 唯一成功响应
    success = (0, "成功")

    # custom error code
    failed = (-1, "失败")
    unauthorized = (-2, "invalid or expired credential")
    validation_error = (-3, "参数校验错误")

    # http error code
    internal_error = (500, "内部错误")
    forbidden = (403, "禁止访问")


class AesResponse(JSONResponse):
    """ "
    响应：
    res = {
        "code": 100200,
        "responseTime": "datetime",
        "message": "message",  # 当code不等于100200表示业务错误，该字段返回错误信息
        "data": "data"    # 当code等于100200表示正常调用，该字段返回正常结果
        }
    不直接使用该Response， 使用下面的响应Model - 具有校验/生成文档的功能
    """

    def __init__(
        self, content: Any = None, status_code: int = 200, **kwargs: Any
    ):
        super().__init__(content, status_code=status_code, **kwargs)

    def render(self, content: Any) -> bytes:
        # update responseTime
        content["responseTime"] = datetime_now().strftime(
            DATETIME_FORMAT_STRING
        )
        # if not get_settings().DEBUG:
        #     content = AESUtil(local_configs.AES.SECRET).encrypt_data(ujson.dumps(content))
        return super(AesResponse, self).render(content)


DataT = TypeVar("DataT")


class Resp(GenericModel, Generic[DataT]):
    """
    响应Model
    """

    code: int = Field(
        default=ResponseCodeEnum.success.value,
        description=f"业务响应代码, {ResponseCodeEnum.dict}",
    )
    responseTime: datetime = Field(default=None, description="响应时间")
    message: Optional[str] = Field(default=None, description="响应提示信息")
    data: Optional[DataT] = Field(default=None, description="响应数据格式")

    @validator("data", always=True)
    def check_consistency(cls, v, values):
        if (
            values.get("message") is None
            and values.get("code") != ResponseCodeEnum.success.value
        ):
            raise ValueError(
                f"Must provide a message when code is not {ResponseCodeEnum.success.value}!"
            )
        # if values.get("message") and v:
        # raise ValueError("Response can't provide both message and data!")
        return v

    @classmethod
    def fail(cls, message: str, code: int = ResponseCodeEnum.failed.value):
        return cls(code=code, message=message)

    class Config(DateTimeFormatConfig):
        ...


class SimpleSuccess(Resp):
    """
    简单响应成功
    """


class PageInfo(BaseModel):
    """
    翻页相关信息
    """

    total_page: int
    total_count: int
    size: int
    page: int


class PageResp(Resp, Generic[DataT]):
    page_info: PageInfo = None
    data: Optional[List[DataT]] = None

    __params_type__ = Pager

    @classmethod
    def create(
        cls,
        items: Sequence[DataT],
        total: int,
        pager: Pager,
    ) -> "PageResp[DataT]":
        return cls[DataT](
            data=items, page_info=generate_page_info(total, pager)
        )


def generate_page_info(total_count, pager: Pager):
    return PageInfo(
        total_page=ceil(total_count / pager.limit),
        total_count=total_count,
        size=pager.limit,
        page=pager.offset // pager.limit + 1,
    )
