from collections import deque

from src.arguments import args
from src.modules.audio.detection.ai import ModelProxy
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

    def process(self, audio_samples: list[GstChannel]):
        self.audio_queue.append(audio_samples)

        if SETTINGS.AUDIO_PLAYBACK:  # Only for debug purposes
            play_sample(audio_samples[0], 0)

        res, prb = self.model.infer(audio_samples)
        self.predictions_queue.append(res)
        self.probabilities_queue.append(prb)

        if any(res):
            print("Drone")
        else:
            print("Other")
