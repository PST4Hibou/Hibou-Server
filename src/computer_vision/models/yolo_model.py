from ultralytics import YOLO
import logging


class YOLOModel:
    """General YOLO model wrapper for v8, v11, etc."""

    def __init__(self, model_path: str):
        try:
            self.model = YOLO(model_path)
            logging.info(f"✅ Loaded YOLO model: {model_path}")
        except Exception as e:
            logging.error(f"❌ Failed to load YOLO model: {e}")
            raise

    def track(self, frame):
        """Run tracking/detection on a frame."""
        # YOLOv8 and YOLOv11 support .track() or .predict() APIs
        results = self.model.track(frame, stream=True)
        return results
