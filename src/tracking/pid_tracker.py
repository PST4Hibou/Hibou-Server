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
        yaw_pid_coefs: PIDTracker.PidCoefs,
        pitch_pid_coefs: PIDTracker.PidCoefs,
    ):
        """
        Initialize the PID tracker with specified gains and parameters.
        """
        self.yaw_pid = PID(
            yaw_pid_coefs.kp,
            yaw_pid_coefs.ki,
            yaw_pid_coefs.kd,
            setpoint=yaw_pid_coefs.setpoint,
            output_limits=yaw_pid_coefs.output_limits,
            sample_time=0.2,
        )
        self.pitch_pid = PID(
            pitch_pid_coefs.kp,
            pitch_pid_coefs.ki,
            pitch_pid_coefs.kd,
            setpoint=pitch_pid_coefs.setpoint,
            output_limits=pitch_pid_coefs.output_limits,
            sample_time=0.6,
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

    def update(self, boxn: list[float]) -> tuple[float, float] | None:
        if boxn is None:
            return None

        dx, dy = self.calculate_distance_from_center(boxn)

        # print(f"dx: {dx:.2f}, dy: {dy:.2f}")

        yaw_angle = self.yaw_pid(dx)
        pitch_angle = self.pitch_pid(dy)

        return yaw_angle, pitch_angle
