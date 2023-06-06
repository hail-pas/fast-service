from pydantic import Field, BaseModel


class CaptchaCodeResponse(BaseModel):
    unique_key: str = Field(description="验证码唯一标识")
