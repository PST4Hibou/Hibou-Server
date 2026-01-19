import abc
from typing import Optional, TypeVar

TController = TypeVar("TController")


class BaseController(abc.ABC):
    """Base class for controlling an audio device."""

    def __init__(self):
        pass

    @classmethod
    @abc.abstractmethod
    def scan_devices(cls) -> Optional[TController]:
        """Scan the network for device dosc"""
        raise NotImplementedError
