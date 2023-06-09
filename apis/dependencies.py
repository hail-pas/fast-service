import time
from typing import Callable, Optional, Annotated
from urllib.parse import unquote

from jose import ExpiredSignatureError
from loguru import logger
from fastapi import Query, Header, Depends, Security
from pydantic import BaseModel, PositiveInt
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
from common.fastapi import AuthorizedRequest
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
        self: "TheBearer",
        request: Request,
    ) -> Optional[
        HTTPAuthorizationCredentials
    ]:  # _authorization: Annotated[Optional[str], Depends(oauth2_scheme)]
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise ApiException(
                code=ResponseCodeEnum.unauthorized.value,
                message=AuthorizationHeaderMissingMsg,
            )
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise ApiException(
                    code=ResponseCodeEnum.unauthorized.value,
                    message=AuthorizationHeaderInvalidMsg,
                )
            return None
        if scheme != "Bearer":
            if self.auto_error:
                raise ApiException(
                    code=ResponseCodeEnum.unauthorized.value,
                    message=AuthorizationHeaderTypeErrorMsg,
                )
            return None
        return HTTPAuthorizationCredentials(
            scheme=scheme,
            credentials=credentials,
        )


auth_schema = TheBearer()


def pure_get_pager(
    page: PositiveInt = Query(default=1, example=1, description="第几页"),
    size: PositiveInt = Query(default=10, example=10, description="每页数量"),
) -> Pager:
    return Pager(limit=size, offset=(page - 1) * size)


def paginate(
    model: Model,
    search_fields: Optional[set],
    list_schema: BaseModel,
    max_limit: Optional[int],
) -> Callable[
    [PositiveInt, PositiveInt, str, set[str], Optional[set[str]]],
    CURDPager,
]:
    def get_pager(
        page: PositiveInt = Query(default=1, example=1, description="第几页"),
        size: PositiveInt = Query(default=10, example=10, description="每页数量"),
        search: str = Query(
            None,
            description=f"搜索关键字, 匹配字段: {', '.join(search_fields)}",
        ),
        order_by: set[str] = Query(
            default=set(),
            example="-id",
            description=(
                "排序字段, 多个字段用英文逗号分隔. 升序保持原字段名, 降序增加前缀-."
                f"可选字段: {', '.join(model._meta.db_fields)}"
            ),
        ),
        selected_fields: Optional[set[str]] = Query(
            default=set(),
            description=f"返回字段, 多个字段用英文逗号分隔. 可选字段: {', '.join(list_schema.__fields__.keys())}",
        ),
    ) -> CURDPager:
        if max_limit:
            size = min(size, max_limit)
        for field in order_by:
            if field.startswith("-"):
                field = field[1:]  # noqa
            if field not in model._meta.db_fields:
                raise ApiException(
                    ObjectNotExistMsgTemplate % f"排序字段 {field} ",
                )
        if selected_fields:
            selected_fields.add("id")
        return CURDPager(
            limit=size,
            offset=(page - 1) * size,
            order_by=order_by or set(),
            search=search,
            selected_fields=selected_fields,
        )

    return get_pager


async def token_required(
    request: AuthorizedRequest,
    token: Annotated[HTTPAuthorizationCredentials, Depends(auth_schema)],
) -> Account:
    jwt_secret: str = local_configs.JWT.SECRET
    try:
        payload = Jwt(jwt_secret).decode(token.credentials)
        payload: JwtPayload = JwtPayload(**payload)
        account_id = payload.id
        if account_id is None:
            raise ApiException(
                code=ResponseCodeEnum.unauthorized.value,
                message=AuthorizationHeaderInvalidMsg,
            )
    except ExpiredSignatureError as e:
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=TokenExpiredMsg,
        ) from e
    # except jwt.JWTError:
    # raise ApiException(ResponseCodeEnum.unauthorized.value, AuthorizationHeaderInvalidMsg)
    # # 初始化全局用户信息，后续处理函数中直接使用
    except Exception as e:
        logger.error("解析token失败: e")
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=AuthorizationHeaderInvalidMsg,
        ) from e

    account: Optional[Account] = (
        await Account.filter(id=account_id).prefetch_related("roles").first()
    )
    if not account:
        raise ApiException(
            code=ResponseCodeEnum.unauthorized.value,
            message=AuthorizationHeaderInvalidMsg,
        )
    request.scope["user"] = account
    return account


async def api_key_required(
    request: Request,
    api_key: str = Security(
        APIKeyHeader(
            name="X-Api-Key",
            scheme_name="API key header",
            auto_error=False,
        ),
    ),
) -> None:
    if not api_key:
        raise ApiException(
            message=ApikeyMissingMsg,
            code=ResponseCodeEnum.unauthorized.value,
        )
    if api_key == local_configs.PROJECT.API_KEY:
        return api_key

    raise ApiException(
        message=ApikeyInvalidMsg,
        code=ResponseCodeEnum.unauthorized.value,
    )


# depends on token_required
async def api_permission_check(
    request: AuthorizedRequest,
    account: Account = Depends(token_required),
    x_role_id: str = Header(title="角色id", description="使用的角色id"),
) -> Account:
    # router = request.scope["router"]
    # endpoint = request.scope["endpoint"]
    role = await account.roles.filter(id=x_role_id).first()
    if not role:
        raise ApiException(
            code=ResponseCodeEnum.forbidden.value,
            message=BrokenAccessControl,
        )
    request.scope["role"] = role

    permissions = await get_permissions(account, role)

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
        ...,
        example=int(time.time()),
        description="秒级时间戳",
    ),
    x_signature: str = Header(..., example="sign", description="签名"),
) -> None:
    if request.method in ["GET", "DELETE"]:
        sign_str = request.scope["query_string"].decode()
        sign_str = unquote(sign_str)
    else:
        try:
            sign_str = await request.body()
            sign_str = sign_str.decode()
        except Exception as e:
            raise ApiException(JsonRequiredMsg) from e
    sign_str = sign_str + f".{x_timestamp}"
    if int(time.time()) - x_timestamp > 60:
        raise ApiException(TimestampExpiredMsg)
    if not x_signature or not SignAuth(local_configs.SIGN_SECRET).verify(
        x_signature,
        sign_str,
    ):
        raise ApiException(SignCheckErrorMsg)


class CheckAllowedHost:
    allowed_hosts: set

    def __init__(self, allowed_hosts: Optional[set] = None) -> None:
        if not allowed_hosts:
            allowed_hosts = {"*"}
        self.allowed_hosts = allowed_hosts

    def __call__(self, request: Request) -> None:
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
