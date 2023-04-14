import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_account_refresh_token(authorized_client: AsyncClient):
    response = await authorized_client.post("/v1/auth/token/refresh")
    assert response.json().get("code") == 0
