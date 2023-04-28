import time

import httpx
import ujson
from loguru import logger

from common.encrypt import SignAuth


async def request(method, url, api_key, sign_key, **kwargs):
    timestamp = str(int(time.time()))
    headers = kwargs.get("headers", {})
    headers.update({"x-timestamp": timestamp})

    if method in ["get", "delete"]:
        sign_data = kwargs.get("params", {})
    else:
        sign_data = kwargs.get("data", {})
        sign_data.update(kwargs.get("json", {}))
    sign_data_str = ujson.dumps(sign_data, ensure_ascii=False, sort_keys=True)
    logger.debug(f"sign_data: {sign_data}")
    sign_data_str = f"{sign_data_str}&api_key={api_key}&timestamp={timestamp}"
    logger.debug(f"sign_data_str: {sign_data_str}")

    headers["x-sign"] = SignAuth(sign_key).generate_sign(sign_data_str)
    kwargs["headers"] = headers

    async with httpx.AsyncClient() as client:
        return await client.request(method=method, url=url, **kwargs)
