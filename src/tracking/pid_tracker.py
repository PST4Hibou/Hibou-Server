from __future__ import annotations
from src.tracking.base_tracker import BaseTracker
from simple_pid import PID

import dataclasses


class PIDTracker(BaseTracker):
    """
    PID-based tracker implementation.
    """

    @dataclasses.dataclass
    class PidCoefs:
        kp: float
        ki: float
        kd: float
        setpoint: float = 0.0
        output_limits: tuple[float | None, float | None] = (None, None)

    def __init__(
        self,
        pan_pid: PIDTracker.PidCoefs,
        tilt_pid: PIDTracker.PidCoefs,
        zoom_pid: PIDTracker.PidCoefs,
    ):
        """
        Initialize the PID tracker with specified gains and parameters.
        """
        self.pan_pid = PID(
            pan_pid.kp,
            pan_pid.ki,
            pan_pid.kd,
            setpoint=pan_pid.setpoint,
            output_limits=pan_pid.output_limits,
            sample_time=0.6,
        )
        self.tilt_pid = PID(
            tilt_pid.kp,
            tilt_pid.ki,
            tilt_pid.kd,
            setpoint=tilt_pid.setpoint,
            output_limits=tilt_pid.output_limits,
            sample_time=0.6,
        )

        self.zoom_pid = PID(
            zoom_pid.kp,
            zoom_pid.ki,
            zoom_pid.kd,
            setpoint=zoom_pid.setpoint,
            output_limits=zoom_pid.output_limits,
            sample_time=1,
        )

    @staticmethod
    def calculate_distance_from_center(boxn: list[float]) -> tuple[float, float]:
        """
        Calculate  offset of the box center from the image center.
        The output range is [-0.5, 0.5].
        """

        # Frame center for normalized coordinates
        frame_center_x = 0.5
        frame_center_y = 0.5

        x1, y1, x2, y2 = boxn

        # Box center
        box_center_x = (x1 + x2) / 2
        box_center_y = (y1 + y2) / 2

        dx = frame_center_x - box_center_x
        dy = frame_center_y - box_center_y

        return dx, dy

    def update(self, boxn: list[float]) -> tuple[float, float, float] | None:
        if boxn is None:
            return None

        # PTZ orientation
        dx, dy = self.calculate_distance_from_center(boxn)

        pan_angle = self.pan_pid(dx)
        tilt_angle = self.tilt_pid(dy)

        # Zoom level
        zoom_level = self.zoom_pid(boxn[2] - boxn[0])

        return pan_angle, -tilt_angle, zoom_level
