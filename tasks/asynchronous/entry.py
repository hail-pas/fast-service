import os
import asyncio
import argparse
import importlib

import ujson

from conf.config import local_configs
from common.fastapi import setup_sentry
from storages.redis import AsyncRedisUtil
from storages.redis.keys import RedisCacheKey
from common.command.shell import init_ctx
from storages.relational.models import Task


async def run_task(task_id: str, param_id: str) -> any:
    # init context
    await init_ctx()
    setup_sentry(local_configs)  # sentry

    # retrieve params and clear params
    key = RedisCacheKey.TaskPramsKey.format(task_id=task_id, param_id=param_id)
    args = ujson.loads(await AsyncRedisUtil.hget(key, "args", "[]"))
    kwargs = ujson.loads(await AsyncRedisUtil.hget(key, "kwargs", "{}"))
    await AsyncRedisUtil._redis.delete(key)

    # retrieve task
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise ValueError(f"Task-{task_id}: Does not exist")

    # retrieve func
    module_name = task.file_path.replace(os.sep, ".")[:-3]
    func_name = task.func_name
    module = importlib.import_module(module_name)
    func = getattr(module, func_name, None)
    if not func:
        raise ValueError(
            f"Task-{task_id}: Module-{module_name} Func-{func_name} Does not exist",
        )

    # run task
    return await func(*args, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-tid",
        "--task_id",
        type=str,
        help="任务id",
    )
    parser.add_argument(
        "-pid",
        "--param_id",
        type=str,
        help="redis参数id",
    )

    args = parser.parse_args()
    task_id = args.task_id
    param_id = args.param_id

    loop = asyncio.get_event_loop()
    task_ret = loop.create_task(run_task(task_id, param_id))
    loop.run_until_complete(task_ret)
    loop.close()
    task_ret.result()
