from fastapi import APIRouter

from common.fastapi import RespSchemaAPIRouter
from apis.http.apps.outer.v1.ping.views import router as ping_router

v1_routes = APIRouter(route_class=RespSchemaAPIRouter)

v1_routes.include_router(ping_router)
