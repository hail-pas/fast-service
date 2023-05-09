import asyncio
from types import ModuleType
from typing import Union, Iterable
from urllib.parse import quote

import pytest
import pytest_asyncio
from httpx import AsyncClient
from tortoise import Tortoise
from tortoise.exceptions import OperationalError, DBConnectionError
from tortoise.contrib.test import _generate_config

from conf.config import local_configs
from core.factory import app
from common.encrypt import PasswordUtil
from storages.relational.models import Role, System, Account

TORTOISE_TEST_DB = "sqlite://:memory:"
AUTHORIZED_CONFIG = {
    "username": "admin",
    "nickname": "admin",
    "password": "admin",
    # "roles": "admin",
    # "systems": "default"
}

TEST_CONNECTION_CONGIF = local_configs.RELATIONAL.tortoise_orm_config.get(
    "connections"
).get("test")
if TEST_CONNECTION_CONGIF:
    TORTOISE_TEST_DB = f"mysql://{quote(TEST_CONNECTION_CONGIF.get('credentials').get('user'))}:{quote(TEST_CONNECTION_CONGIF.get('credentials').get('password'))}@{TEST_CONNECTION_CONGIF.get('credentials').get('host')}:{TEST_CONNECTION_CONGIF.get('credentials').get('port')}/fast_service_test?charset=utf8mb4"  # noqa


def getTestDBConfig(
    app_label: str, modules: Iterable[Union[str, ModuleType]]
) -> dict:
    return _generate_config(
        TORTOISE_TEST_DB,
        app_modules={app_label: modules},
        testing=True,
        connection_label=app_label,
    )


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """event loop"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncClient:
    """不携带授权头部的 FastApi Client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def initialize_db(request) -> None:
    """初始化数据库"""
    # db_url = "sqlite://:memory:"
    # initializer(["storages.relational.models"], db_url=db_url, app_label="master")
    # request.addfinalizer(finalizer)
    config = getTestDBConfig(
        app_label="master", modules=["storages.relational.models"]
    )

    async def _init_db() -> None:
        await Tortoise.init(config)
        try:
            await Tortoise._drop_databases()
        except (DBConnectionError, OperationalError):  # pragma: nocoverage
            pass

        await Tortoise.init(config, _create_db=True)
        await Tortoise.generate_schemas(safe=False)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_init_db())

    request.addfinalizer(
        lambda: loop.run_until_complete(Tortoise._drop_databases())
    )


@pytest_asyncio.fixture(scope="session")
async def initialize_resources(initialize_db) -> tuple[Account, Role]:
    """
    初始化resources、systems、roles、permissions、accounts
    做为测试的调用账户
    """
    # 创建用户

    test_account = await Account.create(
        username=AUTHORIZED_CONFIG["username"],
        password=PasswordUtil.get_password_hash(AUTHORIZED_CONFIG["password"]),
        nickname=AUTHORIZED_CONFIG["nickname"],
    )
    await System.create(label="burnish", code="burnish")
    role = await Role.create(label="admin", code="admin")
    await test_account.roles.add(role)
    return test_account, role


@pytest_asyncio.fixture(scope="session")
async def get_token_and_role(client, initialize_resources) -> tuple[str, Role]:
    account, role = initialize_resources
    username = account.username
    # username = AUTHORIZED_CONFIG["username"]
    password = AUTHORIZED_CONFIG["password"]

    login_response = await client.post(
        "/v1/auth/login", json={"username": username, "password": password}
    )
    assert login_response.json().get("code") == 0

    return login_response.json().get("data").get("access_token"), role


@pytest_asyncio.fixture(scope="session")
async def authorized_client(get_token_and_role) -> AsyncClient:
    """带授权头部的 FastApi Client"""
    token, role = get_token_and_role
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Role-Id": str(role.id),
        },
    ) as client:
        yield client
