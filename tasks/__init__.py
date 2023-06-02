import os
import re
import uuid
import inspect
from typing import Union, Optional

import yaml
import ujson
from loguru import logger

from conf.config import local_configs
from storages.enums import TaskTypeEnum
from third_apis.k8s import (
    NAMESPACE,
    JOB_TEMPLATE,
    CRONJOB_TEMPLATE,
    JobConfig,
    CronJobConfig,
    client,
    batch_v1_api,
)


class UsageError(Exception):
    ...


async def _load_or_create_task(task_proxy: "TaskProxy") -> tuple[bool, str]:
    # from common.command.shell import init_ctx_relational
    # await init_ctx_relational()
    from storages.relational.models import Task

    _t, _ = await Task.update_or_create(
        file_path=task_proxy.file_path,
        func_name=task_proxy.func_name,
        defaults={
            "type_": task_proxy.type_.value,
            "cron": task_proxy.cron,
            "description": task_proxy.description,
            "enabled": task_proxy.enabled,
        },
    )
    return True, str(_t.id)


class TaskProxy:
    file_path: str
    func_name: str
    func: callable
    description: str
    type_: TaskTypeEnum
    cron: Optional[str]
    enabled: bool
    param_id: Optional[str]

    def __init__(
        self,
        func: callable,
        description: str,
        type_: TaskTypeEnum,
        cron: Optional[str],
        enabled: bool = True,
    ) -> None:
        file_path = os.path.abspath(inspect.getfile(func))
        self.file_path = os.path.relpath(
            file_path,
            local_configs.PROJECT.BASE_DIR,
        )
        self.func_name = func.__name__
        self.func = func
        self.description = description
        self.type_ = type_
        self.cron = cron
        self.enabled = enabled

    async def __call__(self, *args, **kwargs):
        return await self.func(*args, **kwargs)

    async def delay(self, *args, **kwargs):
        from storages.redis import AsyncRedisUtil, keys

        # save params
        param_id = uuid.uuid4()
        _, task_id = await _load_or_create_task(self)
        key = keys.RedisCacheKey.TaskPramsKey.format(
            task_id=task_id,
            param_id=param_id,
        )
        await AsyncRedisUtil.hset(
            key,
            "args",
            ujson.dumps(args),
            exp_of_none=60 * 60 * 24,
        )
        await AsyncRedisUtil.hset(
            key,
            "kwargs",
            ujson.dumps(kwargs),
            exp_of_none=60 * 60 * 24,
        )
        # create k8s task
        config = self.generate_job_config(task_id=task_id, param_id=param_id)
        body = self.generate_yaml_body(config)
        try:
            batch_v1_api.create_namespaced_job(namespace=NAMESPACE, body=body)
        except Exception as e:
            logger.error(f"Create job failed: {repr(e)}")
        return config.name

    async def schedule(self) -> tuple[bool, str]:
        if self.type_ is not TaskTypeEnum.scheduled:
            return False, "Task is not a scheduled task!"
        config = self.generate_cronjob_config()
        body = self.generate_yaml_body(config)
        try:
            batch_v1_api.create_namespaced_cron_job(
                namespace=NAMESPACE,
                body=body,
            )
        except Exception as e:
            logger.error(f"Create cronjob failed: {repr(e)}")

        return config.name

    def generate_yaml_body(self, config: Union[JobConfig, CronJobConfig]):
        yaml_path = (
            JOB_TEMPLATE
            if self.type_ is TaskTypeEnum.asynchronous
            else CRONJOB_TEMPLATE
        )
        with open(yaml_path) as f:
            content = f.read()
        placeholders = re.findall(r"\{\{.*?\}\}", content)
        for placeholder in placeholders:
            var_name = placeholder[2:-2].strip()
            if var_name in config.dict():
                if not config.dict()[var_name]:
                    raise UsageError(
                        f"Kubsernets Yaml Config-{var_name} is required!",
                    )
                content = content.replace(placeholder, config.dict()[var_name])
        return yaml.safe_load(content)

    def generate_job_config(
        self,
        task_id: str,
        param_id: Optional[str] = None,
    ) -> JobConfig:
        prefix = self.file_path.replace(os.sep, ".")[:-3]
        name = f"{prefix}.{self.func_name.replace('_', '-')}"
        command = f'python tasks/asynchronous/entry.py --task_id "{task_id}" --param_id "{param_id}"'
        return JobConfig(name=name, command=command)

    def generate_cronjob_config(self) -> CronJobConfig:
        prefix = self.file_path.replace(os.sep, ".")[:-3]
        name = f"{prefix}.{self.func_name.replace('_', '-')}"
        command = f"python {self.file_path}"
        return CronJobConfig(name=name, command=command, cron=self.cron)


class TaskManager:
    def task(  # noqa
        self,
        description: Optional[str] = "",
        type_: TaskTypeEnum = TaskTypeEnum.asynchronous,
        cron: str = "",
        enabled: bool = True,
    ):
        def _1(func):
            if not inspect.iscoroutinefunction(func):
                raise UsageError(
                    f"Task-{func.__name__} is not Awaitable Callable!",
                )

            if type_ is TaskTypeEnum.scheduled and not cron:
                raise UsageError(
                    f"Cron Task-{func.__name__} must specify cron rule!",
                )

            nonlocal description
            if not description:
                description = func.__doc__.strip() if func.__doc__ else ""

            # def _2(*args, **kwargs):
            #     return func(*args, **kwargs)

            return TaskProxy(func, description, type_, cron, enabled)

        return _1

    @classmethod
    def delete_job(cls, job_name: str):
        batch_v1_api.delete_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground",
                grace_period_seconds=5,
            ),
        )

    @classmethod
    def delete_cronjob(cls, job_name: str):
        batch_v1_api.delete_namespaced_cron_job(
            name=job_name,
            namespace=NAMESPACE,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground",
                grace_period_seconds=5,
            ),
        )


task_manager = TaskManager()
