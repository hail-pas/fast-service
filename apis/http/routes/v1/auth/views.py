import json
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Depends, APIRouter
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError
from tortoise.contrib.pydantic import pydantic_model_creator

from conf.config import local_configs
from common.types import JwtPayload
from common.utils import datetime_now
from common.encrypt import Jwt, PasswordUtil
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp, SimpleSuccess
from apis.dependencies import jwt_required
from common.constant.messages import (
    ObjectNotExistMsgTemplate,
    UsernameOrPasswordErrorMsg,
    ObjectAlreadyExistMsgTemplate,
)
from storages.relational.curd.resource import get_resource_tree
from storages.relational.models.account import Role, System, Account
from storages.relational.pydantic.system import SystemList
from storages.relational.pydantic.account import (
    AccountList,
    AccountCreate,
    AccountDetail,
    AccountDetailWithResource,
)

router = APIRouter(route_class=RespSchemaAPIRouter)

"""
1. request_schema
"""

LoginSchema = pydantic_model_creator(
    Account,
    name="LoginSchema",
    include=["username", "password"],
    exclude_readonly=True,
)

"""
2. response_schema
"""


class AuthData(BaseModel):
    token_type: str
    access_token: str
    expired_at: datetime
    account: AccountDetailWithResource

    class Config:
        orm_mode = True


"""
3. view_func
"""


@router.post(
    "/login", summary="登录", description="登录接口", response_model=Resp[AuthData]
)
async def login(login_data: LoginSchema):
    account: Optional[Account] = (
        await Account.filter(username=login_data.username)
        .prefetch_related("roles")
        .first()
    )
    if not account:
        return Resp.fail(message=ObjectNotExistMsgTemplate % "账户")
    if not PasswordUtil.verify_password(login_data.password, account.password):
        return Resp.fail(message=UsernameOrPasswordErrorMsg)
    account.last_login_at = datetime_now()
    await account.save(update_fields=["last_login_at"])
    expired_at = datetime_now() + timedelta(
        minutes=local_configs.JWT.EXPIRATION_DELTA_MINUTES
    )
    payload = JwtPayload(account_id=account.id, expired_at=expired_at)
    data = {
        "token_type": "Bearer",
        "access_token": Jwt(local_configs.JWT.SECRET).get_jwt(
            json.loads(payload.json())
        ),
        "expired_at": expired_at,
        "account": await AccountDetailWithResource.from_tortoise_orm(account),
    }

    data["account"].resources = await get_resource_tree(
        system=await System.get(code="burnish"), role=account.roles[0]
    )
    data["account"].systems = await SystemList.from_queryset(
        System.filter(roles__in=await account.roles.all())
    )
    return Resp[AuthData](data=AuthData(**data))


# @router.post("/oauth/login", summary="第三方登录", description="第三方登录接口", response_model=Resp[AuthData])
# async def oauth_login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     if login_data.grant_type == "password":
#         return await login(LoginSchema(username=login_data.username, password=login_data.password))
#     return Resp.fail(message=ActionNotSupportMsgTemplate % "登录方式")


@router.post(
    "/token/refresh",
    summary="刷新token",
    description="刷新token过期时间",
    response_model=Resp[AuthData],
)
async def refresh_token(
    account: Account = Depends(jwt_required),
):
    expired_at = datetime_now() + timedelta(
        minutes=local_configs.JWT.EXPIRATION_DELTA_MINUTES
    )
    data = {
        "token_type": "Bearer",
        "token_value": Jwt(local_configs.JWT.SECRET).get_jwt(
            {"account_id": account.id, "exp": expired_at}
        ),
        "expired_at": expired_at,
        "account": account,
    }
    return Resp[AuthData](data=AuthData(**data))


@router.post(
    "/logout",
    summary="登出",
    description="退出登录接口",
    response_model=SimpleSuccess,
    dependencies=[Depends(jwt_required)],
)
async def logout():
    return SimpleSuccess()


@router.post("/register", summary="用户注册", description="新用户注册接口")
async def register(register_in: AccountCreate) -> Resp[AccountDetail]:
    data = register_in.dict()
    role_ids = data.pop("roles")
    roles = []
    for role_id in role_ids:
        role = await Role.get_or_none(id=role_id)
        if not role:
            return Resp.fail(ObjectNotExistMsgTemplate % "角色")
        roles.append(role)
    try:
        account = await Account.create(**data)
        await account.roles.add(*roles)
    except IntegrityError:
        return Resp.fail(ObjectAlreadyExistMsgTemplate % "用户")
    data = await AccountDetail.from_tortoise_orm(account)
    return Resp[AccountDetail](data=data)


inner_account_register_callback_router = APIRouter()


@inner_account_register_callback_router.post(
    "{$callback_host}/callback/account/{$request.body.username}",
    summary="内部用户注册回调",
    description="内部用户注册回调接口",
)
def inner_register_callback(
    account: AccountList,
) -> SimpleSuccess:
    pass


@router.post(
    "/register/inner",
    summary="内部用户注册",
    description="内部用户注册注册接口",
    callbacks=inner_account_register_callback_router.routes,
)
async def inner_register(
    register_in: AccountCreate, callback_host: str
) -> SimpleSuccess:
    return SimpleSuccess()
