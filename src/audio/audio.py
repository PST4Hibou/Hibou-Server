from abc import ABC, abstractmethod
from threading import Thread
from typing import Callable, override
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class SourceInterface(ABC):
    """
    Abstract base class representing any audio source.

    This interface defines the required methods for any audio source,
    such as a file, GStreamer pipeline, or microphone, allowing the
    application to receive channel-aligned audio frames via a callback.
    """

    def __init__(self):
        """
        Initialize the source interface.

        The `_callback` attribute stores a function that will be called
        whenever new audio data is available.
        """
        self._callback: Callable[[list], None] | None = None

    def set_callback(self, callback: Callable[[list], None]):
        """
        Register a callback to receive audio frames.

        Args:
            callback (Callable[[list], None]): A function that accepts a list
                of channel-aligned audio frames. This function will be called
                whenever new audio data is available.
        """
        self._callback = callback

    @abstractmethod
    def start(self):
        """
        Start producing audio data.

        Subclasses must implement this method to begin streaming or generating
        audio frames. Audio data should be delivered by calling `_emit(data)`.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop producing audio data and release any resources.

        Subclasses must implement this method to cleanly stop the audio source,
        ensuring that no further callbacks are invoked.
        """
        pass

    def _emit(self, data: list):
        """
        Deliver audio data to the registered callback.

        This helper should be used by subclasses to send new audio frames
        to the consumer.

        Args:
            data (list): A list of channel-aligned audio frames.
        """
        if self._callback is not None:
            self._callback(data)


class Source(SourceInterface):
    """
    Threaded implementation base class for continuous audio sources.

    Provides a background thread mechanism to poll or generate audio frames
    in a loop, delivering them through the `_callback` mechanism.
    """

    def __init__(self):
        """
        Initialize the threaded source.

        Sets up the internal thread and control flag for starting and stopping
        the background processing loop.
        """
        super().__init__()

        self._thread = Thread(target=self._run, args=())
        self._continue = False

    @override
    def start(self):
        """
        Start the audio source background thread.

        Launches the internal thread that runs `_run` in a loop. Subsequent
        calls have no effect if the thread is already running.
        """
        if self._continue:
            return

        self._continue = True
        self._thread.start()

    @abstractmethod
    def _run(self):
        """
        Background thread loop to continuously produce or poll audio frames.

        Subclasses must implement this method to:
            - Continuously generate or retrieve audio frames.
            - Call `self._emit(data)` whenever new frames are ready.

        This method runs in a separate thread when `start()` is called.
        """
        pass

    @override
    def stop(self):
        """
        Stop the background audio thread.
        """
        self._continue = False
        self._thread.join()
