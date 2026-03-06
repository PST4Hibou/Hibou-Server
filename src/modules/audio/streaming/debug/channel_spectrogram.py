import matplotlib.pyplot as plt

import numpy as np
import librosa


class ChannelTimeSpectrogram:
    def __init__(self, num_mics=8, frame_duration_s=0.5, history_length=200):
        self.num_mics = num_mics
        self.history_length = history_length
        self.frame_duration_s = frame_duration_s

        # Matrix of energy history: rows = time, cols = channels
        self.data = np.zeros((history_length, num_mics))

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(8, 6))

        # Create the initial heatmap
        self.im = self.ax.imshow(
            self.data,
            origin="lower",  # time increasing upward
            aspect="auto",
            cmap="inferno",  # or "hot", "viridis"
            interpolation="nearest",
        )

        self.cbar = self.fig.colorbar(self.im, ax=self.ax)
        self.cbar.set_label("Energy")

        self.ax.set_xlabel("Channel index")
        self.ax.set_ylabel("Time (frames)")
        self.ax.set_title("Channel-Time Energy Spectrogram")

        # X-axis:
        self.ax.set_xticks(np.arange(self.num_mics))
        self.ax.set_xticklabels([f"Ch {i}" for i in range(self.num_mics)])

        # Y-axis:
        self.ax.yaxis.set_visible(False)

        self.fig.tight_layout()
        self.fig.show()

    def update(self):
        self.fig.canvas.flush_events()

    def set_input(self, energies):
        """
        Insert the latest frame of energy values (1D array: num_channels)
        into the scrolling heatmap.
        """
        energies = np.array(energies, dtype=np.float32)  # ensure numpy array

        # # Optional: smooth across channels for soft peaks
        from scipy.ndimage import gaussian_filter1d

        #
        # smoothed = gaussian_filter1d(energies, sigma=1.0)

        # Roll the buffer up by 1 row
        self.data = np.roll(self.data, -1, axis=0)

        # Insert a new frame at the bottom
        self.data[-1, :] = energies

        self.data[-3:, :] = gaussian_filter1d(self.data[-3:, :], sigma=1.0, axis=0)

        # Update the heatmap
        self.im.set_data(self.data)

        # Optional: set color scale
        self.im.set_clim(0, 200)

        self.fig.canvas.draw()


def convert_to_linear_spectrogram(audios: list):
    return [np.array(librosa.amplitude_to_db(np.abs(librosa.stft(np.array(a, dtype=np.float32), n_fft=2048, hop_length=512)), ref=np.max), dtype=np.float32) for a in audios]

class StftSpectrogram:
    def __init__(self, num_mics=8, frame_duration_s=0.5):
        self.num_mics = num_mics

        self.data = np.zeros((1025 * num_mics, 12))
        print(self.data.shape)

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(8, 6))

        # Create the initial heatmap
        self.im = self.ax.imshow(
            self.data,
            origin="lower",  # time increasing upward
            aspect="auto",
            cmap="viridis",  # or "hot", "inferno"
            interpolation="nearest",
        )

        self.fig.tight_layout()
        self.fig.show()

    def update(self):
        self.fig.canvas.flush_events()

    def set_input(self, audios):
        data = np.stack(convert_to_linear_spectrogram(audios))
        self.data = data.reshape(data.shape[0] * data.shape[1], data.shape[2])

        # Update the heatmap
        self.im.set_data(self.data)
        self.im.set_clim(np.min(self.data), np.max(self.data))

        self.fig.canvas.draw()
