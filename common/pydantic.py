from datetime import datetime

from common.utils import DATETIME_FORMAT_STRING


class DateTimeFormatConfig:
    json_encoders = {
        datetime: lambda v: v.strftime(DATETIME_FORMAT_STRING),
    }
