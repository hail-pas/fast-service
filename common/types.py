import enum
import uuid
from datetime import datetime

from pydantic import BaseModel


class ClassPropertyDescriptor:
    def __init__(self, fget, fset=None):  # noqa
        self.fget = fget  # noqa
        self.fset = fset  # noqa

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func  # noqa
        return self


def _classproperty(func):
    """
    类属性
    """
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


class MyEnum(enum.Enum):
    @_classproperty
    def dict(cls):
        return {item.value: item.label for item in cls}

    @_classproperty
    def labels(cls):
        return [item.label for item in cls]

    @_classproperty
    def values(cls):
        return [item.value for item in cls]

    @_classproperty
    def choices(cls):
        return [(item.value, item.label) for item in cls]

    @_classproperty
    def help_text(cls):
        description = ""
        for k, v in cls.dict.items():
            description = f"{description}、{k}-{v}"
        return f"choices: {description}"

    @property
    def label(self):
        return self._label

    def _generate_next_value_(name, start, count, last_values) -> str:  # type: ignore
        """
        Uses the name as the automatic value, rather than an integer

        See https://docs.python.org/3/library/enum.html#using-automatic-values for reference
        """
        return name


class IntEnumMore(int, MyEnum):
    def __new__(cls, value, label):
        obj = int.__new__(cls)
        obj._value_ = value
        obj._label = label
        return obj

    def __str__(self) -> str:
        return self.value

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, MyEnum):
            return self.value == __value.value
        return super().__eq__(__value)


class StrEnumMore(str, MyEnum):
    def __new__(cls, value, label):
        obj = str.__new__(cls)
        obj._value_ = value
        obj._label = label
        return obj

    def __str__(self) -> str:
        return self.value

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, MyEnum):
            return self.value == __value.value
        return super().__eq__(__value)


class Map(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super().__delitem__(key)
        del self.__dict__[key]


class JwtPayload(BaseModel):
    account_id: uuid.UUID
    expired_at: datetime
