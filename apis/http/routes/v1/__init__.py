"""
HTTP API
"""
from fastapi import APIRouter

from common.fastapi import RespSchemaAPIRouter
from common.constant.tags import TagsEnum
from apis.http.routes.v1.auth import views as auth
from apis.http.routes.v1.common import views as common
from apis.http.routes.v1.account import views as account

v1_routes = APIRouter(prefix="/v1", route_class=RespSchemaAPIRouter)

v1_routes.include_router(
    auth.router, prefix="/auth", tags=[TagsEnum.authorization]
)
v1_routes.include_router(account.router, prefix="/account")
v1_routes.include_router(common.router, prefix="/other", tags=[TagsEnum.other])
