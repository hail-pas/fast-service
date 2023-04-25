import datetime

from aredis_om.model import Field, HashModel

from storages.redis import AsyncRedisUtil
from storages.redis.keys import ProjectCode


class Vehicle(HashModel):
    vin: str = Field(primary_key=True, description="车辆vin")
    location: str
    report_time: datetime.datetime

    class Meta:
        global_key_prefix = ProjectCode
        model_key_prefix = "Vehicle"
        database = AsyncRedisUtil.get_redis()
        # key_pattern = "{global_key_prefix}:{model_key_prefix}:{vin}"

    # @root_validator
    # def values_validate(cls, values):
    #     ...
    #     return values
