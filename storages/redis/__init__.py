# ruff: noqa
from typing import Any, Callable, Optional

from redis.typing import KeyT, FieldT, ExpiryT, EncodableT
from redis.asyncio import Redis, Connection, ConnectionPool

from conf.config import local_configs


class AsyncRedisUtil:
    """异步redis操作."""

    _db: int = local_configs.REDIS.DB
    _pool: ConnectionPool = None
    _redis: Redis = None

    @classmethod
    def init(
        cls,
        host: str = local_configs.REDIS.HOST,
        port: int = local_configs.REDIS.PORT,
        username: Optional[str] = local_configs.REDIS.USERNAME,
        password: Optional[str] = local_configs.REDIS.PASSWORD,
        db: int = local_configs.REDIS.DB,
        max_connections: int = local_configs.REDIS.MAX_CONNECTIONS,
        single_connection_client: bool = True,
        **kwargs,
    ) -> Redis:
        if cls._redis:
            return cls._redis

        # conn = aioredis.Connection(
        #     host=local_configs.REDIS.HOST,
        #     port=local_configs.REDIS.PORT,
        #     db=local_configs.REDIS.DB,
        #     password=local_configs.REDIS.PASSWORD,
        #     decode_responses=True,
        #     encoding_errors="strict",
        # )
        cls._pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            max_connections=max_connections,
            decode_responses=True,
            encoding_errors="strict",
        )
        cls._redis = Redis(
            connection_pool=cls._pool,
            single_connection_client=single_connection_client,
            **kwargs,
        )
        return cls._redis

    @classmethod
    def get_pool(
        cls,
        db: int = local_configs.REDIS.DB,
        **kwargs,
    ) -> ConnectionPool:
        if db == cls._db:
            return cls._pool
        return ConnectionPool(
            Connection(
                host=local_configs.REDIS.HOST,
                port=local_configs.REDIS.PORT,
                db=db,
                password=local_configs.REDIS.PASSWORD,
                decode_responses=True,
                encoding_errors="strict",
            ),
        )

    @classmethod
    def get_redis(cls) -> Redis:
        return cls._redis

    @classmethod
    async def _exp_of_none(
        cls,
        *args,
        exp_of_none: ExpiryT,
        callback: str,
    ) -> Any:
        """设置缓存过期."""
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
        return ret  # noqa

    @classmethod
    async def set(
        cls, key: KeyT, value: EncodableT, exp: ExpiryT = None
    ) -> Any:
        return await cls._redis.set(key, value, ex=exp)

    @classmethod
    async def get(cls, key: KeyT, default: EncodableT = None) -> Any:
        value = await cls._redis.get(key)
        if value is None:
            return default
        return value

    @classmethod
    async def hget(
        cls, name: str, key: str, default: EncodableT = None
    ) -> Any:
        """缓存清除, 接收list or str."""
        v = await cls._redis.hget(name, key)
        if v is None:
            return default
        return v

    @classmethod
    async def get_or_set(
        cls,
        key: KeyT,
        default: EncodableT | None = None,
        value_func: Callable[[], tuple[EncodableT, ExpiryT]] = None,
    ) -> Any:
        """获取或者设置缓存."""
        value = await cls._redis.get(key)
        if value is None and default:
            return default
        if value is not None:
            return value
        if value_func:
            value, exp = await value_func()
            await cls._redis.set(key, value, expire=exp)
        return value

    @classmethod
    async def delete(cls, key: KeyT) -> Any:
        return await cls._redis.delete(key)

    @classmethod
    async def sadd(
        cls,
        name: KeyT,
        values: list[EncodableT],
        exp_of_none: ExpiryT = None,
    ) -> Any:
        cls._redis.sadd()
        return await cls._exp_of_none(
            name,
            values,
            exp_of_none=exp_of_none,
            callback="sadd",
        )

    @classmethod
    async def hset(
        cls,
        name: KeyT,
        key: FieldT,
        value: EncodableT,
        exp_of_none: ExpiryT = None,
    ) -> Any:
        return await cls._exp_of_none(
            name,
            key,
            value,
            exp_of_none=exp_of_none,
            callback="hset",
        )

    @classmethod
    async def hincrby(
        cls,
        name: KeyT,
        key: FieldT,
        value: int = 1,
        exp_of_none: ExpiryT = None,
    ) -> Any:
        return await cls._exp_of_none(
            name,
            key,
            value,
            exp_of_none=exp_of_none,
            callback="hincrby",
        )

    @classmethod
    async def hincrbyfloat(
        cls,
        name: KeyT,
        key: FieldT,
        value: float,
        exp_of_none: ExpiryT = None,
    ) -> Any:
        return await cls._exp_of_none(
            name,
            key,
            value,
            exp_of_none=exp_of_none,
            callback="hincrbyfloat",
        )

    @classmethod
    async def incrby(
        cls,
        name: KeyT,
        value: int = 1,
        exp_of_none: ExpiryT = None,
    ) -> Any:
        return await cls._exp_of_none(
            name,
            value,
            exp_of_none=exp_of_none,
            callback="incrby",
        )

    @classmethod
    async def close(cls) -> None:
        await cls._redis.close()


async def get_async_redis() -> ConnectionPool:
    return AsyncRedisUtil.get_pool()
