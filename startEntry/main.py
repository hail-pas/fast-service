import sys
import asyncio
from aerich import Command
from conf.config import local_configs

sys.path.append(local_configs.PROJECT.BASE_DIR)

"""FastAPI"""

import gunicorn.app.base

class FastApiApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


async def run_migrations():
    command = Command(
        tortoise_config=local_configs.RELATIONAL.tortoise_orm_config,
        app='master',
        location=f'{local_configs.PROJECT.BASE_DIR.absolute()}/storages/relational/migrate/versions',
    )
    await command.init()
    await command.upgrade()

if __name__ == '__main__':
#     uvicorn.run(
#         "core.factory:app",
#         host=local_configs.SERVER.HOST,
#         port=local_configs.SERVER.PORT,
#         reload=local_configs.PROJECT.DEBUG,
#     )
    # gunicorn core.factory:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80
    # import sys
    asyncio.get_event_loop().run_until_complete(run_migrations())
    options = {
        'bind': '%s:%s' % (local_configs.SERVER.HOST, local_configs.SERVER.PORT),
        'workers': local_configs.SERVER.WORKERS_NUM,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'debug': local_configs.PROJECT.DEBUG,
        'loglevel': 'debug' if local_configs.PROJECT.DEBUG else 'info',
        'max_requests': 4096, # # 最大请求数之后重启worker，防止内存泄漏
        'max_requests_jitter': 512, # 随机重启防止所有worker一起重启：randint(0, max_requests_jitter)
        'graceful_timeout': 120,
        'timeout': 180,
        'logger_class': 'core.loguru.GunicornLogger'
    }
    from core.factory import app
    FastApiApplication(app, options).run()
