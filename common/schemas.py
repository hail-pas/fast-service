from typing import List, Optional

from pydantic import BaseModel, PositiveInt, conint


class Pager(BaseModel):
    limit: PositiveInt = 10
    offset: conint(ge=0) = 0


class CURDPager(Pager):
    order_by: List = []
    search: Optional[str] = None
