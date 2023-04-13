import uuid
from typing import List, Optional

from fastapi import Query, Depends, APIRouter

from apis.http.curd import CURDGenerator
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp
from apis.dependencies import account_permission_check
from storages.relational.curd.resource import get_resource_tree
from storages.relational.pydantic.role import (
    RoleList,
    RoleCreate,
    RoleDetail,
    RoleUpdate,
)
from storages.relational.models.account import (
    Role,
    System,
    Account,
    Resource,
    Permission,
)
from apis.http.routes.v1.account.schemas import (
    AccountFilterSchema,
    ResourceFilterSchema,
)
from storages.relational.pydantic.system import (
    SystemList,
    SystemCreate,
    SystemDetail,
    SystemUpdate,
)
from storages.relational.pydantic.account import (
    AccountList,
    AccountCreate,
    AccountDetail,
    AccountUpdate,
)
from storages.relational.pydantic.resource import (
    ResourceList,
    ResourceCreate,
    ResourceDetail,
    ResourceUpdate,
    ResourceLevelTreeNode,
)
from storages.relational.pydantic.permission import (
    PermissionList,
    PermissionCreate,
    PermissionDetail,
    PermissionUpdate,
)

router = APIRouter(
    dependencies=[Depends(account_permission_check)],
    route_class=RespSchemaAPIRouter,
)

router.include_router(
    CURDGenerator(
        schema=AccountList,
        db_model=Account,
        prefix="account/",
        create_schema=AccountCreate,
        update_schema=AccountUpdate,
        filter_schema=AccountFilterSchema,
        retrieve_schema=AccountDetail,
        search_fields=["username", "nickname"],
        tags=["账户信息管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=RoleList,
        db_model=Role,
        prefix="role/",
        create_schema=RoleCreate,
        update_schema=RoleUpdate,
        retrieve_schema=RoleDetail,
        search_fields=["label"],
        tags=["角色管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=SystemList,
        db_model=System,
        prefix="system/",
        create_schema=SystemCreate,
        update_schema=SystemUpdate,
        retrieve_schema=SystemDetail,
        search_fields=["label"],
        tags=["系统管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=PermissionList,
        db_model=Permission,
        prefix="permission/",
        create_schema=PermissionCreate,
        update_schema=PermissionUpdate,
        retrieve_schema=PermissionDetail,
        search_fields=["label"],
        tags=["权限管理"],
    )
)

router.include_router(
    CURDGenerator(
        schema=ResourceList,
        db_model=Resource,
        prefix="resource/",
        retrieve_schema=ResourceDetail,
        create_schema=ResourceCreate,
        update_schema=ResourceUpdate,
        filter_schema=ResourceFilterSchema,
        search_fields=[
            "code",
            "label",
        ],
        tags=["资源管理"],
    )
)


@router.get("resource/tree", tags=["资源管理"], summary="获取资源树")
async def resource_tree(
    role_id: Optional[uuid.UUID] = Query(None, description="角色id"),
    system_id: uuid.UUID = Query(..., description="系统id"),
) -> Resp[List[ResourceLevelTreeNode]]:
    """
    获取资源树
    """
    system = await System.get(id=system_id)
    if not system:
        return Resp.fail(message="系统不存在")
    role = None
    if role_id:
        role = await Role.get_or_none(id=role_id)
        if not role:
            return Resp.fail(message="角色不存在")
    return Resp[List[ResourceLevelTreeNode]](
        data=await get_resource_tree(
            system=system,
            role=role,
        )
    )
