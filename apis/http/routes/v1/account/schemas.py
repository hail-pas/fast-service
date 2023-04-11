from dataclasses import dataclass

from fastapi import Query

from storages import enums


@dataclass
class AccountFilterSchema:
    phone: str = Query(None, description="手机号")
    roles__id: str = Query(None, description="角色id")
    status: enums.StatusEnum = Query(
        None, description=f"状态, {enums.StatusEnum.dict}"
    )

    def __post_init__(self, *args, **kwargs):
        # validate or add custom field
        self.extra_args = []
        self.extra_kwargs = {}

    # def __post_init_post_parse__(self):
    #     pass


@dataclass
class ResourceFilterSchema:
    code: str = Query(None, description="资源名称")
    label: str = Query(None, description="系统id")
    parent: str = Query(None, description="父级资源id")
    rely_on: str = Query(None, description="依赖资源id")

    def __post_init__(self, *args, **kwargs):
        # validate or add custom field
        self.extra_args = []
        self.extra_kwargs = {}

    # def __post_init_post_parse__(self):
    #     pass
