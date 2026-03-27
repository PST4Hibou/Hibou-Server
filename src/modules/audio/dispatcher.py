from collections import deque

import numpy as np

from src.arguments import args
from src.helpers.ipc import base_ipc
from src.modules.audio.detection.ai import ModelProxy
from src.modules.audio.localization.data import AudioBuffer, InferenceResult
from src.modules.audio.localization.strategies.gcc_phat.strategy import Analyzer
from src.modules.audio.streaming import GstChannel
from src.modules.audio.streaming.play import play_sample
from src.settings import SETTINGS


class AudioDispatcher:
    """
    Class responsible for dispatching audio data to the appropriate processing modules, such as inference and localization.
    """

    def __init__(self):
        self.audio_queue = deque(maxlen=20)
        # True or False
        self.predictions_queue = deque(maxlen=20)
        # Confidence of the prediction, between 0 and 1
        self.probabilities_queue = deque(maxlen=20)
        self.model = ModelProxy(args.audio_model)

        self.analyzer = Analyzer(SETTINGS.AUDIO_REC_HZ)

    def process(self, audio_samples: list[GstChannel]):
        self.audio_queue.append(audio_samples)

        if SETTINGS.AUDIO_PLAYBACK:  # Only for debug purposes
            play_sample(audio_samples[0], 0)

        res, prb = self.model.infer(audio_samples)
        self.predictions_queue.append(res)
        self.probabilities_queue.append(prb)

        # print(res)
        # print(prb)
        # if any(res):
        #     print("Drone")
        # else:
        #     print("Other")
        base_ipc.get_ipc_handler().publish(SETTINGS.IPC_ACOUSTIC_DETECTION_TOPIC, "drone" if any(res) else "other")

        i = 0
        for audio, pts in audio_samples:
            self.analyzer.push_buffer(
                AudioBuffer(timestamp=pts, channel=i, data=np.array(audio))
            )
            i += 1
        i = 0
        for pred in res:
            self.analyzer.push_inference(
                InferenceResult(
                    timestamp=audio_samples[i][1], channel=i, confidence=0, drone=pred
                )
            )
            i += 1

        self.analyzer.get_angle()

    def get_last_channels(self) -> list[GstChannel] | None:
        try:
            return self.audio_queue.pop()
        except IndexError:
            return None

    def is_empty(self) -> bool:
        return len(self.audio_queue) == 0
