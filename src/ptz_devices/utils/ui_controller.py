import threading
import time
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from src.ptz_devices.ptz_controller import PTZController


def start_ui_controller(ptz_name: str, text_bottom: str = ""):

    speed = 4
    min_speed, max_speed = 1, 7
    current_direction = {"axis": None, "pan_cw": None, "tilt_cw": None}
    running = True

    # ---- Continuous PTZ Loop ----
    def loop_motion():
        while running:
            if current_direction["axis"]:
                axis = str(current_direction["axis"])
                pan_cw = current_direction["pan_cw"]
                tilt_cw = current_direction["tilt_cw"]
                PTZController(ptz_name).start_continuous(
                    speed,
                    axis=axis,
                    pan_clockwise=pan_cw if pan_cw is not None else True,
                    tilt_clockwise=tilt_cw if tilt_cw is not None else True,
                )
            time.sleep(0.2)

    # Start loop in background thread
    thread = threading.Thread(target=loop_motion, daemon=True)
    thread.start()

    # ---- Button callbacks ----
    def move_up(event):
        current_direction.update({"axis": "Y", "tilt_cw": True, "pan_cw": None})

    def move_down(event):
        current_direction.update({"axis": "Y", "tilt_cw": False, "pan_cw": None})

    def move_left(event):
        current_direction.update({"axis": "X", "pan_cw": False, "tilt_cw": None})

    def move_right(event):
        current_direction.update({"axis": "X", "pan_cw": True, "tilt_cw": None})

    def increase_speed(event):
        nonlocal speed
        speed = min(speed + 1, max_speed)
        text_speed.set_text(f"Speed: {speed}")
        plt.draw()

    def decrease_speed(event):
        nonlocal speed
        speed = max(speed - 1, min_speed)
        text_speed.set_text(f"Speed: {speed}")
        plt.draw()

    def stop(event):
        current_direction.update({"axis": None, "pan_cw": None, "tilt_cw": None})
        PTZController(ptz_name).stop_continuous()

    def quit_app(event):
        nonlocal running
        running = False
        PTZController(ptz_name).stop_continuous()
        plt.close("all")

    # ---- Matplotlib GUI ----
    fig, ax = plt.subplots(figsize=(5, 5))
    plt.subplots_adjust(bottom=0.3)
    ax.axis("off")

    # Speed text
    text_speed = ax.text(
        0.5, 0.95, f"Speed: {speed}", ha="center", va="center", fontsize=14
    )

    # Azimuth text
    azimuth_text = ax.text(
        0.5, 0.9, f"Azimuth: Unknown", ha="center", va="center", fontsize=14
    )
    # Bottom text
    ax.text(
        0.5,
        -0.1,  # X=0.5 (center), Y=0.02 (near bottom)
        text_bottom,  # Initial message
        ha="center",
        va="center",
        fontsize=8,
    )

    # Button positions
    btn_positions = {
        "up": [0.4, 0.65, 0.2, 0.1],
        "down": [0.4, 0.35, 0.2, 0.1],
        "left": [0.2, 0.5, 0.2, 0.1],
        "right": [0.6, 0.5, 0.2, 0.1],
        "stop": [0.4, 0.5, 0.2, 0.1],
        "plus": [0.75, 0.1, 0.1, 0.1],
        "minus": [0.15, 0.1, 0.1, 0.1],
        "quit": [0.45, 0.1, 0.1, 0.1],
    }

    # Create buttons with proper labels
    buttons = {
        "up": Button(plt.axes(btn_positions["up"]), "↑"),
        "down": Button(plt.axes(btn_positions["down"]), "↓"),
        "left": Button(plt.axes(btn_positions["left"]), "←"),
        "right": Button(plt.axes(btn_positions["right"]), "→"),
        "stop": Button(plt.axes(btn_positions["stop"]), "STOP"),
        "plus": Button(plt.axes(btn_positions["plus"]), "+"),
        "minus": Button(plt.axes(btn_positions["minus"]), "−"),
        "quit": Button(plt.axes(btn_positions["quit"]), "Quit"),
    }

    def on_press(event: Any):
        if event.inaxes == buttons["up"].ax:
            move_up(event)
        elif event.inaxes == buttons["down"].ax:
            move_down(event)
        elif event.inaxes == buttons["left"].ax:
            move_left(event)
        elif event.inaxes == buttons["right"].ax:
            move_right(event)

    def on_release(event: Any):
        if event.inaxes in [
            buttons["up"].ax,
            buttons["down"].ax,
            buttons["left"].ax,
            buttons["right"].ax,
        ]:
            stop(event)
            azi = PTZController(ptz_name).get_azimuth()
            azimuth_text.set_text(f"Azimuth: {azi}")
            plt.draw()

    # Connect actions
    buttons["minus"].on_clicked(decrease_speed)
    buttons["plus"].on_clicked(increase_speed)
    buttons["quit"].on_clicked(quit_app)
    buttons["stop"].on_clicked(stop)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("button_release_event", on_release)

    plt.show()

    # Cleanup after closing GUI
    running = False
    PTZController(ptz_name).stop_continuous()
