from typing import List, Union, Optional

import aioredis

from conf.config import local_configs


class AsyncRedisUtil:
    """
    异步redis操作
    """

    _db: int = local_configs.REDIS.DB
    _pool: aioredis.ConnectionPool = None
    _redis: aioredis.Redis = None

    @classmethod
    def init(
        cls,
        host: str = local_configs.REDIS.HOST,
        port: int = local_configs.REDIS.PORT,
        password: Optional[str] = local_configs.REDIS.PASSWORD,
        db: int = local_configs.REDIS.DB,
        **kwargs,
    ):
        if cls._redis:
            return cls._redis
        aioredis.from_url("redis://localhost")

        # conn = aioredis.Connection(
        #     host=local_configs.REDIS.HOST,
        #     port=local_configs.REDIS.PORT,
        #     db=local_configs.REDIS.DB,
        #     password=local_configs.REDIS.PASSWORD,
        #     decode_responses=True,
        #     encoding_errors="strict",
        # )
        cls._pool = aioredis.ConnectionPool(
            host=local_configs.REDIS.HOST,
            port=local_configs.REDIS.PORT,
            db=local_configs.REDIS.DB,
            password=local_configs.REDIS.PASSWORD,
            decode_responses=True,
            encoding_errors="strict",
        )
        cls._redis = aioredis.Redis(connection_pool=cls._pool)
        return cls._redis

    @classmethod
    def get_pool(cls, db: int = local_configs.REDIS.DB, **kwargs):
        if db == cls._db:
            return cls._pool
        return aioredis.ConnectionPool(
            aioredis.Connection(
                host=local_configs.REDIS.HOST,
                port=local_configs.REDIS.PORT,
                db=db,
                password=local_configs.REDIS.PASSWORD,
                decode_responses=True,
                encoding_errors="strict",
            )
        )

    @classmethod
    def get_redis(cls):
        return cls._redis

    @classmethod
    async def _exp_of_none(cls, *args, exp_of_none, callback):
        """
        设置缓存过期
        """
        if not exp_of_none:
            return await getattr(cls._redis, callback)(*args)
        key = args[0]
        async with cls._redis.pipeline(transaction=True) as pipe:
            fun = getattr(pipe, callback)
            exists = await cls._redis.exists(key)
            if not exists:
                fun(*args)
                pipe.expire(key, exp_of_none)
                ret, _ = await pipe.execute()
            else:
                fun(*args)
                ret = (await pipe.execute())[0]
        return ret

    @classmethod
    async def set(cls, key, value, exp=None):
        await cls._redis.set(key, value, expire=exp)

    @classmethod
    async def get(cls, key, default=None):
        value = await cls._redis.get(key)
        if value is None:
            return default
        return value

    @classmethod
    async def hget(cls, name: str, key: str, default=None):
        """
        缓存清除, 接收list or str
        """
        v = await cls._redis.hget(name, key)
        if v is None:
            return default
        return v

    @classmethod
    async def get_or_set(cls, key, default=None, value_fun=None):
        """
        获取或者设置缓存
        """
        value = await cls._redis.get(key)
        if value is None and default:
            return default
        if value is not None:
            return value
        if value_fun:
            value, exp = await value_fun()
            await cls._redis.set(key, value, expire=exp)
        return value

    @classmethod
    async def delete(cls, key: Union[List[str], str]):
        return await cls._redis.delete(key)

    @classmethod
    async def sadd(cls, name, values, exp_of_none=None):
        return await cls._exp_of_none(
            name, values, exp_of_none=exp_of_none, callback="sadd"
        )

    @classmethod
    async def hset(cls, name, key, value, exp_of_none=None):
        return await cls._exp_of_none(
            name, key, value, exp_of_none=exp_of_none, callback="hset"
        )

    @classmethod
    async def hincrby(cls, name, key, value=1, exp_of_none=None):
        return await cls._exp_of_none(
            name, key, value, exp_of_none=exp_of_none, callback="hincrby"
        )

    @classmethod
    async def hincrbyfloat(cls, name, key, value, exp_of_none=None):
        return await cls._exp_of_none(
            name, key, value, exp_of_none=exp_of_none, callback="hincrbyfloat"
        )

    @classmethod
    async def incrby(cls, name, value=1, exp_of_none=None):
        return await cls._exp_of_none(
            name, value, exp_of_none=exp_of_none, callback="incrby"
        )

    @classmethod
    async def close(cls):
        await cls._pool.disconnect()


async def get_async_redis():
    return AsyncRedisUtil.get_pool()
