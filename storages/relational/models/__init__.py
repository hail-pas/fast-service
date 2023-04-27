from tortoise import Tortoise

from storages.relational.models.task import *  # noqa
from storages.relational.models.account import *  # noqa

# init model relations, 启动时慢. 好处是 pydantic_model_creator自动创建 逆向关联的model字段
Tortoise.init_models(["storages.relational.models"], "master")
