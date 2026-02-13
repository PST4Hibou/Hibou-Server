from dataclasses import dataclass


def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

@dataclass(frozen=True)
class Range:
    min: int
    max: int