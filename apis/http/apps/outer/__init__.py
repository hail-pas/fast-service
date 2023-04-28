from fastapi import Depends, FastAPI

from conf.config import local_configs
from common.fastapi import setup_sub_app
from apis.dependencies import api_key_required
from common.constant.tags import OuterAppTagsEnum
from apis.http.apps.outer.v1 import v1_routes

api_app = FastAPI(
    dependencies=[Depends(api_key_required)],
    title=f"{local_configs.PROJECT.NAME}-外部",
    description=local_configs.PROJECT.DESCRIPTION,
    docs_url=local_configs.SERVER.DOCS_URL
    if local_configs.PROJECT.DEBUG
    else None,
    redoc_url=local_configs.SERVER.REDOC_URL,
    openapi_tags=[
        {"name": name, "description": description}
        for name, description in OuterAppTagsEnum.choices
    ],
)

api_app = setup_sub_app(api_app, "api")

api_app.include_router(v1_routes, prefix="/v1")
