import sys
import enum
import threading
from typing import Union, Callable
from functools import wraps

from common.types import _classproperty

classproperty = _classproperty


class SingletonDecorator:
    def __init__(self, cls: type) -> None:
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs) -> any:
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance


def timelimit(timeout: Union[int, float]) -> Callable:
    """A decorator to limit a function to `timeout` seconds, raising `TimeoutError`
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
    inspired by <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/473878>.
    """

    def _1(function: Callable) -> Callable:
        @wraps(function)
        def _2(*args, **kw) -> any:
            class Dispatch(threading.Thread):
                def __init__(self) -> None:
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None

                    self.setDaemon(True)
                    self.start()

                def run(self) -> None:
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


def extend_enum(*inherited_enums) -> Callable[[enum.Enum], enum.Enum]:
    def wrapper(added_enum: enum.Enum) -> enum.Enum:
        joined = {}
        for inherited_enum in inherited_enums:
            for item in inherited_enum:
                joined[item.name] = item.value
            for item in added_enum:
                joined[item.name] = item.value
        return enum.Enum(added_enum.__name__, joined)

    return wrapper
