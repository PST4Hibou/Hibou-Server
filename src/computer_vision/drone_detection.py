# computer_vision/object_detection.py
import threading
import logging
import cv2
from time import time

from .models.yolo_model import YOLOModel
from .utils import draw_detections


class DroneDetection:
    """Handles drone detection using a YOLOv8 model with optional background threading."""

    def __init__(self, model_type: str = "yolo", model_path: str = "yolov8n.pt"):
        self.model = YOLOModel(model_path)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._stream: cv2.VideoCapture | None = None

        logging.info(f"DroneDetection initialized with model: {model_type}")

    def _run_detection(self, display: bool = True):
        """Internal method running detection loop in a thread."""
        # while True:
        #     print("hello")
        if self._stream is None or not self._stream.isOpened():
            logging.error("Invalid stream")
            return

        logging.info("Detection loop started")

        while not self._stop_event.is_set():

            ret, frame = self._stream.read()
            if not ret:
                continue

            # FASTEST WAY — YOLO predict()
            results = self.model.predict(frame)
            print(results)
            frame = draw_detections(frame, results)

            if display:
                cv2.imshow("Drone Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.stop()
                    break

        logging.info("Detection loop ended")
        cv2.destroyAllWindows()

    def start(self, stream: cv2.VideoCapture, display: bool = True):
        """Start detection in a background thread."""
        if self._thread and self._thread.is_alive():
            logging.warning("Detection already running.")
            return

        self._stream = stream
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_detection, args=(display,), daemon=True
        )
        self._thread.start()

    def stop(self):
        """Stop the detection thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        """Check if detection thread is active."""
        return self._thread is not None and self._thread.is_alive()

    def __del__(self):
        """Ensure resources are cleaned up on destruction."""
        self.stop()
        cv2.destroyAllWindows()
