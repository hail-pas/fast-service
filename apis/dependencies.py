import time
from typing import Optional, Annotated
from urllib.parse import unquote

from jose import jwt
from loguru import logger
from fastapi import Query, Header, Depends, Security
from pydantic import PositiveInt
from tortoise.models import Model
from fastapi.security import (
    HTTPBearer,
    APIKeyHeader,
    HTTPAuthorizationCredentials,
)
from starlette.requests import Request
from fastapi.security.utils import get_authorization_scheme_param

from conf.config import local_configs
from common.types import JwtPayload
from common.utils import get_client_ip
from common.encrypt import Jwt, SignAuth
from common.schemas import Pager, CURDPager
from common.responses import ResponseCodeEnum
from common.exceptions import ApiException
from common.constant.messages import (
    JsonRequiredMsg,
    TokenExpiredMsg,
    ApikeyInvalidMsg,
    ApikeyMissingMsg,
    SignCheckErrorMsg,
    BrokenAccessControl,
    TimestampExpiredMsg,
    IPNotAllowewedMsgTemplate,
    ObjectNotExistMsgTemplate,
    AuthorizationHeaderInvalidMsg,
    AuthorizationHeaderMissingMsg,
    AuthorizationHeaderTypeErrorMsg,
)
from storages.relational.models import Account
from storages.relational.curd.account import get_permissions


class TheBearer(HTTPBearer):
    async def __call__(
        self, request: Request
    ) -> Optional[
        HTTPAuthorizationCredentials
    ]:  # _authorization: Annotated[Optional[str], Depends(oauth2_scheme)]
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise ApiException(
                ResponseCodeEnum.unauthorized.value,
                AuthorizationHeaderMissingMsg,
            )
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise ApiException(
                    ResponseCodeEnum.unauthorized.value,
                    AuthorizationHeaderInvalidMsg,
                )
            else:
                return None
        if scheme != "Bearer":
            if self.auto_error:
                raise ApiException(
                    ResponseCodeEnum.unauthorized.value,
                    AuthorizationHeaderTypeErrorMsg,
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
                    ObjectNotExistMsgTemplate % f"排序字段 {field} ",
                )
        return CURDPager(
            limit=size,
            offset=(page - 1) * size,
            order_by=order_by,
            search=search,
        )

    return get_pager


async def token_required(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(auth_schema)],
    x_role_id: str = Header(..., description="角色id"),
) -> Account:
    jwt_secret: str = local_configs.JWT.SECRET
    try:
        payload = Jwt(jwt_secret).decode(token.credentials)
        payload: JwtPayload = JwtPayload(**payload)
        account_id = payload.account_id
        if account_id is None:
            raise ApiException(
                code=ResponseCodeEnum.unauthorized.value,
                message=AuthorizationHeaderInvalidMsg,
            )
    except jwt.ExpiredSignatureError:
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value, message=TokenExpiredMsg
        )
    # except jwt.JWTError:
    # raise ApiException(ResponseCodeEnum.unauthorized.value, AuthorizationHeaderInvalidMsg)
    # # 初始化全局用户信息，后续处理函数中直接使用
    except Exception:
        logger.error("解析token失败: e")
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=AuthorizationHeaderInvalidMsg,
        )

    account: Optional[Account] = (
        await Account.filter(id=account_id).prefetch_related("roles").first()
    )
    if not account:
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=AuthorizationHeaderInvalidMsg,
        )
    role = await account.roles.filter(id=x_role_id).first()
    if not role:
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=BrokenAccessControl,
        )
    request.scope["role"] = role
    request.scope["user"] = account
    return account


async def api_key_required(
    request: Request,
    api_key: str = Security(
        APIKeyHeader(
            name="x-api-key", scheme_name="API key header", auto_error=False
        )
    ),
):
    if not api_key:
        raise ApiException(
            message=ApikeyMissingMsg, code=ResponseCodeEnum.unauthorized.value
        )
    if api_key == local_configs.PROJECT.API_KEY:
        return api_key

    raise ApiException(
        message=ApikeyInvalidMsg, code=ResponseCodeEnum.unauthorized.value
    )


# depends on token_required
async def api_permission_check(
    request: Request,
    account: Account = Depends(token_required),
) -> Account:
    # router = request.scope["router"]
    # endpoint = request.scope["endpoint"]
    permissions = await get_permissions(account, request.scope["role"])

    method = request.method
    path = request.scope["path"]
    request.scope["path_params"]

    if f"{method}:{path}" in permissions:
        return account

    raise ApiException(
        code=ResponseCodeEnum.forbidden.value,
        message=ResponseCodeEnum.forbidden.label,
    )


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
            raise ApiException(JsonRequiredMsg)
    sign_str = sign_str + f".{x_timestamp}"
    if int(time.time()) - x_timestamp > 60:
        raise ApiException(TimestampExpiredMsg)
    if not x_signature or not SignAuth(local_configs.SIGN_SECRET).verify(
        x_signature, sign_str
    ):
        raise ApiException(SignCheckErrorMsg)


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
        raise ApiException(IPNotAllowewedMsgTemplate % caller_host)
