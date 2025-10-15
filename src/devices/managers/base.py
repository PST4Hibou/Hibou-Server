from __future__ import annotations
from typing import Generic, List, TypeVar

import abc

# Define type variables
TSource = TypeVar("TSource")  # Raw device type (e.g., DanteDevice)
TTarget = TypeVar("TTarget")  # Internal model type (e.g., Device)


class DeviceManager(abc.ABC, Generic[TSource, TTarget]):
    """Base class for all network audio device managers."""

    @staticmethod
    @abc.abstractmethod
    async def _scan_devices() -> List[TSource]:
        """Async discovery logic implemented by subclasses."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def scan_devices(cls) -> List[TTarget]:
        """Sync wrapper for device discovery."""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def to_device(device: TSource) -> TTarget:
        """Convert a discovered raw device into the internal Device model."""
        raise NotImplementedError
