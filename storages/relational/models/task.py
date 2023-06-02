from __future__ import annotations

import os
import importlib

from tortoise import fields

from tasks import TaskProxy
from storages import enums
from storages.relational.models.base import UUIDPrimaryKeyModel


class Task(UUIDPrimaryKeyModel):
    file_path = fields.CharField(max_length=128, description="模块")
    func_name = fields.CharField(max_length=100, description="函数")
    type_ = fields.CharEnumField(
        max_length=20,
        enum_type=enums.TaskTypeEnum,
        description="任务类型",
    )
    cron = fields.CharField(max_length=100, description="定时任务表达式")
    description = fields.CharField(max_length=100, description="任务描述")
    enabled = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table_description = "任务"
        unique_together = (("file_path", "func_name"),)

    @property
    def task_proxy(self) -> TaskProxy:
        module_name = self.file_path.replace(os.sep, ".")[:-3]
        func_name = self.func_name
        module = importlib.import_module(module_name)
        func = getattr(module, func_name, None)
        if not func:
            raise ValueError(
                f"module: {module_name} has no function: {func_name}",
            )
        return TaskProxy(
            func=func,
            task_id=self.id,
            file_path=self.file_path,
            func_name=self.func_name,
            type_=self.type_,
            cron=self.cron,
            description=self.description,
            enabled=self.enabled,
        )

    def __str__(self) -> str:
        return f"""
            "type": {self.type_},
            "file_path": {self.module},
            "func_name": {self.function},
            "cron": {self.cron},
            "description": {self.description},
            "enabled": {self.enabled},
            """
