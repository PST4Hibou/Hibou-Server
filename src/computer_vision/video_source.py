import abc
from abc import abstractmethod


class VideoSource(abc.ABC):
    """
    Abstract base class for video source implementations.

    Define the interface and common utilities expected from video source implementations.
    Concrete source classes (e.g., RtspStream, ...) must inherit from this class
    and implement the abstract methods.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the video stream."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the video stream."""
        pass
