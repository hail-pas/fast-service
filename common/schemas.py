from typing import Optional

from pydantic import BaseModel, PositiveInt, conint


class Pager(BaseModel):
    limit: PositiveInt = 10
    offset: conint(ge=0) = 0


class CURDPager(Pager):
    order_by: set[str] = set()
    search: Optional[str] = None
    selected_fields: Optional[set[str]] = None
