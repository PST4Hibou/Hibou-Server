import abc
from typing import List, Optional, TypeVar

from src.devices.audio.dante.models import DanteADCDevice

TController = TypeVar("TController")


class BaseController(abc.ABC):
    """Base class for controlling an audio device."""

    def __init__(self):
        self.adc_devices: List[DanteADCDevice] = []

    @classmethod
    @abc.abstractmethod
    def scan_devices(cls) -> Optional[TController]:
        """Scan the network for device dosc"""
        raise NotImplementedError
