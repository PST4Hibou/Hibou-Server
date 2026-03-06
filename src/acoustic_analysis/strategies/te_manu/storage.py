from src.acoustic_analysis.data import MicInfo
from collections import deque

import pyroomacoustics as pra
import numpy as np


class Options:
    MIC_RADIUS = 0.2
    NFFT = 256  # 512  # FFT size
    HOP = NFFT // 2  # Hop length (50% overlap)
    FRAME_WINDOW = 10
    SPEED_OF_SOUND = 343.0
    TAU = 0.5  # Time constant for exponential smoothing in seconds
    TIME_SCALE = 1e9  # Because our TS units is ns.
    MAX_ANGULAR_SPEED = 500.0  # [TODO] Evaluate this value based on expected drone movement, specs, and field studies.
    MIN_ALLOWED_CHANGE = 0.5  # Minimum change in angle to consider it a valid movement, to filter out noise.
    MIN_ALLOWED_SPEED = 0.5  # Minimum angular speed (degrees per second) to consider for adaptive smoothing, to prevent over-smoothing when the drone is moving slowly.
    IS_CIRCLE = False
    SPLIT_LEVEL = 0.5
    OUTPUT = False  # False


class Data:
    def __init__(
        self,
        sample_rate: int,
        mic_infos: list[MicInfo],
        mic_pos: np.ndarray,
        room: pra.Room,
    ):
        self.channels = len(mic_infos)
        self.sample_rate = sample_rate
        self.mic_infos = mic_infos
        self.mic_pos = mic_pos
        self.room = room


class History:
    def __init__(self, channels: int, storage_limit: int = 20):
        self.angles_history = deque(maxlen=storage_limit)
        self.angles_src_history = deque(maxlen=storage_limit)
        self.output_history = deque(maxlen=storage_limit)
        self.time_history = deque(maxlen=storage_limit)
        self.bulk_tdoa_history = deque(maxlen=storage_limit)
        self.recent_speeds = deque(maxlen=min(max(storage_limit * 2, 100), 300))

        self.confidence_history = [
            deque(maxlen=storage_limit) for channels in range(channels)
        ]
        self.prediction_history = [
            deque(maxlen=storage_limit) for channels in range(channels)
        ]
        self.buffer_history = [
            deque(maxlen=storage_limit) for channels in range(channels)
        ]
        self.stft_history = [
            deque(maxlen=storage_limit) for channels in range(channels)
        ]

        self.storage_limit = storage_limit
        self.channels = channels
