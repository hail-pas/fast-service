from common.command import cli


async def init_ctx_db():
    import importlib

    from tortoise import Tortoise

    from conf.config import local_configs

    await Tortoise.init(config=local_configs.RELATIONAL.tortoise_orm_config)
    main = importlib.import_module("__main__")
    ctx = main.__dict__
    ctx.update({"db": Tortoise.get_connection("shell")})


@cli.command("shell", short_help="命令行模式")
def shell():
    import pdb
    import cProfile
    import importlib

    from IPython import start_ipython
    from traitlets.config import Config

    # models = {cls.__name__: cls for cls in BaseModel.__subclasses__()}
    main = importlib.import_module("__main__")
    ctx = main.__dict__
    ctx.update(
        {
            # **models,
            "ipdb": pdb,
            "cProfile": cProfile,
        }
    )
    conf = Config()
    conf.InteractiveShellApp.exec_lines = [
        "print('System Ready!')",
        "from common.command.shell import init_ctx_db",
        "await init_ctx_db()",
        "from storages.redis import AsyncRedisUtil",
        "AsyncRedisUtil.init()",
    ]
    # DEBUG=10, INFO=20, WARN=30
    conf.InteractiveShellApp.log_level = 30
    conf.TerminalInteractiveShell.loop_runner = "asyncio"
    conf.TerminalInteractiveShell.colors = "neutral"
    conf.TerminalInteractiveShell.autoawait = True
    start_ipython(argv=[], user_ns=ctx, config=conf)
