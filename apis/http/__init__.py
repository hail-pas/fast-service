"""HTTP API."""
from typing import Optional

from fastapi import Request, APIRouter
from pydantic import BaseModel

from conf.config import local_configs
from common.fastapi import RespSchemaAPIRouter
from common.responses import Resp
from apis.http.routes.v1 import v1_routes
from common.constant.tags import TagsEnum

http_routes = APIRouter(route_class=RespSchemaAPIRouter)

# mount apis
# v1
http_routes.include_router(v1_routes)


class HealthCheck(BaseModel):
    name: str
    environment: str
    latest_version: str
    description: Optional[str]


@http_routes.get(
    "/",
    tags=[TagsEnum.root],
    summary="健康检查",
    response_model=Resp[HealthCheck],
)
async def index() -> Resp[HealthCheck]:
    return Resp[HealthCheck](
        message="OK",
        data={
            "name": local_configs.PROJECT.NAME,
            "environment": local_configs.PROJECT.ENVIRONMENT,
            "latest_version": local_configs.PROJECT.VERSION,
            "description": local_configs.PROJECT.DESCRIPTION,
        },
    )


class UriItem(BaseModel):
    method: str
    path: str
    name: Optional[str]
    tags: list[Optional[str]]


@http_routes.get("/uri-list", tags=[TagsEnum.root], summary="全部uri")
def get_all_urls_from_request(request: Request) -> Resp[list[UriItem]]:
    url_list = []
    for route in request.app.routes:
        route_info = {
            "path": route.path,
            "name": getattr(route, "summary", None) or route.name,
            "tags": getattr(route, "tags", []),
        }
        if getattr(route, "methods", []):
            for method in route.methods:
                if method in ["HEAD", "OPTIONS"]:
                    continue
                url_list.append(
                    {
                        "method": method,
                        **route_info,
                    },
                )
        else:
            url_list.append(
                {
                    "method": "ws",
                    **route_info,
                },
            )
    return Resp(data=url_list)
