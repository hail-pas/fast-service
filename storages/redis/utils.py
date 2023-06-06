from typing import Optional

from common.enums import ResponseCodeEnum
from common.utils import generate_random_string
from storages.redis import AsyncRedisUtil
from common.exceptions import ApiException
from storages.redis.keys import RedisCacheKey
from common.constant.messages import RequestLimitedMsg


async def generate_capthca_code(
    unique_key: str,
    length: int,
    all_digits: bool = False,
    excludes: Optional[list] = None,
) -> str:
    if await AsyncRedisUtil.get(
        RedisCacheKey.CaptchaCodeKey.format(unique_key=unique_key),
    ):
        raise ApiException(
            message=RequestLimitedMsg,
            code=ResponseCodeEnum.request_limited.value,
        )
    code = generate_random_string(length, all_digits, excludes)
    await AsyncRedisUtil.set(
        RedisCacheKey.CaptchaCodeKey.format(unique_key=unique_key),
        code,
        exp=60 * 5,
    )
    return code


async def verify_captcha_code(unique_key: str, code: str) -> bool:
    return (
        await AsyncRedisUtil.get(
            RedisCacheKey.CaptchaCodeKey.format(unique_key=unique_key),
        )
        == code
    )
