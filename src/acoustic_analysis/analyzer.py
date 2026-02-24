from src.acoustic_analysis.data import AudioBuffer, InferenceResult, MicInfo
from abc import ABC, abstractmethod


class AudioAnalyzer(ABC):
    """
    Abstract base class for analyzing audio data to determine the angle of arrival (AoA) of a drone.

    Subclasses must implement audio buffer processing, inference integration, and angle computation.
    """

    def __init__(self, sample_rate: int, mic_infos: list[MicInfo]):
        self.sample_rate = sample_rate
        self.mic_infos = mic_infos

    @abstractmethod
    def push_buffer(self, buffer: AudioBuffer):
        """
        Add audio buffer data to the analyzer for processing.

        Args:
            buffer: Audio data buffer to be analyzed.
        """
        pass

    @abstractmethod
    def push_inference(self, inference: InferenceResult):
        """
        Add inference result to the analyzer for angle computation.

        Args:
            inference: Result of an inference on drone presence for a certain channel.
        """
        pass

    @abstractmethod
    def get_angle(self) -> float:
        """
        Compute and return the angle of arrival of the drone.

        Returns:
            Angle of arrival in degrees, between 0 and 360.
        """
        pass
