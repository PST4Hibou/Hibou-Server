from abc import ABC, abstractmethod

class BaseIPC(ABC):
    def lifespan(self):
        """
        Function to start the IPC handler if needed for setup or processing.
        For Zeromq, this will start the proxy in a separate thread, so it must be called once at initialization.
        """
        raise NotImplementedError

    @abstractmethod
    def publish(self, topic: str, message: str) -> None:
        """Send a message to the IPC topic."""
        pass

    @abstractmethod
    def subscribe(self, topic_filter: str, callback: callable) -> str:
        """Subscribe to messages from the IPC topic"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the IPC channel."""
        pass

def get_ipc_handler() -> BaseIPC:
    """
    Factory function to create an IPC handler instance.
    Can be extended to support multiple IPC implementations based on configuration.
    """
    from src.helpers.ipc.zmqhandler import ZmqHandler
    return ZmqHandler()