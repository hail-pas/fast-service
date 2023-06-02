import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_root(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json().get("code") == 0


@pytest.mark.asyncio()
async def test_uri_list(client: AsyncClient) -> None:
    response = await client.get("/uri-list")
    assert response.status_code == 200
    assert response.json().get("code") == 0
