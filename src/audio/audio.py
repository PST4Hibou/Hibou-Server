from abc import ABC, abstractmethod
from threading import Thread
from typing import Callable, override
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class SourceInterface(ABC):
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


class Source(SourceInterface):
    def __init__(self):
        super().__init__()

        self._thread = Thread(target=self._run, args=())
        self._continue = False

    @override
    def start(self):
        if self._continue:
            return

        self._continue = True
        self._thread.start()

    @abstractmethod
    def _run(self):
        """
        Background thread loop that continuously polls the data queue.
        Calls `on_data_ready` when new frames are available.
        """
        pass

    @override
    def stop(self):
        """
        Helper for subclasses to deliver data to the registered callback.
        """
        self._continue = False
        self._thread.join()
