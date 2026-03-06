from src.acoustic_analysis.strategies.te_manu.storage import Options
from pyroomacoustics.experimental import tdoa

import numpy as np
import math


def compute_vectors(signals: list[np.ndarray], interp: int, fs: int) -> np.ndarray:
    """
    Compute TDOA of each mic relative to mic 0 for a given chunk
    0 Is the reference
    """
    n_mics = len(signals)
    tdoas = np.zeros((n_mics, n_mics))

    for j in range(0, n_mics):
        ref_sig = signals[j]
        for k in range(0, n_mics):
            tdoas[j][k] = tdoa(
                ref_sig,
                signals[k],
                interp=interp,
                fs=fs,
                phat=True,
            )

    return tdoas


def to_angle(mic_spacing: float, tau: float) -> float:
    """
    Convert TDOA (seconds) to angle from array normal.
    sin(θ) = (c * τ) / d  =>  θ = arcsin(clamp((c*τ)/d, -1, 1))
    Returns angle in degrees.
    """
    arg = (Options.SPEED_OF_SOUND * tau) / mic_spacing
    arg = np.clip(arg, -1.0, 1.0)
    theta_rad = math.asin(arg)
    return math.degrees(theta_rad)


def tdoa_to_angle(tau: float, pos1: np.ndarray, pos2: np.ndarray) -> float:
    """
    Convert TDOA (seconds) to angle of arrival (degrees) for a given microphone pair.
    Assumes far‑field and source in the horizontal plane.

    Parameters:
        tau : TDOA in seconds (positive means sound arrives at pos2 first)
        pos1, pos2 : (x, y) positions of the two microphones (in metres)

    Returns:
        angle in degrees [0, 360) measured from the positive x‑axis.
    """
    # Vector from mic1 to mic2
    d_vec = pos2 - pos1
    d = np.linalg.norm(d_vec)
    if d == 0:
        return np.nan

    # Baseline angle (direction from mic1 to mic2)
    baseline_angle = np.arctan2(d_vec[1], d_vec[0])

    # Projection of source direction onto baseline
    arg = (Options.SPEED_OF_SOUND * tau) / d
    arg = np.clip(arg, -1.0, 1.0)
    theta = np.arccos(arg)  # angle from baseline (0 to π)

    # Determine which side of the baseline the source lies on
    # tau > 0 → source is on the side of mic2
    if tau > 0:
        source_angle = baseline_angle + theta
    else:
        source_angle = baseline_angle - theta

    # Normalise to [0, 2π)
    source_angle = source_angle % (2 * np.pi)
    return np.degrees(source_angle)


def angle_from_matrix(
    tdoa_matrix: np.ndarray, mic_positions: np.ndarray, detecting_indices: list[int]
) -> tuple[float, float]:
    """
    Compute a single angle from the TDOA matrix using all pairs of detecting microphones.

    Args:
        tdoa_matrix : (n_mics, n_mics) matrix of TDOA values (seconds)
        mic_positions : (3, n_mics) array of microphone coordinates (x, y, z)
        detecting_indices : list of indices where the microphone detected the drone

    Returns:
        (angle_deg, confidence) where confidence is the fraction of used pairs
        (or 0 if fewer than 2 detections).
    """
    n_detect = len(detecting_indices)
    if n_detect < 2:
        return np.nan, 0.0

    angles = []
    weights = []  # could be based on pair quality (e.g., inverse variance)

    for i in range(n_detect):
        for j in range(i + 1, n_detect):
            idx1 = detecting_indices[i]
            idx2 = detecting_indices[j]
            tau = tdoa_matrix[idx1, idx2]  # TDOA from mic1 to mic2

            pos1 = mic_positions[:2, idx1]
            pos2 = mic_positions[:2, idx2]

            angle = tdoa_to_angle(tau, pos1, pos2)
            if not np.isnan(angle):
                angles.append(angle)
                weights.append(1.0)  # or use a quality metric

    if not angles:
        return np.nan, 0.0

    # Circular weighted mean
    sin_sum = sum(w * np.sin(np.radians(a)) for w, a in zip(weights, angles))
    cos_sum = sum(w * np.cos(np.radians(a)) for w, a in zip(weights, angles))
    mean_angle = np.degrees(np.arctan2(sin_sum, cos_sum)) % 360

    # Confidence: fraction of possible pairs actually used
    max_pairs = n_detect * (n_detect - 1) / 2
    conf = len(angles) / max_pairs

    return mean_angle, conf
