import socket
import logging
from typing import Sequence

from typing_extensions import overload


class YamahaRemoteControl:
    """
    This class implements the Yamaha Remote Control protocol.
    """

    def __init__(self, ip: str, port: int, device_id: int = 0):
        self.ip = ip
        self.port = port
        self.device_id = device_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip, self.port))
        logging.info("Yamaha Remote Control connected")

    def send_command(self, command: str) -> str | None:
        """
        Send a command to the Yamaha Remote Control protocol.
        Args:
            command: The command to send.

        Returns: result

        """
        # Add the required patterns for YRC
        command = " " + command + "\n"
        try:
            self.socket.send(command.encode())
            if result := self.socket.recv(1024):
                return result.decode()

        except Exception as e:
            logging.error(
                f"[yamaha_remote_control] Error sending command: {command}, error: {e}"
            )

    @overload
    def set_phantom_power(
        self, channels: Sequence[int], state: Sequence[int]
    ) -> None: ...

    @overload
    def set_phantom_power(self, channels: int, state: int) -> None: ...

    def set_phantom_power(self, channels, state):
        """
        Used to set the phantom power of a Yamaha device.
        Args:
            channels: List or Index of channel.s
            state: List or value of state.s

        Returns:
        """
        if isinstance(channels, int):
            channels = [channels]
            state = [state]

        for channel in zip(channels, state):
            command = f"set IO:Current/InCh/48VOn {channel} {self.device_id} {state}"
            self.send_command(command)
