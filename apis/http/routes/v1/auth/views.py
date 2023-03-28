import json
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Body, Depends, APIRouter
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from conf.config import local_configs
from common.types import JwtPayload
from common.utils import datetime_now
from common.encrypt import Jwt, PasswordUtil
from common.responses import Resp, SimpleSuccess
from apis.dependencies import jwt_required
from storages.relational.models.account import Role, Account
from apis.http.routes.v1.account.pydntic_model import (
    AccountCreate,
    AccountDetail,
)

router = APIRouter()

"""
1. request_schema
"""


class LoginSchema(BaseModel):
    username: str = Body(..., description="用户名", example="phoenix")
    password: str = Body(..., description="密码")


"""
2. response_schema
"""


class AuthData(BaseModel):
    token_type: str
    access_token: str
    expired_at: datetime
    account: AccountDetail

    class Config:
        orm_mode = True


"""
3. view_func
"""


@router.post(
    "/login", summary="登录", description="登录接口", response_model=Resp[AuthData]
)
async def login(login_data: LoginSchema):
    account: Optional[Account] = await Account.filter(
        username=login_data.username
    ).first()
    if not account:
        return Resp.fail(message="用户不存在")
    if not PasswordUtil.verify_password(login_data.password, account.password):
        return Resp.fail(message="用户名或密码错误")
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
        "account": await AccountDetail.from_tortoise_orm(account),
    }
    return Resp[AuthData](data=AuthData(**data))


# @router.post("/oauth/login", summary="第三方登录", description="第三方登录接口", response_model=Resp[AuthData])
# async def oauth_login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     if login_data.grant_type == "password":
#         return await login(LoginSchema(username=login_data.username, password=login_data.password))
#     return Resp.fail(message="暂不支持的登录方式")


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
            return Resp.fail("角色不存在")
        roles.append(role)
    try:
        data["password"] = PasswordUtil.get_password_hash(data["password"])
        account = await Account.create(**data)
        await account.roles.add(*roles)
    except IntegrityError:
        return Resp.fail("用户已存在")
    data = await AccountDetail.from_tortoise_orm(account)
    """
    1. cls._meta.fields_map.keys() 没有 roles 导致要获取reverserelation 字段需要显示指定;
       不确定是不是tortoise orm 的bug
    """
    return Resp[AccountDetail](data=data)
