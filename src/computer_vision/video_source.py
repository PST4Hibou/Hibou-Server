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
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stop the video stream."""
        raise NotImplementedError

    @abstractmethod
    def get_fps(self) -> float:
        """Get the **frames per second** (FPS) of the video stream."""
        raise NotImplementedError

    @abstractmethod
    def get_frame(self) -> tuple[bool, any]:
        """Retrieve the next frame from the video stream."""
        raise NotImplementedError

    @abstractmethod
    def is_opened(self) -> bool:
        """Check if the video stream is opened."""
        raise NotImplementedError
