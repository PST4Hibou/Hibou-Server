# computer_vision/utils.py
import random
import cv2


def get_class_colour(cls_num: int):
    """Generate a unique color for each class ID."""
    random.seed(cls_num)
    return tuple(random.randint(0, 255) for _ in range(3))


def draw_detections(frame, results, conf_threshold=0.4):
    """Draw YOLOv8 detection boxes and labels on a frame."""
    for result in results:
        class_names = result.names
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf < conf_threshold:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            class_name = class_names[cls]
            colour = get_class_colour(cls)

            cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
            cv2.putText(
                frame,
                f"{class_name} {conf:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                colour,
                2,
            )
    return frame
