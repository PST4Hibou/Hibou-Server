import abc
from abc import abstractmethod


class BaseTracker(abc.ABC):
    """
    Abstract base class for all tracking algorithm implementations.

    Define the interface and common utilities expected from tracking algorithm implementations.
    Concrete tracker classes (e.g., PID, ...) must inherit from this class
    and implement the abstract methods.
    """

    @abstractmethod
    def update(self, results) -> tuple[float, float] | None:
        """Update the tracker state based on new detection results."""
        pass
