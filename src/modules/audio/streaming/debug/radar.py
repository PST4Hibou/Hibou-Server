from matplotlib.projections.polar import PolarAxes
from matplotlib.colors import Normalize
from typing import cast

import matplotlib.pyplot as plt
import numpy as np


class RadarPlot:
    def __init__(self):
        self.max_distance = 10
        self.max_energy = 20
        self.fig = plt.figure()
        self.ax = cast(PolarAxes, self.fig.add_subplot(111, projection="polar"))
        self.ax.set_theta_zero_location("W")  # 0 degrees on the left
        self.ax.set_theta_direction(-1)  # clockwise
        self.ax.set_rmax(self.max_distance)
        self.ax.set_rticks(range(0, self.max_distance + 1, 2))
        self.ax.grid(True)

        # Initial single radar line
        angle = 0
        (self.line,) = self.ax.plot(
            [0, np.deg2rad(angle)], [0, self.max_distance], color="green", linewidth=2
        )

        # Colormap
        self.cmap = plt.get_cmap("RdYlGn_r")  # red=high, green=low
        self.norm = Normalize(vmin=0, vmax=self.max_energy)

        # --- Angle text label ---
        # Placed outside the polar plot (figure-relative coordinates)
        self.text_angle = self.fig.text(
            0.02, 0.95, "Angle: 0°", fontsize=15, color="black", backgroundcolor="white"
        )

        plt.ion()
        plt.show(block=False)

    def update(self):
        self.fig.canvas.flush_events()

    def set_input(self, angle, energy):
        """
        angle: single angle in degrees
        energy: single energy value
        """
        self.line.set_data([0, np.deg2rad(angle)], [0, self.max_distance])

        # Map energy to color
        color = self.cmap(self.norm(energy))
        self.line.set_color(color)

        # Update angle display
        self.text_angle.set_text(f"Angle: {angle:.1f}°")

        self.fig.canvas.draw()
