from enum import Enum, unique

from conf.config import local_configs

ProjectCode = local_configs.PROJECT.UNIQUE_CODE

assert ProjectCode, "Must Define Unique Project Code as Redis Prefix"

RedisKeyPrefix = f"{ProjectCode}:"


@unique
class RedisSearchIndexPrefix(str, Enum):
    pass


@unique
class RedisCacheKey(str, Enum):
    RedisLockKey = RedisKeyPrefix + "RedisLock:{unique_key}"
    TaskPramsKey = RedisKeyPrefix + "TaskPrams:{task_id}:{param_id}"
    CaptchaCodeKey = RedisKeyPrefix + "CaptchaCode:{unique_key}"
