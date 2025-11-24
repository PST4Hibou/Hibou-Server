from __future__ import annotations
import dataclasses
import math
from simple_pid import PID
from ultralytics.engine.results import Results
from src.tracking.base_tracker import BaseTracker


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
        )
        self.pitch_pid = PID(
            pitch_pid_coefs.kp,
            pitch_pid_coefs.ki,
            pitch_pid_coefs.kd,
            setpoint=pitch_pid_coefs.setpoint,
            output_limits=pitch_pid_coefs.output_limits,
        )

    @staticmethod
    def calculate_min_distance_from_center(result: Results):
        """
        Calculate the minimum distance from the center between all the boxes detected for an object
        """
        img_h, img_w = result.orig_img.shape[:2]
        frame_center_x = img_w / 2
        frame_center_y = img_h / 2

        min_dx, min_dy = float("inf"), float("inf")

        for x1, y1, x2, y2 in result.boxes.xyxy.tolist():
            box_center_x = (x1 + x2) / 2
            box_center_y = (y1 + y2) / 2

            dx = abs(frame_center_x - box_center_x)
            dy = abs(frame_center_y - box_center_y)

            min_dx = min(min_dx, dx)
            min_dy = min(min_dy, dy)

        return min_dx, min_dy

    def update(self, results: list[Results] | None) -> tuple[float, float] | None:
        """
        Update the tracker state based on new detection results.

        :param results: Detection results from the object detection model
        """
        if results is None:
            return None

        min_dx, min_dy = math.inf, math.inf
        for result in results:
            dx, dy = self.calculate_min_distance_from_center(result)

            min_dx = min(min_dx, dx)
            min_dy = min(min_dy, dy)

        yaw_angle = self.yaw_pid(min_dx)
        pitch_angle = self.yaw_pid(min_dy)

        return yaw_angle, pitch_angle
