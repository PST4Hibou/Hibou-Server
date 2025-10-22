from hikvisionapi import Client

import logging
import math


class PTZ:
    """
    Provides an interface to control a PTZ (Pan-Tilt-Zoom) camera.

    This class is designed to manage and control PTZ cameras, allowing movement
    across different axes (pan, tilt) and zoom levels. It supports absolute
    positioning, continuous movement, and status retrieval. The class requires
    authentication and establishes a connection to the PTZ client for issuing
    commands.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        start_azimuth: int = None,
        end_azimuth: int = None,
    ):
        self._host = host
        self._username = username
        self._password = password
        self._client = None
        self._MIN_SPEED = 1
        self._MAX_SPEED = 7
        self._start_azimuth = start_azimuth
        self._end_azimuth = end_azimuth

        if not username and not password:
            logging.warning("No username or password provided for PTZ connection.")
            return

        try:
            self._client = Client(
                f"http://{self._host}", self._username, self._password
            )
            logging.info(f"Connected to PTZ camera at {self._host}")
        except Exception as e:
            logging.error(f"Failed to connect to PTZ camera at {self._host}: {e}")
            raise ConnectionError(f"PTZ connection failed: {e}")

    def set_position(self, elevation: float, azimuth: float, zoom: float) -> bool:
        """
        Move the camera to an absolute PTZ position.
        """
        if not self._client:
            logging.error("PTZ client not initialized.")
            return False

        xml_absolute = f"""
        <PTZData>
            <AbsoluteHigh>
                <elevation>{elevation}</elevation>
                <azimuth>{azimuth}</azimuth>
                <absoluteZoom>{zoom}</absoluteZoom>
            </AbsoluteHigh>
        </PTZData>
        """.strip()

        try:
            self._client.PTZCtrl.channels[1].absolute(
                method="put",
                data=xml_absolute,
                headers={"Content-Type": "application/xml"},
            )

            return True

        except Exception as e:
            logging.error(f"Error sending PTZ absolute command: {e}")
            return False

    def _send_continuous_ptz_command(self, pan, tilt) -> bool:
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
        if not self._client:
            logging.error("PTZ client not initialized.")
            return False

        xml_absolute = f"""
            <PTZData><pan>{pan}</pan><tilt>{tilt}</tilt></PTZData>
        """.strip()

        try:
            self._client.PTZCtrl.channels[1].continuous(
                method="put",
                data=xml_absolute,
                headers={"Content-Type": "application/xml"},
            )

            return True

        except Exception as e:
            logging.error(f"Error sending PTZ absolute command: {e}")
            return False

    def start_continuous(
        self, speed: int = 5, axis: str = "XY", pan_clockwise=True, tilt_clockwise=True
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
        speed = max(self._MIN_SPEED, min(speed, self._MAX_SPEED)) * 15

        axis = axis.upper()
        if axis not in {"X", "Y", "XY"}:
            logging.warning(f"Invalid axis '{axis}', defaulting to 'XY'.")
            axis = "XY"

        pan = tilt = 0
        if "X" in axis:
            pan = speed if pan_clockwise else -speed
        if "Y" in axis:
            tilt = speed if tilt_clockwise else -speed
        success = self._send_continuous_ptz_command(pan, tilt)

        if not success:
            logging.debug("Failed to start continuous PTZ movement.")
        return success

    def stop_continuous(self):
        """
        Stops any ongoing continuous PTZ (Pan-Tilt-Zoom) commands.

        This method sends a stop signal to terminate any currently running
        continuous PTZ commands. It sets the pan and tilt velocity to zero, ensuring
        that the movement of the camera stops immediately.

        Raises:
            Exception: If there is an issue while sending the stop command.
        """
        self._send_continuous_ptz_command(0, 0)

    def get_azimuth(self) -> int:
        """
        Gets the azimuth value from the PTZ (Pan-Tilt-Zoom) status.

        The method retrieves the PTZ status and extracts the azimuth value from the
        AbsoluteHigh component. The azimuth represents the horizontal angle of the
        camera's orientation in the PTZ system.

        Returns:
            int: The azimuth value as an integer.
        """
        return int(self.get_status()["PTZStatus"]["AbsoluteHigh"]["azimuth"])

    def get_elevation(self) -> int:
        """
        Gets the elevation value from the PTZ (Pan-Tilt-Zoom) status.

        The method retrieves PTZ status data and extracts the 'elevation' value
        from the absolute high position information.

        Returns:
            int: The elevation value extracted from the PTZ status.

        """
        return int(self.get_status()["PTZStatus"]["AbsoluteHigh"]["elevation"])

    def get_zoom(self) -> int:
        """
        Gets the zoom level of the PTZ (Pan-Tilt-Zoom) camera.

        This method retrieves the absolute zoom level from the camera's current
        status data. The zoom level represents the current zoom factor of the
        camera, as an integer value.

        Returns:
            int: The current absolute zoom level of the camera.
        """
        return int(self.get_status()["PTZStatus"]["AbsoluteHigh"]["absoluteZoom"])

    def get_status(self) -> dict:
        """
        Retrieve current PTZ status and parse useful values.
        """
        if not self._client:
            logging.error("PTZ client not initialized.")
            return {}

        try:
            return self._client.PTZCtrl.channels[1].status(method="get")
        except Exception as e:
            logging.error(f"Failed to get PTZ status: {e}")
            return {}

    def go_to_angle(self, angle: float):
        """
        Converts a logical angle into azimuth range and moves camera.
        """

        status = self.get_status()
        if not status:
            elevation = 0
            zoom = 0
        else:
            elevation = status["PTZStatus"]["AbsoluteHigh"]["elevation"]
            zoom = status["PTZStatus"]["AbsoluteHigh"]["absoluteZoom"]

        azimuth = math.floor(
            (angle - 0) * (self._end_azimuth - self._start_azimuth) / (30 - 0)
            + self._start_azimuth
        )
        self.set_position(elevation, azimuth, zoom)
