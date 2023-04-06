from fastapi import Depends, APIRouter

from apis.http.curd import CURDGenerator
from common.encrypt import PasswordUtil
from common.responses import Resp
from apis.dependencies import account_permission_check
from storages.relational.models.account import (
    Role,
    System,
    Account,
    Resource,
    Permission,
)
from apis.http.routes.v1.account.pydntic_model import (
    RoleList,
    RoleCreate,
    AccountList,
    SystemCreate,
    SystemDetail,
    AccountCreate,
    AccountDetail,
    AccountUpdate,
    PermissionCreate,
    PermissionDetail,
    SystemResourceCreate,
    SystemResourceDetail,
    SystemResourceUpdate,
    SystemResourceFilterSchema,
)

router = APIRouter(dependencies=[Depends(account_permission_check)])

router.include_router(
    CURDGenerator(
        schema=AccountList,
        db_model=Account,
        prefix="account/",
        create_schema=AccountCreate,
        update_schema=AccountUpdate,
        retrieve_schema=AccountDetail,
        tags=["账户信息管理"],
        create_route=False,
    )
)


@router.post("/account", tags=["账户信息管理"], summary="创建账户")
async def create_account(account_in: AccountCreate) -> Resp[AccountDetail]:
    data = account_in.dict()
    role_ids = data.pop("roles")
    roles = []
    for role_id in role_ids:
        role = await Role.get_or_none(id=role_id)
        if not role:
            return Resp.fail(message="角色不存在")
        roles.append(role)
    data["password"] = PasswordUtil.get_password_hash(data["password"])
    db_model = Account(**data)
    # db_model = await Account.create(**data)
    await db_model.save()
    await db_model.roles.add(*roles)
    data = await AccountDetail.from_tortoise_orm(db_model)
    return Resp[AccountDetail](data=data)


router.include_router(
    CURDGenerator(
        schema=RoleList,
        db_model=Role,
        prefix="role/",
        create_schema=RoleCreate,
        update_schema=RoleCreate,
        tags=["角色管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=SystemDetail,
        db_model=System,
        prefix="system/",
        create_schema=SystemCreate,
        update_schema=SystemCreate,
        tags=["系统管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=PermissionDetail,
        db_model=Permission,
        prefix="permission/",
        create_schema=PermissionCreate,
        update_schema=PermissionCreate,
        tags=["权限管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=SystemResourceDetail,
        db_model=Resource,
        prefix="resource/",
        create_schema=SystemResourceCreate,
        update_schema=SystemResourceUpdate,
        filter_schema=SystemResourceFilterSchema,
        search_fields=[
            "code",
            "label",
        ],
        tags=["资源管理"],
    )
)
