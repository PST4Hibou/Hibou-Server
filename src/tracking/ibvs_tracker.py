import math
from src.tracking.base_tracker import BaseTracker


class IBVSTracker(BaseTracker):

    # Desired normalized box area
    DESIRED_AREA = 0.3

    # Dead zone thresholds
    DEAD_ZONE_X = 0.01
    DEAD_ZONE_Y = 0.01

    # Velocity limits (tune to your PTZ hardware)
    MAX_PAN = 10
    MAX_TILT = 10
    MAX_ZOOM = 0.03

    # Control gains
    LAMBDA_PAN = MAX_PAN / 0.5
    LAMBDA_TILT = MAX_TILT / 0.5
    LAMBDA_ZOOM = 0.0008  # slightly higher for log-scale

    # Smoothing factor (0 = no smoothing, 1 = frozen output)
    SMOOTHING_ALPHA = 0.7

    def __init__(self):
        self.prev_pan = 0.0
        self.prev_tilt = 0.0
        self.prev_zoom = 0.0
        self.missed = 0

    def update(self, boxn: list[float]) -> tuple[int, int, int] | None:
        """
        boxn: [x1, y1, x2, y2] in normalized coordinates (0–1)
        Returns: (pan_vel, tilt_vel, zoom_vel)
        """

        if boxn is None or len(boxn) != 4:
            self.missed += 1
            if self.missed > 50:
                return 0, 0, 0
            return None

        x1, y1, x2, y2 = boxn

        # Reject degenerate boxes
        if x2 <= x1 or y2 <= y1:
            return None

        self.missed = 0

        # -----------------------------
        # Feature extraction
        # -----------------------------

        # Box center
        box_center_x = (x1 + x2) / 2.0
        box_center_y = (y1 + y2) / 2.0

        # Image errors (desired center = 0.5, 0.5)
        error_x = box_center_x - 0.5
        error_y = box_center_y - 0.5

        # Dead zone to prevent jitter
        if abs(error_x) < self.DEAD_ZONE_X:
            error_x = 0.0
        if abs(error_y) < self.DEAD_ZONE_Y:
            error_y = 0.0

        # Area (normalized)
        area = (x2 - x1) * (y2 - y1)

        # Prevent log singularity
        if area <= 1e-6:
            return None

        # Log-scale zoom error (better conditioning)
        error_area = math.log(area / self.DESIRED_AREA)

        # -----------------------------
        # IBVS Control Law (P control)
        # -----------------------------

        pan_vel = -self.LAMBDA_PAN * error_x
        tilt_vel = -self.LAMBDA_TILT * error_y
        zoom_vel = -self.LAMBDA_ZOOM * error_area

        # -----------------------------
        # Velocity saturation
        # -----------------------------

        pan_vel = max(min(pan_vel, self.MAX_PAN), -self.MAX_PAN)
        tilt_vel = max(min(tilt_vel, self.MAX_TILT), -self.MAX_TILT)
        zoom_vel = max(min(zoom_vel, self.MAX_ZOOM), -self.MAX_ZOOM)

        # -----------------------------
        # Output smoothing (low-pass)
        # -----------------------------

        pan_vel = (
            self.SMOOTHING_ALPHA * self.prev_pan + (1 - self.SMOOTHING_ALPHA) * pan_vel
        )
        tilt_vel = (
            self.SMOOTHING_ALPHA * self.prev_tilt
            + (1 - self.SMOOTHING_ALPHA) * tilt_vel
        )
        zoom_vel = (
            self.SMOOTHING_ALPHA * self.prev_zoom
            + (1 - self.SMOOTHING_ALPHA) * zoom_vel
        )

        self.prev_pan = pan_vel
        self.prev_tilt = tilt_vel
        self.prev_zoom = zoom_vel

        return int(pan_vel), int(tilt_vel), int(zoom_vel)
