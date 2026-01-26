from src.ptz_devices.vendors.base_vendor import BaseVendor
from src.computer_vision.rtsp_stream import RtspSource

import threading
import logging


class OpenCVStreamingVendor(BaseVendor):
    """
    Singleton for OpenCV video streaming from a RTSP source using GST.
    """

    _instance = None
    _lock = threading.Lock()  # For thread-safe singleton creation

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        video_channel: int | str = 0,
    ):
        """

        Args:
            video_channel: Can be an integer (for local camera index) or a string (for video file path).
        """
        # Prevent reinitialization if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True  # Flag so __init__ runs only once
        self._cap = RtspSource(video_channel)
        self._cap.start()

        if not self._cap.is_opened():
            logging.error("Cannot open stream.")
        else:
            logging.info("Computer initialized successfully.")

    @classmethod
    def get_instance(cls) -> "OpenCVStreamingVendor":
        """Return the singleton instance, if already created."""
        if cls._instance is None:
            raise RuntimeError(
                "OpenCVStreamingVendor has not been initialized yet. Call PTZ(...) first."
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
            self._cap.stop()
            self._cap = None
            logging.info("Capture released.")
