from abc import ABC, abstractmethod
from typing import Callable

class BaseAudioSource(ABC):
    """
    Abstract interface for any audio source (file, GStreamer, microphone, etc.).
    """

    def __init__(self):
        self._callback: Callable[[list], None] | None = None

    def set_callback(self, callback: Callable[[list], None]):
        """
        Set the callback to be invoked when new audio data is ready.

        Args:
            callback (Callable[[list], None]):
                Function that receives a list of channel-aligned audio frames.
        """
        self._callback = callback

    @abstractmethod
    def start(self):
        """
        Start producing audio data.
        Should eventually call `self._callback(data)` whenever a frame is ready.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop producing audio data and release resources.
        """
        pass

    def _emit(self, data: list):
        """
        Helper for subclasses to deliver data to the registered callback.
        """
        if self._callback is not None:
            self._callback(data)
