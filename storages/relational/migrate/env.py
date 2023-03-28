from conf.config import local_configs

TORTOISE_ORM_CONFIG = local_configs.RELATIONAL.tortoise_orm_config


"""
1. aerich init -t storages.relational.migrate.env.TORTOISE_ORM_CONFIG  --location storages/relational/migrate/versions
2. aerich init-db  # create initial version with version record table
3. aerich migrate --name "message"  # makemigrations
4. aerich upgrade  # migrate
5. aerich upgrade -v -1 # down
6. aerich heads
7. aerich history
8. aerich --app master inspectdb -t table_name  # inspect sql to tortoise orm

>>>>>>> 生成的迁移文件有两个分号, 会导致执行失败
"""
