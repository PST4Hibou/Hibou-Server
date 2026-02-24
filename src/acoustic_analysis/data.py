from dataclasses import dataclass
import numpy as np


@dataclass
class MicInfo:
    """
    A class to represent the information of a microphone.
    """

    channel: int
    angle: float
    orientation: float


@dataclass
class TimestampedData:
    """
    A class to represent a timestamped data point.
    """

    timestamp: int
    channel: int


@dataclass
class AudioBuffer(TimestampedData):
    """
    A class to represent an audio buffer, for ONLY ONE channel.
    """

    sample_rate: int
    data: np.ndarray


@dataclass
class InferenceResult(TimestampedData):
    """
    A class to represent the result of an inference on drone presence.
    """

    confidence: float
    drone: bool
