import abc
from abc import abstractmethod


class VideoRecorder(abc.ABC):
    """
    Abstract base class for video recording implementations.

    Define the interface and common utilities expected from video recorder implementations.
    Concrete recorder classes (e.g., RtspStream, ...) must inherit from this class
    and implement the abstract methods.
    """

    @abstractmethod
    def start_recording(self) -> None:
        """Start the video recording process."""
        pass

    @abstractmethod
    def stop_recording(self) -> None:
        """Stop the video recording process."""
        pass
