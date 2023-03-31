import os
import enum
import multiprocessing
from typing import Any, Dict, Literal, Optional
from pathlib import Path
from functools import lru_cache

import ujson
from pydantic import BaseModel, BaseSettings, validator

BASE_DIR = Path(__file__).resolve().parent.parent


class EnvironmentEnum(str, enum.Enum):
    development = "Development"
    test = "Test"
    production = "Production"


ENVIRONMENT = os.environ.get(
    "environment", EnvironmentEnum.development.value.capitalize()
)

CONFIG_FILE_PREFIX = str(BASE_DIR.absolute()) + f"/conf/content/{ENVIRONMENT.lower()}"

CONFIG_FILE_EXTENSION = "json"


class HostAndPort(BaseModel):
    HOST: str
    PORT: Optional[int]


class Relational(HostAndPort):
    USERNAME: str
    PASSWORD: str
    DB: str
    TYPE: Literal["postgresql", "mysql"] = "postgresql"
    TIMEZONE: Optional[str] = None

    @property
    def url(self):
        pkg = "asyncpg"
        if self.TYPE == "mysql":
            pkg = "aiomysql"
        return f"{self.TYPE}+{pkg}://{self.USERNAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"  # noqa

    @property
    def tortoise_orm_config(self):
        echo = (
            True if ENVIRONMENT == EnvironmentEnum.development.value else False
        )
        return {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": self.HOST,
                        "port": self.PORT,
                        "user": self.USERNAME,
                        "password": self.PASSWORD,
                        "database": self.DB,
                        "echo": echo,
                        "maxsize": 20,
                    },
                },
                "shell": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": self.HOST,
                        "port": self.PORT,
                        "user": self.USERNAME,
                        "password": self.PASSWORD,
                        "database": self.DB,
                        "echo": echo,
                        "maxsize": 20,
                    },
                },
            },
            "apps": {
                "master": {
                    "models": ["storages.relational.models", "aerich.models"],
                    "default_connection": "default",
                }
            },
            # "use_tz": True,   # Will Always Use UTC as Default Timezone
            "timezone": "Asia/Shanghai",
        }


class Redis(HostAndPort):
    USERNAME: Optional[str] = None
    PASSWORD: Optional[str] = None
    DB: int = 0


class Oss(BaseModel):
    ACCESS_KEY_ID: str
    ACCESS_KEY_SECRET: str
    ENDPOINT: str
    EXTERNAL_ENDPOINT: Optional[str]
    BUCKET_NAME: str
    CNAME: Optional[str]  # 自定义域名绑定
    BUCKET_ACL_TYPE: Optional[str] = "private"
    EXPIRE_TIME: int = 60
    MEDIA_LOCATION: Optional[str]
    STATIC_LOCATION: Optional[str]


class CorsConfig(BaseModel):
    ALLOW_ORIGIN: list[str] = ["*"]
    ALLOW_CREDENTIAL: bool = True
    ALLOW_METHODS: list[str] = ["*"]
    ALLOW_HEADERS: list[str] = ["*"]


class Server(HostAndPort):
    REQUEST_SCHEME: str = "https"
    CORS: CorsConfig = CorsConfig()
    WORKERS_NUM: int = (
        multiprocessing.cpu_count() * int(os.getenv("WORKERS_PER_CORE", "2"))
        + 1
    )
    ALLOW_HOSTS: list = ["*"]
    STATIC_PATH: str = "/static"
    STATIC_DIR: str = f"{str(BASE_DIR.absolute())}/static"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"


class Project(BaseModel):
    UNIQUE_CODE: str  # 项目唯一标识，用于redis前缀
    NAME: str = "FastService"
    DESCRIPTION: str = "FastService"
    VERSION: str = "v1"
    DEBUG: bool = False
    ENVIRONMENT: str = EnvironmentEnum.production.value
    LOG_DIR: str = "logs/"
    SKYWALKINGT_SERVER: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    @validator("ENVIRONMENT", allow_reuse=True)
    def check_if_environment_in(cls, v):  # noqa
        env_options = [e.value for e in EnvironmentEnum]
        assert (
            v in env_options
        ), f'Illegal environment config value, options: {",".join(env_options)}'
        return v

    @validator("DEBUG", allow_reuse=True)
    def check_debug_value(
        cls, v: Optional[str], values: Dict[str, Any]
    ):  # noqa
        if "ENVIRONMENT" in values.keys():
            assert not (
                v and values["ENVIRONMENT"] == EnvironmentEnum.production.value
            ), "Production cannot set with debug enabled"
        return v

    @property
    def BASE_DIR(self) -> Path:
        return BASE_DIR


class Hbase(BaseModel):
    SERVERS: list = []


class Kafka(BaseModel):
    SERVERS: list = []


class Jwt(BaseModel):
    SECRET: str
    # AUTH_HEADER_PREFIX: str = "JWT"
    EXPIRATION_DELTA_MINUTES: int = 432000
    REFRESH_EXPIRATION_DELTA_DELTA_MINUTES: int = 4320


class K8s(HostAndPort):
    NAMESPACE: str = ""
    IMAGE: str = ""
    PVC_NAME: str = ""
    CONFIG_FILE: Optional[str] = ""
    CONFIG_MAP_NAME: Optional[str] = ""


class ThirdApiConfig(HostAndPort):
    PROTOCOL: Literal["https", "http", "rpc"] = "https"
    TIMEOUT: int = 6
    EXTRAS: Optional[dict]


class ThirdApiConfigs(BaseModel):
    NACOS: ThirdApiConfig


# class SentryDSN(BaseModel):
#     DSN: str


class LocalConfig(BaseSettings):
    """
    全部的配置信息
    """

    PROJECT: Project

    SERVER: Server

    RELATIONAL: Relational

    REDIS: Redis

    JWT: Jwt

    AES_SECRET: Optional[str]

    SIGN_SECRET: Optional[str]

    OSS: Optional[Oss]

    HBASE: Optional[Hbase]

    KAFKA: Optional[Kafka]  # noqa

    K8S: Optional[K8s]

    THIRD_API_CONFIGS: Optional[ThirdApiConfigs]

    class Config:
        case_sensitive = True
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,  # noqa
        ):
            def json_config_settings_source(
                settings: BaseSettings,
            ) -> Dict[str, Any]:
                encoding = settings.__config__.env_file_encoding
                return ujson.loads(
                    Path(
                        ".".join([CONFIG_FILE_PREFIX, CONFIG_FILE_EXTENSION])
                    ).read_text(encoding)
                )

            return (
                init_settings,
                json_config_settings_source,
                file_secret_settings,
            )


@lru_cache()
def get_local_configs() -> LocalConfig:
    return LocalConfig()


local_configs: LocalConfig = get_local_configs()
