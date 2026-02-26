from dataclasses import dataclass


class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in SingletonMeta._instances:
            SingletonMeta._instances[cls] = super().__call__(*args, **kwargs)
        return SingletonMeta._instances[cls]

def singleton(cls):
    return SingletonMeta(cls.__name__, cls.__bases__, dict(cls.__dict__))


@dataclass(frozen=True)
class Range:
    min: int
    max: int
