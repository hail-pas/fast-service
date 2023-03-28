from pydantic import PositiveInt, conint
from fastapi_pagination.default import Params, RawParams


class Pager(Params):
    limit: PositiveInt = 10
    offset: conint(ge=0) = 0

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.limit,
            offset=self.offset,
        )
