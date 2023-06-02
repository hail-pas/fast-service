from typing import Union

from fastapi import Query, Depends, APIRouter

from storages import enums
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp

router = APIRouter(prefix="/common", route_class=RespSchemaAPIRouter)


@router.get(
    "/enum",
    description="枚举-列表",
    summary="枚举表",
    response_model=Resp[Union[dict, tuple[tuple]]],
)
async def enum_content(
    enum_content: dict = Depends(enums.get_enum_content),
    format: enums.RespFormatEnum = Query(
        default=enums.RespFormatEnum.json_,
        description="返回格式",
    ),
) -> Resp[Union[dict, tuple]]:
    data = enum_content
    if format == enums.RespFormatEnum.list_:
        data = []
        for k, v in enum_content.items():
            data.append((k, tuple(v.items())))
    return Resp[Union[dict, tuple]](data=data)
