"""
HTTP API
"""
from fastapi import APIRouter

from apis.http.routes.v1.auth import views as auth
from apis.http.routes.v1.common import views as common
from apis.http.routes.v1.account import views as account

v1_routes = APIRouter(prefix="/v1")

v1_routes.include_router(auth.router, prefix="/auth", tags=["授权相关"])
v1_routes.include_router(
    account.router, prefix="/account"
)  # , dependencies=[Depends(jwt_required)]
v1_routes.include_router(common.router, prefix="/other", tags=["其他"])
