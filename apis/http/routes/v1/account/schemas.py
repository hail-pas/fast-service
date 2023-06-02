from typing import Optional

from fastapi import Query
from pydantic import dataclasses

from storages import enums


@dataclasses.dataclass
class AccountFilterSchema:
    phone: Optional[str] = Query(None, description="手机号")
    roles__id__in: Optional[list[str]] = Query(None, description="角色id")
    status: Optional[enums.StatusEnum] = Query(
        None,
        description=f"状态, {enums.StatusEnum.dict}",
    )

    def __post_init__(self, *args, **kwargs) -> None:
        # validate or add custom field
        self.extra_args = []
        self.extra_kwargs = {}

    # @validator("roles__id__in")
    # def validate_roles_id(cls, v):
    #     if v:
    #         return v.split(",")

    def __post_init_post_parse__(self) -> None:
        pass


@dataclasses.dataclass
class ResourceFilterSchema:
    code: str = Query(None, description="资源名称")
    label: str = Query(None, description="系统id")
    parent: str = Query(None, description="父级资源id")
    rely_on: str = Query(None, description="依赖资源id")

    def __post_init__(self, *args, **kwargs) -> None:
        # validate or add custom field
        self.extra_args = []
        self.extra_kwargs = {}

    # def __post_init_post_parse__(self):
    #     pass
