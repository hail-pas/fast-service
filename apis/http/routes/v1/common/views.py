import uuid
from typing import Union, Literal

from fastapi import Body, Query, Depends, APIRouter
from captcha.image import ImageCaptcha
from fastapi.responses import StreamingResponse

from storages import enums
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp
from storages.redis.utils import generate_capthca_code
from apis.http.routes.v1.common.responses import CaptchaCodeResponse

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


@router.get(
    "/captcha/image",
    summary="图片验证码",
    description="图片验证码, unique_key附带在响应头中",
)
async def captcha_image() -> StreamingResponse:
    image = ImageCaptcha()
    unique_key = str(uuid.uuid4())
    code = await generate_capthca_code(unique_key=unique_key, length=4)
    return StreamingResponse(
        content=image.generate(chars=code),
        media_type="image/jpeg",
        headers={"x-unique-key": unique_key},
    )


@router.post(
    "/captcha/code",
    summary="发送验证码",
    description="发送验证码, phone + scene组成unique_key",
)
async def captcha_code(
    phone: str = Body(description="手机号", max_length=11, min_length=11),
    scene: Literal["a", "b"] = Body(description="场景"),
) -> Resp[CaptchaCodeResponse]:
    unique_key = f"{scene}:{phone}"
    await generate_capthca_code(unique_key=unique_key, length=4)
    return Resp[CaptchaCodeResponse](data={"unique_key": unique_key})
