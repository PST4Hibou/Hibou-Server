from pathlib import Path

from src.computer_vision import DroneDetection
from src.devices.camera.vendors.hikvision.ds_2dy9250iax_a import DS2DY9250IAXA
from src.devices.camera.ptz_controller import PTZController
from src.settings import SETTINGS
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import random
from collections import deque
from matplotlib.widgets import Button, Slider
from ipywidgets import widgets, interactive

from src.tracking.pid_tracker import PIDTracker


def start_pid_tuning():

    PTZController(
        "main_camera",
        DS2DY9250IAXA,
        host=SETTINGS.PTZ_HOST,
        username=SETTINGS.PTZ_USERNAME,
        password=SETTINGS.PTZ_PASSWORD,
        start_azimuth=SETTINGS.PTZ_START_AZIMUTH,
        end_azimuth=SETTINGS.PTZ_END_AZIMUTH,
        rtsp_port=SETTINGS.PTZ_RTSP_PORT,
        video_channel=SETTINGS.PTZ_VIDEO_CHANNEL,
    )
    stream = PTZController("main_camera").get_video_stream()
    PTZController("main_camera").go_to_angle(phi=20, theta=20)

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from random import randrange

    fig, (ax, ay) = plt.subplots(2, 1)

    drone_detector = DroneDetection(
        enable=SETTINGS.AI_CV_ENABLE,
        model_type=SETTINGS.AI_CV_MODEL_TYPE,
        model_path=Path("assets/computer_vision_models/", SETTINGS.AI_CV_MODEL),
    )

    drone_detector.start(stream, display=SETTINGS.CV_VIDEO_PLAYBACK)

    tracker = PIDTracker(
        pan_pid=PIDTracker.PidCoefs(
            kp=30,
            ki=0.0,
            kd=0.3,
            setpoint=0,
            output_limits=(-20, 20),
        ),
        tilt_pid=PIDTracker.PidCoefs(
            kp=30,
            ki=0.0,
            kd=0.03,
            setpoint=0,
            output_limits=(-5, 5),
        ),
    )

    max_points = 1000
    x = deque(maxlen=max_points)
    y = deque(maxlen=max_points)
    y1 = deque(maxlen=max_points)

    (ln,) = ax.plot([], [])
    (ln2,) = ay.plot([], [])

    ax.set_xlim(0, 10)  # Phase 1: fixed view
    ax.set_ylim(0, 360)

    ay.set_xlim(0, 10)  # Phase 1: fixed view
    ay.set_ylim(0, 360)

    start_time = time.time()

    def update(frame):

        results = drone_detector.get_last_results()

        if results is not None:
            for result in results:
                if result is None:
                    continue
                if not "drone" in result.names.values():
                    continue

                boxes = result.boxes
                for box, cls_id, conf in zip(boxes.xyxyn, boxes.cls, boxes.conf):
                    class_id = int(cls_id.item())
                    if class_id != 0:  # Skip if not a drone
                        continue
                    controls = tracker.update(box)

                    PTZController("main_camera").set_relative_angles(
                        phi=controls[0], theta=-controls[1]
                    )

        # PTZController("main_camera").get_status(force_update=True)
        phi, theta = PTZController("main_camera").get_angles()

        current_time = time.time() - start_time

        x.append(current_time)
        y.append(phi)
        y1.append(theta)

        ln.set_data(x, y)
        ln2.set_data(x, y1)

        # 🔥 Phase switch
        if current_time > 10:
            ax.set_xlim(current_time - 10, current_time)
            ay.set_xlim(current_time - 10, current_time)

        return ln, ln2

    animation = FuncAnimation(fig, update, interval=20)
    plt.show()

    exit()
