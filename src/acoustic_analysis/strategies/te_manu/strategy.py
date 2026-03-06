from src.acoustic_analysis.strategies.te_manu.music import compute_stft, last_azimuths
from src.acoustic_analysis.strategies.te_manu.display import (
    HistoryVisualizer,
    AngleVisualizer,
)
from src.acoustic_analysis.data import AudioBuffer, InferenceResult, MicInfo
from src.acoustic_analysis.strategies.te_manu.storage import History, Options, Data
from src.acoustic_analysis.strategies.te_manu.fusion import fuse
from src.acoustic_analysis.analyzer import AudioAnalyzer
from typing import override

import src.acoustic_analysis.strategies.te_manu.tdoa as tdoa
import pyroomacoustics.directivities as dr
import pyroomacoustics as pra
import numpy as np
import math


class Analyzer(AudioAnalyzer):
    def __init__(self, sample_rate: int, mic_infos: list[MicInfo]):
        super().__init__(sample_rate, mic_infos)

        self.mic_angles = np.array([mic.orientation for mic in mic_infos])
        if math.nan in self.mic_angles:
            raise ValueError(
                f"Invalid data has been provided as mic orientation:{mic_infos}"
            )

        directivities = []

        for mic in mic_infos:
            orientation = dr.DirectionVector(
                azimuth=mic.orientation,
                colatitude=np.pi / 2,  # horizontal
            )

            # [TODO] For now, we use hypercardioid, but we should consider using the actual directivity pattern of the mic if available.
            dir_obj = dr.HyperCardioid(orientation=orientation)

            directivities.append(dir_obj)

        mic_positions = np.array(
            [[mic.xpos for mic in mic_infos], [mic.ypos for mic in mic_infos]]
        )

        room = pra.AnechoicRoom(
            fs=sample_rate,
            temperature=20,
            dim=2,  # For now, our physical setup only corresponds to a 2D space.
        )
        room.add_microphone_array(
            pra.MicrophoneArray(mic_positions, sample_rate, directivity=directivities)
        )

        self.data = Data(
            sample_rate=sample_rate,
            mic_infos=mic_infos,
            mic_pos=mic_positions,
            room=room,
        )
        self.history = History(channels=len(mic_infos))
        # self.visualizer = HistoryVisualizer(self.history)
        self.visualizer = AngleVisualizer(self.history)

        self.visualizer.show()

    @override
    def push_buffer(self, buffer: AudioBuffer):
        self.history.buffer_history[buffer.channel].append(buffer.data)
        # Process the buffer and update the mels history
        self.history.stft_history[buffer.channel].append(
            compute_stft(
                buffer.data,
                nfft=Options.NFFT,
                hop=Options.HOP,
                fs=self.sample_rate,
            )
        )

    @override
    def push_inference(self, inference: InferenceResult):
        self.history.prediction_history[inference.channel].append(inference.drone)
        self.history.confidence_history[inference.channel].append(inference.confidence)

        if (
            len(self.history.time_history) == 0
            or self.history.time_history[-1] != inference.timestamp
        ):
            self.history.time_history.append(inference.timestamp)

    @override
    def get_angle(self) -> float | None:
        # Get indices of microphones that detected a drone
        detecting = [
            i
            for i in range(self.history.channels)
            if self.history.prediction_history[i][-1]
        ]

        # There's no need if it's just empty.
        if len(detecting) == 0:
            # Not enough detections – return last valid or NaN
            r = (
                self.history.angles_history[-1]
                if len(self.history.angles_history) > 0
                else math.nan
            )

            self.history.angles_history.append(math.nan)
            self.history.output_history.append(r)

            return r

        fused = math.nan
        if len(self.history.buffer_history[-1][0]) >= Options.SPLIT_LEVEL:
            count = int(1.0 / Options.SPLIT_LEVEL)
            elems_count = int(
                len(self.history.buffer_history[-1][0]) * Options.SPLIT_LEVEL
            )

            for i in range(count):
                signals = [
                    self.history.buffer_history[j][-1][
                        i * elems_count : (i + 1) * elems_count
                    ]
                    for j in range(self.history.channels)
                ]

                tdoa_matrix = tdoa.compute_vectors(
                    signals, interp=1, fs=self.sample_rate
                )
                self.history.bulk_tdoa_history.append(tdoa_matrix)

                # Optional: store tdoa_conf if you want to use it later
                # self.history.tdoa_confidence.append(tdoa_conf)

                fused = fuse(self.data, self.history)
                self.history.output_history.append(fused)

        self.visualizer.update()

        return fused

    """
    @override
    def get_angle(self) -> float | None:
        az = last_azimuths(self.data, self.history)

        # No azimuths do not forcibly mean that there's no drone, it may just be a temporary false negative.
        if len(az) == 0:
            r = (
                self.history.angles_history[-1]
                if len(self.history.angles_history) > 0
                else math.nan
            )

            self.history.angles_history.append(float(math.nan))
            self.history.output_history.append(float(r))

            return r

        # We always look at the smallest angle. There's no particular reason, just that we have to choose a source.
        angles = np.sort(az)
        self.history.angles_src_history.append(angles)
        print(angles)

        angle = angles[0]
        self.history.angles_history.append(float(angle))

        self.history.bulk_tdoa_history.append(
            tdoa.compute_vectors(
                [hist[-1] for hist in self.history.buffer_history],
                interp=1,
                fs=self.sample_rate,
            )
        )

        angle = fuse(self.data, self.history)
        self.history.output_history.append(float(angle))

        self.visualizer.update()

        return angle
    """
