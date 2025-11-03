from __future__ import annotations

import abc


class BaseVendor(abc.ABC):
    """
    Abstract base class for all PTZ camera vendors.

    Defines the interface and common utilities expected from vendor-specific PTZ implementations.
    Concrete vendor classes (e.g., Hikvision, Sony) must inherit from this class
    and implement the abstract methods.
    """

    @abc.abstractmethod
    def set_absolute_ptz_position(
        self, elevation: float, azimuth: float, zoom: float
    ) -> bool:
        """Move the camera to an absolute PTZ position."""
        pass

    @abc.abstractmethod
    def start_continuous(
        self,
        speed: int = 5,
        axis: str = "XY",
        pan_clockwise: bool = True,
        tilt_clockwise: bool = True,
    ) -> bool:
        """Start continuous PTZ motion (panning/tilting)."""
        pass

    @abc.abstractmethod
    def stop_continuous(self) -> None:
        """Stop all ongoing PTZ motion."""
        pass

    @abc.abstractmethod
    def get_status(self, force_update: bool = False) -> dict:
        """Return the current PTZ camera status."""
        pass

    def get_video_stream(self):
        """Optional: subclasses can override to provide RTSP or other streams."""
        raise NotImplementedError("This vendor does not implement video streaming.")
