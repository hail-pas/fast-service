from typing import Optional

from fastapi import Depends, APIRouter
from tortoise.exceptions import IntegrityError
from tortoise.contrib.pydantic import pydantic_model_creator

from common.utils import datetime_now
from common.encrypt import PasswordUtil
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp, SimpleSuccess
from apis.dependencies import token_required
from common.constant.messages import (
    ObjectNotExistMsgTemplate,
    UsernameOrPasswordErrorMsg,
    ObjectAlreadyExistMsgTemplate,
)
from storages.relational.curd.account import get_auth_data
from storages.relational.models.account import Role, Account
from storages.relational.pydantic.account import (
    AuthData,
    AccountList,
    AccountCreate,
    AccountDetail,
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

"""
3. view_func
"""


@router.post(
    "/login",
    summary="登录",
    description="登录接口",
    response_model=Resp[AuthData],
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
    return Resp[AuthData](data=await get_auth_data(account))


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
    account: Account = Depends(token_required),
):
    return Resp[AuthData](data=await get_auth_data(account))


@router.post(
    "/logout",
    summary="登出",
    description="退出登录接口",
    response_model=SimpleSuccess,
    dependencies=[Depends(token_required)],
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
    register_in: AccountCreate,
    callback_host: str,
    # callback_url: Union[HttpUrl, None]
) -> SimpleSuccess:
    return SimpleSuccess()
