import numpy as np


class AngleOfArrivalEstimator:
    def __init__(self, nb_channels, angle_coverage=360, smoothing=0.8):
        self.nb_channels = nb_channels
        self.angle_coverage = angle_coverage
        self.smoothing = smoothing
        self.theta_smooth = None  # last smoothed angle

    def estimate(self, energies):
        energies = np.array(energies, dtype=float)
        if np.sum(energies) < 1e-8:
            return self.theta_smooth  # keep previous if silent

        # Normalize
        weights = energies / np.sum(energies)

        # Channel angles
        angles_deg = np.linspace(
            0, self.angle_coverage, self.nb_channels, endpoint=False
        )
        angles_rad = np.deg2rad(angles_deg)

        # Weighted vector sum
        X = np.sum(weights * np.cos(angles_rad))
        Y = np.sum(weights * np.sin(angles_rad))
        theta_est = np.rad2deg(np.arctan2(Y, X)) % 360

        # Temporal smoothing
        if self.theta_smooth is None:
            self.theta_smooth = theta_est
        else:
            d = (
                (theta_est - self.theta_smooth + 540) % 360
            ) - 180  # shortest angular diff
            self.theta_smooth = (self.theta_smooth + self.smoothing * d) % 360

        return self.theta_smooth
