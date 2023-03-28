import sys
import enum
import threading
from typing import Union
from functools import wraps

from common.types import _classproperty

classproperty = _classproperty


def partial(func, *args):
    """
    保留函数签名的partial装饰器
    """

    def new_func(*func_args):
        return func(*(args + func_args))

    new_func.func = func
    new_func.args = args
    return new_func


def timelimit(timeout: Union[int, float, str]):
    """
    A decorator to limit a function to `timeout` seconds, raising `TimeoutError`
    if it takes longer.
        >>> import time
        >>> def meaningoflife():
        ...     time.sleep(.2)
        ...     return 42
        >>>
        >>> timelimit(.1)(meaningoflife)()
        Traceback (most recent call last):
            ...
        RuntimeError: took too long
        >>> timelimit(1)(meaningoflife)()
        42
    _Caveat:_ The function isn't stopped after `timeout` seconds but continues
    executing in a separate thread. (There seems to be no way to kill a thread.)
    inspired by <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/473878>
    """

    def _1(function):
        @wraps(function)
        def _2(*args, **kw):
            class Dispatch(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None

                    self.setDaemon(True)
                    self.start()

                def run(self):
                    try:
                        self.result = function(*args, **kw)
                    except Exception:
                        self.error = sys.exc_info()

            c = Dispatch()
            c.join(timeout)
            if c.is_alive():
                raise RuntimeError("took too long")
            if c.error:
                raise c.error[1]
            return c.result

        return _2

    return _1


def extend_enum(*inherited_enums):
    def wrapper(added_enum):
        joined = {}
        for inherited_enum in inherited_enums:
            for item in inherited_enum:
                joined[item.name] = item.value
            for item in added_enum:
                joined[item.name] = item.value
        return enum.Enum(added_enum.__name__, joined)

    return wrapper
