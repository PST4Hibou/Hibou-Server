from hikvisionapi import Client

import logging
import math


class PTZ:
    """
    A class to control Hikvision PTZ cameras using the hikvisionapi Client.

    Attributes:
        host (str): IP or hostname of the camera.
        username (str): Username for authentication.
        password (str): Password for authentication.
        elevation (float): Current camera elevation.
        azimuth (float): Current camera azimuth.
        zoom (float): Current zoom level.
        angle (float): Logical angle value used for mapping to azimuth.
    """

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.azimuth = 0
        self.elevation = 0
        self.zoom = 0
        self.angle = 0
        self.client = None

        if not username and not password:
            logging.warning("No username or password provided for PTZ connection.")
            return

        try:
            self.client = Client(f"http://{self.host}", self.username, self.password)
            logging.info(f"Connected to PTZ camera at {self.host}")
        except Exception as e:
            logging.error(f"Failed to connect to PTZ camera at {self.host}: {e}")
            raise ConnectionError(f"PTZ connection failed: {e}")

    def set_position(self, elevation: float, azimuth: float, zoom: float) -> bool:
        """
        Move the camera to an absolute PTZ position.
        """
        if not self.client:
            logging.error("PTZ client not initialized.")
            return False

        self.elevation, self.azimuth, self.zoom = elevation, azimuth, zoom

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
            self.client.PTZCtrl.channels[1].absolute(
                method="put",
                data=xml_absolute,
                headers={"Content-Type": "application/xml"},
            )

            return True

        except Exception as e:
            logging.error(f"Error sending PTZ absolute command: {e}")
            return False

    def get_status(self) -> dict:
        """
        Retrieve current PTZ status and parse useful values.
        """
        if not self.client:
            logging.error("PTZ client not initialized.")
            return {}

        try:
            return self.client.PTZCtrl.channels[1].status(method="get")
        except Exception as e:
            logging.error(f"Failed to get PTZ status: {e}")
            return {}

    def set_angle(self, angle: float):
        """
        Converts a logical angle into azimuth range and moves camera.
        """
        self.angle = angle
        azimuth = math.floor((angle - 0) * (1200 - 750) / (30 - 0) + 750)
        self.set_position(self.elevation, azimuth, self.zoom)
