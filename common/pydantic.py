import inspect
from typing import List
from datetime import datetime

import pydantic

from common.utils import DATETIME_FORMAT_STRING, filter_dict


def optional(*fields):
    """Decorator function used to modify a pydantic model's fields to all be optional.
    Alternatively, you can  also pass the field names that should be made optional as arguments
    to the decorator.
    Taken from https://github.com/samuelcolvin/pydantic/issues/1223#issuecomment-775363074
    """

    def dec(_cls):
        for field in fields:
            _cls.__fields__[field].required = False
        return _cls

    if (
        fields
        and inspect.isclass(fields[0])
        and issubclass(fields[0], pydantic.BaseModel)
    ):
        cls = fields[0]
        fields = cls.__fields__
        return dec(cls)

    return dec


class DateTimeFormatConfig:
    json_encoders = {
        datetime: lambda v: v.strftime(DATETIME_FORMAT_STRING),
    }


def sub_fields_model(
    base_model: pydantic.BaseModel,
    fields: List[str],
) -> pydantic.BaseModel:
    class ToModel(base_model):
        pass

    ToModel.__fields__ = filter_dict(
        ToModel.__fields__, lambda k, _: k in fields
    )
    ToModel.__config__.fields = filter_dict(
        ToModel.__config__.fields, lambda k, _: k in fields
    )
    return ToModel
