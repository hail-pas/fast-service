from fastapi import Request, APIRouter

from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp
from common.constant.tags import OuterAppTagsEnum

router = APIRouter(prefix="/ping", route_class=RespSchemaAPIRouter)


@router.get("", tags=[OuterAppTagsEnum.ping], summary="ping")
async def ping(request: Request) -> Resp:
    return Resp(message="pong")
