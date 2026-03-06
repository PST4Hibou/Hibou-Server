from src.acoustic_analysis.strategies.te_manu.storage import History
from collections import deque

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


class HistoryVisualizer:
    def __init__(self, history: History, figsize: tuple = (14, 12)):
        plt.ion()

        self.history = history
        self.fig, self.axes = plt.subplots(4, 1, figsize=figsize)
        self.fig.tight_layout(pad=3.0)

        # Initialize line objects for each plot
        # Angles: one line per channel
        self.angles_lines = []
        for i in range(history.channels):
            (line,) = self.axes[0].plot(
                [],
                [],
                label=f"Channel {i}",
                marker="o",
                markersize=3,
                linestyle="-",
                alpha=0.7,
            )
            self.angles_lines.append(line)

        # Output: one line per channel
        self.output_lines = []
        for i in range(history.channels):
            (line,) = self.axes[1].plot(
                [],
                [],
                label=f"Channel {i}",
                marker="o",
                markersize=3,
                linestyle="-",
                alpha=0.7,
            )
            self.output_lines.append(line)

        # Recent speeds: single line
        (self.speeds_line,) = self.axes[2].plot(
            [], [], label="Angular Speed", color="purple", linewidth=2
        )

        # Prediction: one line per channel (boolean values)
        self.prediction_lines = []
        for i in range(history.channels):
            (line,) = self.axes[3].plot(
                [],
                [],
                label=f"Channel {i}",
                marker="s",
                markersize=4,
                linestyle="-",
                alpha=0.7,
            )
            self.prediction_lines.append(line)

        # Configure subplots
        self._configure_subplots()

    def _configure_subplots(self):
        """Configure the appearance of each subplot."""
        # Angles subplot
        self.axes[0].set_title("Angles History (with NaN values)")
        self.axes[0].set_ylabel("Angle (degrees)")
        self.axes[0].legend(loc="upper right", fontsize="small")
        self.axes[0].grid(True, alpha=0.3)

        # Output subplot
        self.axes[1].set_title("Output History")
        self.axes[1].set_ylabel("Output Value")
        self.axes[1].legend(loc="upper right", fontsize="small")
        self.axes[1].grid(True, alpha=0.3)

        # Recent speeds subplot
        self.axes[2].set_title("Recent Angular Speeds")
        self.axes[2].set_ylabel("Speed (degrees/second)")
        self.axes[2].legend(loc="upper right", fontsize="small")
        self.axes[2].grid(True, alpha=0.3)

        # Prediction subplot
        self.axes[3].set_title("Prediction History")
        self.axes[3].set_ylabel("Prediction (Boolean)")
        self.axes[3].set_xlabel("Sample Index")
        self.axes[3].legend(loc="upper right", fontsize="small")
        self.axes[3].grid(True, alpha=0.3)
        self.axes[3].set_ylim(-0.1, 1.1)  # Boolean values: 0 or 1

    def _series_from_history(self, history, channel_index: int):
        """Return a per-channel series for either list-of-samples or list-of-series layouts."""
        if not history:
            return []

        first = history[0]

        # Scalar series: history is a list/deque of floats for a single channel
        if np.isscalar(first):
            return list(history)

        # List-of-samples: each item is a list/tuple/ndarray of channel values
        if isinstance(first, (list, tuple, np.ndarray)):
            series = []
            for item in history:
                if (
                    isinstance(item, (list, tuple, np.ndarray))
                    and len(item) > channel_index
                ):
                    series.append(item[channel_index])
                else:
                    series.append(np.nan)
            return series

        # List-of-series: history[channel] is a deque/list of values
        if channel_index < len(history):
            value = history[channel_index]
            if np.isscalar(value):
                return [value]
            return list(value)

        return []

    def update(self):
        """Update the displayed data from the History instance."""
        # Angles history
        for i in range(self.history.channels):
            angles = self._series_from_history(self.history.angles_history, i)
            if angles:
                x_data = list(range(len(angles)))
                self.angles_lines[i].set_data(x_data, angles)

        # Output history
        for i in range(self.history.channels):
            output = self._series_from_history(self.history.output_history, i)
            if output:
                x_data = list(range(len(output)))
                self.output_lines[i].set_data(x_data, output)

        # Recent speeds
        speeds = list(self.history.recent_speeds)
        if speeds:
            x_data = list(range(len(speeds)))
            self.speeds_line.set_data(x_data, speeds)

        # Prediction history
        for i in range(self.history.channels):
            predictions = self._series_from_history(self.history.prediction_history, i)
            if predictions:
                x_data = list(range(len(predictions)))
                self.prediction_lines[i].set_data(x_data, predictions)

        # Auto-scale axes to fit data
        self._autoscale_axes()

        # Force redraw without blocking
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

    def _autoscale_axes(self):
        """Auto-scale all axes to fit the data."""
        for ax in self.axes:
            ax.relim()
            ax.autoscale_view()

    def show(self):
        """Display the visualization."""
        plt.show(block=False)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


class AngleVisualizer:
    def __init__(self, history: History):
        self.history = history

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        self._setup_plot()

    def _setup_plot(self):
        self.ax.set_theta_zero_location("N")  # 0° at top
        self.ax.set_theta_direction(-1)  # clockwise
        self.ax.set_ylim(0, 1)
        self.ax.set_yticks([])
        self.ax.set_title("Angle History", va="bottom", fontsize=14)
        self.cmap = plt.cm.plasma

    def _is_valid(self, value):
        try:
            return value is not None and not np.isnan(value)
        except (TypeError, ValueError):
            return False

    def _draw_lines(self):
        self.ax.cla()
        self._setup_plot()

        angles = [a for a in self.history.output_history]
        n = len(angles)

        if n == 0:
            return

        # Draw main angles as solid lines
        for i, angle in enumerate(angles):
            if not self._is_valid(angle):
                continue
            alpha = 0.2 + 0.6 * (i + 1) / n
            color = self.cmap(i / max(n - 1, 1))
            angle_rad = np.deg2rad(angle)
            self.ax.plot(
                [angle_rad, angle_rad],
                [0, 1],
                color=color,
                alpha=alpha,
                linewidth=1.5,
            )

        # Highlight most recent valid angle in red
        recent_valid = [(i, a) for i, a in enumerate(angles) if self._is_valid(a)]
        if recent_valid:
            _, latest = recent_valid[-1]
            latest_rad = np.deg2rad(latest)
            self.ax.plot(
                [latest_rad, latest_rad],
                [0, 1],
                color="red",
                linewidth=2.5,
                label=f"Latest: {latest:.1f}°",
            )
            self.ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    def show(self):
        self._draw_lines()
        self.fig.show()

    def update(self):
        self._draw_lines()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
