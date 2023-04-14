import json
from datetime import timedelta

from conf.config import local_configs
from common.types import JwtPayload
from common.utils import datetime_now, flatten_list
from common.encrypt import Jwt
from storages.relational.models import Role, System, Account
from storages.relational.pydantic.system import SystemListWithRoles
from storages.relational.pydantic.account import (
    AuthData,
    AccountDetailWithResource,
)


async def get_auth_data(account: Account) -> AuthData:
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

    # data["account"].resources = await get_resource_tree(
    #     system=await System.get(code="default"), role=account.roles[0]
    # )
    data["account"].systems = await SystemListWithRoles.from_queryset(
        System.filter(roles__in=await account.roles.all())
    )
    return AuthData(**data)


async def get_permissions(account: Account, role: Role) -> set:
    permission_set = set(
        flatten_list(
            await account.roles.filter(id=role.id)
            .prefetch_related("permissions", "resources")
            .values_list("permissions__code", "resources__permissions__code")
        )
    )

    # for role in await account.roles.all().prefetch_related("permissions", "resources"):
    #     permission_set |= set(await role.permissions.all().values_list("code", flat=True))
    #     for resource in await role.resources.all():
    #         permission_set |= set(await resource.permissions.all().values_list("code", flat=True))
    return permission_set
