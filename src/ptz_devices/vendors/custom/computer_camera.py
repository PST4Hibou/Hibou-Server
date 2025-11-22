from src.ptz_devices.vendors.base_vendor import BaseVendor

import threading
import logging
import math
import time
import cv2


class ComputerCamera(BaseVendor):
    """
    Singleton for the Computer Camera.
    """

    _instance = None
    _lock = threading.Lock()  # For thread-safe singleton creation

    # Camera channel
    CHANNEL_ID = 0

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        video_channel: int = 0,
    ):
        # Prevent reinitialization if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True  # Flag so __init__ runs only once
        self._cap = cv2.VideoCapture(video_channel)

        if not self._cap.isOpened():
            logging.error("Cannot open computer camera.")
        else:
            logging.info("Computer camera initialized successfully.")

    @classmethod
    def get_instance(cls) -> "ComputerCamera":
        """Return the singleton instance, if already created."""
        if cls._instance is None:
            raise RuntimeError(
                "Camera has not been initialized yet. Call PTZ(...) first."
            )
        return cls._instance

    def _ensure_client_initialized(self) -> bool:
        """Check if the capture client is initialized and log an error if not."""
        if not self._cap:
            logging.error("PTZ client not initialized.")
            return False
        return True

    def get_video_stream(self):
        if not self._initialized:
            return None
        return self._cap

    def release_stream(self):
        """Safely release the video stream."""
        if hasattr(self, "_cap") and self._cap is not None:
            self._cap.release()
            self._cap = None
            logging.info("Capture released.")
