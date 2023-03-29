import sys
import asyncio

import gunicorn.app.base
from aerich import Command

from conf.config import local_configs

sys.path.append(local_configs.PROJECT.BASE_DIR)

"""FastAPI"""


class FastApiApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def post_fork(server, worker):
    # Important: The import of skywalking should be inside the post_fork function
    if local_configs.PROJECT.SKYWALKINGT_SERVER:
        print({"level": "INFO", "message": "Skywalking agent started"})
        import os

        from skywalking import agent, config

        # append pid-suffix to instance name
        # This must be done to distinguish instances if you give your instance customized names
        # (highly recommended to identify workers)
        # Notice the -child(pid) part is required to tell the difference of each worker.
        agent_instance_name = f"python:fast-service-child({os.getpid()})"

        config.init(
            agent_collector_backend_services="192.168.3.46:11800",
            agent_name=f"python:{local_configs.PROJECT.NAME}",
            agent_instance_name=agent_instance_name,
            plugin_fastapi_collect_http_params=True,
            agent_protocol="grpc",
        )

        agent.start()


async def run_migrations():
    command = Command(
        tortoise_config=local_configs.RELATIONAL.tortoise_orm_config,
        app="master",
        location=f"{local_configs.PROJECT.BASE_DIR.absolute()}/storages/relational/migrate/versions",
    )
    await command.init()
    await command.upgrade()


if __name__ == "__main__":
    # gunicorn core.factory:app
    # --workers 4
    # --worker-class uvicorn.workers.UvicornWorker
    # --timeout 180
    # --graceful-timeout 120
    # --max-requests 4096
    # --max-requests-jitter 512
    # --log-level debug
    # --logger-class core.loguru.GunicornLogger
    # --bind 0.0.0.0:80
    # import sys
    asyncio.get_event_loop().run_until_complete(run_migrations())
    options = {
        "bind": "%s:%s"
        % (local_configs.SERVER.HOST, local_configs.SERVER.PORT),
        "workers": 1,  # local_configs.SERVER.WORKERS_NUM,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "debug": local_configs.PROJECT.DEBUG,
        "log_level": "debug" if local_configs.PROJECT.DEBUG else "info",
        "max_requests": 4096,  # # 最大请求数之后重启worker，防止内存泄漏
        "max_requests_jitter": 512,  # 随机重启防止所有worker一起重启：randint(0, max_requests_jitter)
        "graceful_timeout": 120,
        "timeout": 180,
        "logger_class": "core.loguru.GunicornLogger",
        "config": "startEntry.gunicorn_conf.py",
        "post_fork": "startEntry.main.post_fork",
    }
    from core.factory import app

    FastApiApplication(app, options).run()
