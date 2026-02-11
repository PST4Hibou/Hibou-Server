from src.computer_vision.video_source import VideoSource
from ultralytics.engine.results import Results
from .models.yolo_model import YOLOModel
from .utils import draw_detections
from collections import deque
from pathlib import Path

import threading
import logging
import time
import cv2


class DroneDetection:
    """Handles drone detection using a YOLOv8 model with optional background threading."""

    def __init__(
        self,
        model_type: str = "yolo",
        model_path: Path = "yolov8n.pt",
        enable: bool = True,
    ):
        if not enable:
            logging.warning("Drone detection disabled.")
            return
        self.model = YOLOModel(model_path)
        self.channels = self.model.model.yaml.get("channels")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._stream: VideoSource | None = None
        self._fps = 0.0

        self.results_queue = deque(maxlen=1)

        logging.info(f"DroneDetection initialized with model: {model_type}")

    def _run_detection(self, display: bool = True):
        """Internal method running detection loop in a thread."""
        if self._stream is None or not self._stream.is_opened():
            logging.error("Invalid stream")
            return

        logging.info("Detection loop started")

        while not self._stop_event.is_set():
            ret, frame = self._stream.get_frame()
            if not ret:
                self._sleep()
                continue

            # FASTEST WAY — YOLO predict()
            if self.channels == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            results = self.model.predict(frame)

            # If it contains drones
            if any([len(result.boxes) > 0 for result in results]):
                self.results_queue.append(results)
                frame = draw_detections(frame, results)

            if display:
                # display_frame = cv2.resize(
                #     frame,
                #     dsize=(
                #         frame.shape[1] // 2,
                #         frame.shape[0] // 2,
                #     ),
                #     interpolation=cv2.INTER_AREA,
                # )
                cv2.imshow("Drone Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.stop()
                    break

            self._sleep()

        logging.info("Detection loop ended")
        cv2.destroyAllWindows()

    def _sleep(self):
        """Method used to let other code parts run. Should be called from _run_detection loop."""
        if self._fps == 0.0:
            self._fps = self._stream.get_fps()
            if self._fps != 0.0:
                self._fps = 1.0 / self._stream.get_fps()

        time.sleep(self._fps / 10.0)

    def get_last_results(self) -> list[Results] | None:
        """Retrieves the first available result."""
        try:
            return self.results_queue.pop()
        except IndexError:
            return None

    def is_empty(self) -> bool:
        """Tells if the results list is empty."""
        return len(self.results_queue) == 0

    def start(self, stream: VideoSource, display: bool = True):
        """Start detection in a background thread."""
        if not self.model:
            return
        if self._thread and self._thread.is_alive():
            logging.warning("Detection already running.")
            return

        self._stream = stream
        self._fps = self._stream.get_fps()
        if self._fps != 0.0:
            self._fps = 1.0 / self._fps
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
