from pyroomacoustics.experimental import tdoa

from src.modules.audio.localization.analyzer import AudioAnalyzer
from src.modules.audio.localization.data import AudioBuffer, InferenceResult, MicInfo
from typing import override

import numpy as np
import math

num_mics = 3
angles = [30, 60, 90]

SPEED_OF_SOUND = 343.0
# TODO: use micro positioning
DEFAULT_MIC_SPACING = 0.5


class Analyzer(AudioAnalyzer):
    def __init__(self, sample_rate: int):
        super().__init__(sample_rate)

        self.audio_buffers = {}
        self.inference_results = {}
        self.mic_spacing = self._compute_mic_spacing()
        # self.array_orientation = np.mean([m.orientation for m in mic_infos])

    def _compute_mic_spacing(self) -> float:
        return DEFAULT_MIC_SPACING
        # m0, m1 = mic_infos[0], mic_infos[1]
        # if (
        #     m0.xpos is not None
        #     and m0.ypos is not None
        #     and m1.xpos is not None
        #     and m1.ypos is not None
        # ):
        #     return math.hypot(m1.xpos - m0.xpos, m1.ypos - m0.ypos)
        # return DEFAULT_MIC_SPACING

    @override
    def push_buffer(self, buffer: AudioBuffer):
        if buffer.channel > num_mics - 1:
            return
        self.audio_buffers[buffer.channel] = buffer.data

    @override
    def push_inference(self, inference: InferenceResult):
        if inference.channel > num_mics - 1:
            return
        self.inference_results[inference.channel] = inference.drone

    @staticmethod
    def compute_tdoa_vector(
        signals: list[np.ndarray], interp: int, fs: int
    ) -> np.ndarray:
        """
        Compute TDOA of each mic relative to mic 0 for a given chunk
        0 Is the reference
        """
        n_mics = len(signals)
        tdoas = np.zeros(n_mics)
        ref_sig = signals[0]
        for j in range(1, n_mics):
            tdoas[j] = tdoa(
                ref_sig,
                signals[j],
                interp=interp,
                fs=fs,
                phat=True,
            )
        return tdoas

    def _tdoa_to_angle(self, tau: float) -> float:
        """
        Convert TDOA (seconds) to angle from array normal.
        sin(θ) = (c * τ) / d  =>  θ = arcsin(clamp((c*τ)/d, -1, 1))
        Returns angle in degrees.
        """
        arg = (SPEED_OF_SOUND * tau) / self.mic_spacing
        arg = np.clip(arg, -1.0, 1.0)
        theta_rad = math.asin(arg)
        return math.degrees(theta_rad)

    @override
    def get_angle(self) -> float | None:
        if len(self.audio_buffers) != num_mics:
            raise ValueError("Not enough audio")

        # print()
        # Skip when no drone is detected
        # TODO:
        if not any(self.inference_results[i] for i in range(num_mics)):
            # print("No drone detected")
            return None

        signals = [self.audio_buffers[i] for i in range(num_mics)]
        tdoas = self.compute_tdoa_vector(signals, interp=1, fs=self.sample_rate)
        # print(tdoas)
        # use TDOA of mic 1 relative to mic 0
        tau = tdoas[1]
        theta = self._tdoa_to_angle(tau)
        # print(theta)

        # map to global azimuth (0–360°): array orientation + angle from normal
        # azimuth = (self.array_orientation + theta) % 360
        return theta
