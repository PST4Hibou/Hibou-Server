from src.ptz_devices.vendors.base_vendor import BaseVendor
from hikvisionapi import Client


import threading
import logging
import math
import time
import cv2


class DS2DY9250IAXA(BaseVendor):
    """
    Singleton PTZ camera controller.
    Provides an interface to control a PTZ (Pan-Tilt-Zoom) camera, ensuring only one
    instance of the class exists across the entire program.
    """

    _instance = None
    _lock = threading.Lock()  # For thread-safe singleton creation

    # Speed constraints
    MIN_SPEED = 1
    MAX_SPEED = 7
    SPEED_MULTIPLIER = 15

    # Valid axes for movement
    VALID_AXES = {"X", "Y", "XY"}
    DEFAULT_AXIS = "XY"

    # Camera channel
    CHANNEL_ID = 1

    # XML content type
    XML_CONTENT_TYPE = "application/xml"

    # Angle tolerance for movement
    ANGLE_TOLERANCE = 1.5

    MIN_INTERVAL = 1

    def __new__(cls, *args, **kwargs):
        """Ensure only one PTZ instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        start_azimuth: int = None,
        end_azimuth: int = None,
        rtsp_port: int = 554,
        video_channel: int = 1,
    ):
        # Prevent reinitialization if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return

        if not host or not username or not password:
            logging.warning(
                "No username or password provided for PTZ connection. Skipping initialization."
            )
            self._initialized = False
            return

        self._initialized = True  # Flag so __init__ runs only once

        self._host = host
        self._username = username
        self._password = password
        self._client = None
        self._start_azimuth = start_azimuth
        self._end_azimuth = end_azimuth

        self._current_elevation = 0
        self._current_azimuth = 0
        self._current_zoom = 0
        self._current_phi_angle = -50
        self._current_theta_angle = -50
        self._status: dict | None = None
        self._last_angle_update_time = 0

        self.rtsp_url = f"rtsp://{username}:{password}@{host}:{rtsp_port}/Streaming/Channels/10{video_channel}/"
        self.rtsp_stream = cv2.VideoCapture(self.rtsp_url)

        if not self.rtsp_stream.isOpened():
            logging.error("❌ Cannot open RTSP stream. Check the URL or credentials.")
            logging.error(
                f"RTSP URL: rtsp://{username}:XXX@{host}:{rtsp_port}/Streaming/Channels/10{video_channel}/"
            )
        else:
            logging.info("rtsp stream opened")

        if not username and not password:
            logging.warning("No username or password provided for PTZ connection.")
            return

        try:
            self._client = Client(
                f"http://{self._host}", self._username, self._password
            )
            logging.info(f"✅ Connected to PTZ camera at {self._host}")
        except Exception as e:
            logging.error(f"❌ Failed to connect to PTZ camera at {self._host}: {e}")
            raise ConnectionError(f"PTZ connection failed: {e}")

    @classmethod
    def get_instance(cls) -> "DS2DY9250IAXA":
        """Return the singleton PTZ instance, if already created."""
        if cls._instance is None:
            raise RuntimeError("PTZ has not been initialized yet. Call PTZ(...) first.")
        return cls._instance

    def _ensure_client_initialized(self) -> bool:
        """Check if the PTZ client is initialized and log an error if not."""
        if not self._client:
            logging.error("PTZ client not initialized.")
            return False
        return True

    @staticmethod
    def _build_absolute_position_xml(
        elevation: float, azimuth: float, zoom: float
    ) -> str:
        """Build XML command for absolute positioning."""
        return f"""
        <PTZData>
            <AbsoluteHigh>
                <elevation>{elevation}</elevation>
                <azimuth>{azimuth}</azimuth>
                <absoluteZoom>{zoom}</absoluteZoom>
            </AbsoluteHigh>
        </PTZData>
        """.strip()

    @staticmethod
    def _build_continuous_movement_xml(pan: int, tilt: int) -> str:
        """Build XML command for continuous movement."""
        return f"<PTZData><pan>{pan}</pan><tilt>{tilt}</tilt></PTZData>"

    def set_absolute_ptz_position(
        self, elevation: float, azimuth: float, zoom: float
    ) -> bool:
        """
        Move the camera to an absolute PTZ position.
        """
        if not self._ensure_client_initialized():
            return False

        xml_command = self._build_absolute_position_xml(elevation, azimuth, zoom)

        try:
            self._client.PTZCtrl.channels[self.CHANNEL_ID].absolute(
                method="put",
                data=xml_command,
                headers={"Content-Type": self.XML_CONTENT_TYPE},
            )

            self._current_elevation = elevation
            self._current_azimuth = azimuth
            self._current_zoom = zoom

            return True

        except Exception as e:
            logging.error(f"Error sending PTZ absolute command: {e}")
            return False

    def _send_continuous_ptz_command(self, pan: int, tilt: int) -> bool:
        """
        Sends a continuous pan-tilt-zoom (PTZ) command to the PTZ client.

        This method constructs an XML payload for the PTZ command, specifying the pan
        and tilt values, and attempts to send the command via the PTZ client. If the
        client is not initialized or an error occurs during transmission, the method
        logs the error and returns False.

        Args:
            pan: The pan (horizontal) value to send in the PTZ command.
            tilt: The tilt (vertical) value to send in the PTZ command.

        Returns:
            bool: True if the command was sent successfully, otherwise False.
        """
        if not self._ensure_client_initialized():
            return False

        xml_command = self._build_continuous_movement_xml(pan, tilt)

        try:
            self._client.PTZCtrl.channels[self.CHANNEL_ID].continuous(
                method="put",
                data=xml_command,
                headers={"Content-Type": self.XML_CONTENT_TYPE},
            )

            return True

        except Exception as e:
            logging.error(f"Error sending PTZ continuous command: {e}")
            return False

    def _normalize_speed(self, speed: int) -> int:
        """Normalize speed value to valid range and apply multiplier."""
        return max(self.MIN_SPEED, min(speed, self.MAX_SPEED)) * self.SPEED_MULTIPLIER

    def _validate_axis(self, axis: str) -> str:
        """Validate and normalize axis parameter."""
        normalized_axis = axis.upper()
        if normalized_axis not in self.VALID_AXES:
            logging.warning(
                f"Invalid axis '{axis}', defaulting to '{self.DEFAULT_AXIS}'."
            )
            return self.DEFAULT_AXIS
        return normalized_axis

    @staticmethod
    def _calculate_pan_tilt(
        axis: str, speed: int, pan_clockwise: bool, tilt_clockwise: bool
    ) -> tuple[int, int]:
        """Calculate pan and tilt values based on axis and direction."""
        pan = tilt = 0
        if "X" in axis:
            pan = speed if pan_clockwise else -speed
        if "Y" in axis:
            tilt = speed if tilt_clockwise else -speed
        return pan, tilt

    def get_video_stream(self):
        if not self._initialized:
            return None
        return self.rtsp_stream

    def start_continuous(
        self,
        speed: int = 5,
        axis: str = "XY",
        pan_clockwise: bool = True,
        tilt_clockwise: bool = True,
    ) -> bool:
        """
        Starts a continuous Pan-Tilt-Zoom (PTZ) movement command.

        This method initiates a continuous movement of the PTZ camera along the
        specified axis, at the given speed, and in the indicated direction. The
        speed is constrained within the allowable range, and if an invalid axis
        is provided, the method defaults to movement along both axes ("XY").
        The movement direction can independently be specified for both pan
        (horizontal) and tilt (vertical).

        Args:
            speed (int): Speed of the PTZ movement. Defaults to 5.
            axis (str): Axis of movement. Acceptable values are "X", "Y", or "XY".
                Defaults to "XY".
            pan_clockwise (bool): Direction of pan movement. If True, the camera
                pans clockwise. Defaults to True.
            tilt_clockwise (bool): Direction of tilt movement. If True, the camera
                tilts clockwise. Defaults to True.

        Returns:
            bool: True if the continuous movement command is successfully initiated,
                False otherwise.
        """
        normalized_speed = self._normalize_speed(speed)
        validated_axis = self._validate_axis(axis)
        pan, tilt = self._calculate_pan_tilt(
            validated_axis, normalized_speed, pan_clockwise, tilt_clockwise
        )

        success = self._send_continuous_ptz_command(pan, tilt)

        if not success:
            logging.debug("Failed to start continuous PTZ movement.")
        return success

    def stop_continuous(self) -> None:
        """
        Stops any ongoing continuous PTZ (Pan-Tilt-Zoom) commands.

        This method sends a stop signal to terminate any currently running
        continuous PTZ commands. It sets the pan and tilt velocity to zero, ensuring
        that the movement of the camera stops immediately.

        Raises:
            Exception: If there is an issue while sending the stop command.
        """
        self._send_continuous_ptz_command(0, 0)
        self._update_status()

    def get_azimuth(self) -> int:
        """
        Gets the azimuth value from the PTZ (Pan-Tilt-Zoom) status.

        The method retrieves the PTZ status and extracts the azimuth value from the
        AbsoluteHigh component. The azimuth represents the horizontal angle of the
        camera's orientation in the PTZ system.

        Returns:
            int: The azimuth value as an integer.
        """
        return self._current_azimuth

    def get_elevation(self) -> int:
        """
        Gets the elevation value from the PTZ (Pan-Tilt-Zoom) status.

        The method retrieves PTZ status data and extracts the 'elevation' value
        from the absolute high-position information.

        Returns:
            int: The elevation value extracted from the PTZ status.

        """
        return self._current_elevation

    def get_zoom(self) -> int:
        """
        Gets the zoom level of the PTZ (Pan-Tilt-Zoom) camera.

        This method retrieves the absolute zoom level from the camera's current
        status data. The zoom level represents the current zoom factor of the
        camera, as an integer value.

        Returns:
            int: The current absolute zoom level of the camera.
        """
        return self._current_zoom

    def _update_status(self) -> None:
        """Update internal status from PTZ camera."""
        if not self._ensure_client_initialized():
            return

        try:
            status = self._client.PTZCtrl.channels[self.CHANNEL_ID].status(method="get")
            absolute_high = status["PTZStatus"]["AbsoluteHigh"]
            self._current_zoom = int(absolute_high["absoluteZoom"])
            self._current_elevation = int(absolute_high["elevation"])
            self._current_azimuth = int(absolute_high["azimuth"])
            self._status = status
        except Exception as e:
            logging.error(f"Failed to get PTZ status: {e}")

    def get_status(self, force_update: bool = False) -> dict:
        """
        Retrieve current PTZ status and parse useful values.
        """
        if force_update:
            self._update_status()
        return self._status

    def _angle_to_azimuth(self, angle: float) -> int:
        """Convert logical angle to azimuth value within the configured range."""
        return math.floor(
            (angle - 0) * (self._end_azimuth - self._start_azimuth) / (90 - 0)
            + self._start_azimuth
        )

    def _angle_to_elevation(self, angle: float) -> int:
        """Convert logical angle to azimuth value within the configured range."""
        return math.floor(
            (angle - 0) * (self._end_azimuth - self._start_azimuth) / (90 - 0)
            + self._start_azimuth
        )

    def go_to_angle(self, phi: float = None, theta: float = None) -> bool:
        """
        Converts a logical angle into azimuth range and moves the camera.
        Only sends a command if:
        - The change in angle exceeds the tolerance, AND
        - At least MIN_INTERVAL seconds have passed since the previous update.
        """
        if not self._initialized:
            return False

        if phi is None and theta is None:
            return False

        now = time.time()
        dt = now - self._last_angle_update_time

        # Use existing angles if arg is None
        target_phi = phi if phi is not None else self._current_phi_angle
        target_theta = theta if theta is not None else self._current_theta_angle

        delta_phi = abs(target_phi - self._current_phi_angle)
        delta_theta = abs(target_theta - self._current_theta_angle)

        # Check tolerance and minimal time interval
        angle_change_small = (delta_phi < self.ANGLE_TOLERANCE) and (
            delta_theta < self.ANGLE_TOLERANCE
        )
        too_soon = dt < self.MIN_INTERVAL

        if angle_change_small or too_soon:
            return False

        # Update internal state
        self._last_angle_update_time = now
        self._current_phi_angle = target_phi
        self._current_theta_angle = target_theta

        azimuth = self._angle_to_azimuth(target_phi)
        elevation = target_theta  # TODO: Find correct map.

        return self.set_absolute_ptz_position(elevation, azimuth, self._current_zoom)

    def release_stream(self):
        """Safely release the RTSP stream."""
        if hasattr(self, "rtsp_stream") and self.rtsp_stream is not None:
            self.rtsp_stream.release()
            self.rtsp_stream = None
            logging.info("📷 RTSP stream released.")
