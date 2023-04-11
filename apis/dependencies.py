import time
from typing import Optional, Annotated
from urllib.parse import unquote

from jose import jwt
from loguru import logger
from fastapi import Query, Header, Depends
from pydantic import PositiveInt
from tortoise.models import Model
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request
from fastapi.security.utils import get_authorization_scheme_param

from conf.config import local_configs
from common.types import JwtPayload
from common.utils import flatten_list, get_client_ip
from common.encrypt import Jwt, SignAuth
from common.schemas import Pager, CURDPager
from common.responses import ResponseCodeEnum
from common.exceptions import ApiException
from storages.relational.models.account import Account


class TheBearer(HTTPBearer):
    async def __call__(
        self, request: Request
    ) -> Optional[
        HTTPAuthorizationCredentials
    ]:  # _authorization: Annotated[Optional[str], Depends(oauth2_scheme)]
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise ApiException(
                ResponseCodeEnum.unauthorized.value, "未携带授权头部信息"
            )
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise ApiException(
                    ResponseCodeEnum.unauthorized.value, "授权头部信息有误"
                )
            else:
                return None
        if scheme != "Bearer":
            if self.auto_error:
                raise ApiException(
                    ResponseCodeEnum.unauthorized.value, "授权信息类型错误, 请使用 Bearer"
                )
            else:
                return None
        return HTTPAuthorizationCredentials(
            scheme=scheme, credentials=credentials
        )


auth_schema = TheBearer()


def pure_get_pager(
    page: PositiveInt = Query(default=1, example=1, description="第几页"),
    size: PositiveInt = Query(default=10, example=10, description="每页数量"),
):
    return Pager(limit=size, offset=(page - 1) * size)


def paginate(
    model: Model, search_fields: Optional[set], max_limit: Optional[int]
):
    def get_pager(
        page: PositiveInt = Query(default=1, example=1, description="第几页"),
        size: PositiveInt = Query(default=10, example=10, description="每页数量"),
        order_by: str = Query(
            default="",
            example="-id",
            description=f"排序字段, 多个字段用逗号分隔. 可选字段: {', '.join(model._meta.db_fields)}",
        ),
        search: str = Query(
            None, description=f"搜索关键字, 匹配字段: {', '.join(search_fields)}"
        ),
    ):
        if max_limit:
            size = min(size, max_limit)
        order_by = list(filter(lambda x: x, order_by.split(",")))
        for field in order_by:
            if field.startswith("-"):
                field = field[1:]
            if field not in model._meta.db_fields:
                raise ApiException(
                    f"排序字段 {field} 不存在",
                )
        return CURDPager(
            limit=size,
            offset=(page - 1) * size,
            order_by=order_by,
            search=search,
        )

    return get_pager


async def jwt_required(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(auth_schema)],
) -> Account:
    jwt_secret: str = local_configs.JWT.SECRET
    try:
        payload = Jwt(jwt_secret).decode(token.credentials)
        payload: JwtPayload = JwtPayload(**payload)
        account_id = payload.account_id
        if account_id is None:
            raise ApiException(
                code=ResponseCodeEnum.unauthorized.value, message="授权头部信息有误"
            )
    except jwt.ExpiredSignatureError:
        raise ApiException(
            code="token过期", message=ResponseCodeEnum.unauthorized.value
        )
    # except jwt.JWTError:
    #     raise ApiException(ResponseCodeEnum.unauthorized.value, "授权头部信息有误")
    # # 初始化全局用户信息，后续处理函数中直接使用
    except Exception:
        logger.error("解析token失败: e")
        raise ApiException(
            code="授权头部信息有误", message=ResponseCodeEnum.unauthorized.value
        )

    account = await Account.get_or_none(id=account_id)
    if not account:
        raise ApiException(
            code="授权头部信息有误", message=ResponseCodeEnum.unauthorized.value
        )
    request.scope["user"] = account
    return account


async def get_permissions(account: Account) -> set:
    permission_set = set(
        flatten_list(
            await account.roles.all()
            .prefetch_related("permissions", "resources")
            .values_list("permissions__code", "resources__permissions__code")
        )
    )
    # for role in await account.roles.all().prefetch_related("permissions", "resources"):
    #     permission_set |= set(await role.permissions.all().values_list("code", flat=True))
    #     for resource in await role.resources.all():
    #         permission_set |= set(await resource.permissions.all().values_list("code", flat=True))
    return permission_set


# depends on jwt_required
async def account_permission_check(
    request: Request,
    # token: HTTPAuthorizationCredentials = Depends(auth_schema)
    token: Annotated[HTTPAuthorizationCredentials, Depends(auth_schema)],
) -> Account:
    # router = request.scope["router"]
    # endpoint = request.scope["endpoint"]
    account: Account = await jwt_required(request, token)
    permissions = await get_permissions(account)

    method = request.method
    path = request.scope["path"]
    request.scope["path_params"]

    if f"{method}:{path}" in permissions:
        return account

    raise ApiException(code=ResponseCodeEnum.forbidden.value, message="没有权限")


async def sign_check(
    request: Request,
    x_timestamp: int = Header(
        ..., example=int(time.time()), description="秒级时间戳"
    ),
    x_signature: str = Header(..., example="sign", description="签名"),
):
    if request.method in ["GET", "DELETE"]:
        sign_str = request.scope["query_string"].decode()
        sign_str = unquote(sign_str)
    else:
        try:
            sign_str = await request.body()
            sign_str = sign_str.decode()
        except Exception:
            raise ApiException("json body required")
    sign_str = sign_str + f".{x_timestamp}"
    if int(time.time()) - x_timestamp > 60:
        raise ApiException("timestamp expired")
    if not x_signature or not SignAuth(local_configs.SIGN_SECRET).verify(
        x_signature, sign_str
    ):
        raise ApiException("sign check failed")


class CheckAllowedHost:
    allowed_hosts: set

    def __init__(self, allowed_hosts: set = {"*"}) -> None:
        self.allowed_hosts = allowed_hosts

    def __call__(self, request: Request):
        if "*" in local_configs.SERVER.ALLOW_HOSTS:
            return
        caller_host = get_client_ip(request)
        if "." in caller_host:
            host_segments = caller_host.strip().split(".")
            if len(host_segments) == 4:
                blur_segments = ["*", "*", "*", "*"]
                for i in range(4):
                    blur_segments[i] = host_segments[i]
                    if (
                        ".".join(blur_segments)
                        in local_configs.SERVER.ALLOW_HOSTS
                    ):
                        return
        raise ApiException(f"IP {caller_host} 不在访问白名单")
