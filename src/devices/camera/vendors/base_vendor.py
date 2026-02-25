from src.helpers.decorators import Range
from dataclasses import dataclass
from typing import Final

import numpy as np
import abc


@dataclass(frozen=True)
class PTZAxisRange:
    logical: Range
    hardware: Range


class BaseVendor(abc.ABC):
    """
    Abstract base class for all PTZ camera vendors.

    Defines the interface and common utilities expected from vendor-specific PTZ implementations.
    Concrete vendor classes (e.g., Hikvision) must inherit from this class
    and implement the abstract methods.
    """

    SPEED_RANGE: Final[Range] = Range(-10, 10)
    PAN_RANGE: Final[Range] = Range(0, 360)
    TILT_RANGE: Final[Range] = Range(-90, 40)
    ZOOM_RANGE: Final[Range] = Range(1, 20)

    ANGLE_TOLERANCE: Final[float] = 1.0
    MIN_TIME_INTERVAL: Final[int] = 1

    VALID_AXES = {"X", "Y", "XY"}

    RATE_LIMIT_INTERVAL: Final[int] = 1

    # PAN
    def _validate_pan(self, pan: float) -> None:
        if not (self.PAN_RANGE.min <= pan <= self.PAN_RANGE.max):
            raise ValueError(
                f"Pan must be between {self.PAN_RANGE.min} " f"and {self.PAN_RANGE.max}"
            )

    def _clamp_pan(self, pan: float) -> float:
        return np.clip(pan, self.PAN_RANGE.min, self.PAN_RANGE.max)

    # TILT
    def _validate_tilt(self, tilt: float) -> None:
        if not (self.TILT_RANGE.min <= tilt <= self.TILT_RANGE.max):
            raise ValueError(
                f"Tilt must be between {self.TILT_RANGE.min} "
                f"and {self.TILT_RANGE.max}"
            )

    def _clamp_tilt(self, tilt: float) -> float:
        return np.clip(tilt, self.TILT_RANGE.min, self.TILT_RANGE.max)

    # ZOOM
    def _validate_zoom(self, zoom: int) -> None:
        if not (self.ZOOM_RANGE.min <= zoom <= self.ZOOM_RANGE.max):
            raise ValueError(
                f"Zoom must be between {self.ZOOM_RANGE.min} "
                f"and {self.ZOOM_RANGE.max}"
            )

    def _clamp_zoom(self, zoom: int) -> int:
        return np.clip(zoom, self.ZOOM_RANGE.min, self.ZOOM_RANGE.max)

    # SPEED
    def _validate_speed(self, speed: int) -> None:
        if not (self.SPEED_RANGE.min <= speed <= self.SPEED_RANGE.max):
            raise ValueError(
                f"Speed must be between {self.SPEED_RANGE.min} "
                f"and {self.SPEED_RANGE.max}"
            )

    def _clamp_speed(self, speed: int) -> int:
        return np.clip(speed, self.SPEED_RANGE.min, self.SPEED_RANGE.max)

    def _validate_axis(self, axis: str) -> bool:
        """Validate and normalize axis parameter."""
        normalized_axis = axis.upper()
        if normalized_axis not in self.VALID_AXES:
            return False
        return True

    @abc.abstractmethod
    def _set_absolute_ptz_position(
        self,
        pan: float | None,
        tilt: float | None,
        zoom: int | None,
    ) -> bool:
        raise NotImplementedError(
            "This vendor does not implement absolute positioning."
        )

    @abc.abstractmethod
    def _set_relative_ptz_position(
        self,
        pan: float | None,
        tilt: float | None,
        zoom: int | None,
    ) -> bool:
        raise NotImplementedError(
            "This vendor does not implement absolute positioning."
        )

    @abc.abstractmethod
    def _start_continuous(self, pan_speed: int, tilt_speed: int) -> bool:
        raise NotImplementedError(
            "This vendor does not implement continuous PTZ motion."
        )

    @abc.abstractmethod
    def is_initialized(self) -> bool:
        raise NotImplementedError("This vendor does not implement initialization.")

    @abc.abstractmethod
    def stop_continuous(self):
        raise NotImplementedError(
            "This vendor does not implement stopping continuous PTZ motion."
        )

    @abc.abstractmethod
    def get_status(self, force_update: bool = False) -> dict:
        """Return the current PTZ camera status."""
        raise NotImplementedError("This vendor does not implement status retrieval.")

    @abc.abstractmethod
    def get_video_stream(self):
        """Optional: subclasses can override to provide RTSP or other streams."""
        raise NotImplementedError("This vendor does not implement video streaming.")

    def set_absolute_ptz_position(
        self,
        pan: float | None = None,
        tilt: float | None = None,
        zoom: int | None = None,
        clamp: bool = False,
    ) -> bool:

        if not self.is_initialized():
            raise RuntimeError("Vendor not initialized.")

        if pan is not None:
            if clamp:
                pan = self._clamp_pan(pan)
            else:
                self._validate_pan(pan)

        if tilt is not None:
            if clamp:
                tilt = self._clamp_tilt(tilt)
            else:
                self._validate_tilt(tilt)

        if zoom is not None:
            if clamp:
                zoom = self._clamp_zoom(zoom)
            else:
                self._validate_zoom(zoom)

        return self._set_absolute_ptz_position(
            pan=pan,
            tilt=tilt,
            zoom=zoom,
        )

    def set_relative_ptz_position(
        self,
        pan: float | None = None,
        tilt: float | None = None,
        zoom: int | None = None,
    ) -> bool:
        if not self.is_initialized():
            raise RuntimeError("Vendor not initialized.")

        return self._set_relative_ptz_position(
            pan=pan,
            tilt=tilt,
            zoom=zoom,
        )

    def start_continuous(
        self,
        pan_speed: int = 5,
        tilt_speed: int = 5,
        clamp: bool = False,
    ):
        if not self.is_initialized():
            raise RuntimeError("Vendor not initialized.")

        if clamp:
            pan_speed = self._clamp_speed(pan_speed)
            tilt_speed = self._clamp_speed(tilt_speed)
        else:
            self._validate_speed(pan_speed)
            self._validate_speed(tilt_speed)

        return self._start_continuous(pan_speed, tilt_speed)

    def set_3d_position(self, start_x, start_y, end_x, end_y) -> bool:
        raise NotImplementedError("This vendor does not implement 3D positioning.")
