import os
import ast
import sys
import logging
import traceback
from types import FrameType
from typing import cast
from itertools import chain

from loguru import logger
from gunicorn import glogging

from conf.config import BASE_DIR, EnvironmentEnum, local_configs
from common.utils import datetime_now

LOG_LEVEL = logging.DEBUG if local_configs.PROJECT.DEBUG else logging.INFO

# colorize log
blue = "\x1b[38;5;39m"
cyan = "\x1b[36m"
green = "\x1b[32;20m"
yellow = "\x1b[38;5;226m"
red = "\x1b[38;5;196m"
bold_red = "\x1b[31;1m"
# reset = "\x1b[0m"
no_color = "\033[0m"


class InterceptHandler(logging.Handler):
    """Logs to loguru from Python logging module"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        if record.exc_info:
            # 异常日志处理
            if local_configs.PROJECT.DEBUG:
                print(f"{bold_red}{traceback.format_exc()}")
            else:
                # 保持日志一致性
                tb = traceback.extract_tb(sys.exc_info()[2])
                # 获取最后一个堆栈帧的文件名和行号
                file_name, line_num, func_name, code_str = tb[-1]
                location = f"{file_name}:{func_name}:{line_num}"
                logger.bind(location=location).critical(traceback.format_exc())
            return

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def setup_loguru_logging_intercept(level=logging.DEBUG, modules=()):
    logging.basicConfig(handlers=[InterceptHandler()], level=level)  # noqa
    for logger_name in chain(("",), modules):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler(level=level)]
        # mod_logger.propagate = False


def serialize(record):
    """Serialize the JSON log."""
    log = {}

    # https://docs.datadoghq.com/tracing/connect_logs_and_traces/python/
    # span = ddtrace.tracer.current_span()
    # trace_id, span_id = (span.trace_id, span.span_id) if span else (None, None)

    # # add ids to structlog event dictionary
    # log['dd.trace_id'] = str(trace_id or 0)
    # log['dd.span_id'] = str(span_id or 0)
    # log['dd.env'] = ddtrace.config.env or ""
    # log['dd.service'] = ddtrace.config.service or ""
    # log['dd.version'] = ddtrace.config.version or ""

    log["time"] = record["time"].strftime("%Y:%m:%d %H:%M:%S %Z %z")
    log["level"] = record["level"].name
    log["message"] = record["message"]
    if record["extra"].get("json"):
        # logger.bind(json=True).info()
        # dict/list or python object string convert
        log["message"] = ast.literal_eval(log["message"])
    location = record["name"]
    log["name"] = location
    if record["function"]:
        location = f'{location}:{record["function"]}'
    log["location"] = f'{location}:{record["line"]}'
    log.update(record.get("extra", {}))
    return log


def json_sink(message):
    serialized = serialize(message.record)
    if not serialized:
        return

    color = ""

    if local_configs.PROJECT.ENVIRONMENT == EnvironmentEnum.development.value:
        level_color = {
            "TRACE": blue,
            "DEBUG": cyan,
            "INFO": green,
            "SUCCESS": no_color,
            "WARNING": yellow,
            "ERROR": red,
            "CRITICAL": bold_red,
        }
        color = level_color.get(serialized["level"], no_color)
    print(f"{color}{serialized}")


def init_loguru():
    # loguru
    logger.remove()
    logger.add(
        sink=os.path.join(
            BASE_DIR,
            f'{local_configs.PROJECT.LOG_DIR}{datetime_now().strftime("%Y-%m-%d")}-service.log',
        ),
        rotation="500 MB",  # 日志文件最大限制500mb
        retention="30 days",  # 最长保留30天
        format="{message}",  # 日志显示格式
        compression="zip",  # 压缩形式保存
        encoding="utf-8",  # 编码
        level=LOG_LEVEL,  # 日志级别
        enqueue=True,  # 默认是线程安全的，enqueue=True使得多进程安全
        serialize=True,
        backtrace=True,
        diagnose=True,
    )
    logger.add(
        sink=json_sink,
        format="{message}",  # 日志显示格式
        level=LOG_LEVEL,  # 日志级别
        enqueue=True,  # 默认是线程安全的，enqueue=True使得多进程安全
        serialize=True,
        backtrace=True,
        diagnose=True,
        colorize=True,
    )

    UVICORN_LOGGING_MODULES = (
        "uvicorn.error",
        "uvicorn.asgi",
        "uvicorn.access",
        # "gunicorn.error",
        # "gunicorn.asgi",
        # "gunicorn.access"
        "fastapi",
    )

    setup_loguru_logging_intercept(
        level=logging.getLevelName(LOG_LEVEL), modules=UVICORN_LOGGING_MODULES
    )

    # disable duplicate logging
    logging.getLogger("root").handlers.clear()
    logging.getLogger("uvicorn").handlers.clear()


class GunicornLogger(glogging.Logger):
    def __init__(self, cfg):
        super().__init__(cfg)
        LOGGING_MODULES = (
            "gunicorn.error",
            "gunicorn.asgi",
            "gunicorn.access",
        )
        setup_loguru_logging_intercept(
            level=logging.getLevelName(LOG_LEVEL), modules=LOGGING_MODULES
        )
