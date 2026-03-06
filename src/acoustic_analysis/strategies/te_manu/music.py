from src.acoustic_analysis.strategies.te_manu.storage import History, Options, Data
from scipy import signal as sig

import pyroomacoustics as pra
import numpy as np


def compute_stft(signal, nfft, hop, fs):
    # Compute STFT for channel
    f, t, Zxx = sig.stft(
        signal,
        fs=fs,  # We only need the STFT, not actual frequencies
        nperseg=nfft,
        noverlap=nfft - hop,
        return_onesided=True,
    )

    return Zxx


def last_azimuths(data: Data, history: History):
    n_detected = np.sum(
        [history.prediction_history[i][-1] for i in range(history.channels)]
    )
    if n_detected == 0:
        return np.array([])

    X = np.array([history.stft_history[i][-1] for i in range(history.channels)])

    mid_frame = X.shape[2] // 2
    frame_start = max(0, mid_frame - Options.FRAME_WINDOW // 2)
    frame_end = min(X.shape[2], mid_frame + Options.FRAME_WINDOW // 2)

    doa = pra.doa.NormMUSIC(
        data.mic_pos,
        data.sample_rate,
        Options.NFFT,
        n_src=n_detected,
        num_iter=5,
    )

    # Keep 3D shape: (n_mics, n_freq, n_snapshots)
    doa.locate_sources(X[:, :, frame_start:frame_end])

    return np.rad2deg(doa.azimuth_recon)  # Convert to degrees
