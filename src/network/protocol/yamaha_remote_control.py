import socket
import logging
import time

from typing import Sequence
from typing_extensions import overload
from src.network.protocol.yamaha.descriptions import YSDPPacket
from src.network.protocol.yamaha.discovery import YamahaDiscoverer


# For documentation regarding the protocol, please refer to:
# https://ca.yamaha.com/download/files/2323669


class YamahaRemoteControl:
    """
    Yamaha Remote Control protocol implementation class.
    """

    def __init__(self, ip: str, port: int = 49280, device_id: int = 0):
        self.ip = ip
        self.port = port
        self.device_id = device_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip, self.port))

        logging.info(f"Waiting for {self.device_id} to be ready.")

        # Wait for the device to be in normal mode.
        mode = "invalid"
        exe_status = "0"
        sys_status = "0"
        sync_status = "0"
        muted_status = "0"

        # Spec says to wait at least 1 sec between every request, but truth be told,
        # even Yamaha (R Remote) does not follow it, so we use a smaller cool down.

        # Wait for the device to be ready to receive messages.
        while mode != "normal":
            time.sleep(0.05)
            result = self.send_command("devstatus runmode")
            if not result:
                logging.warning(
                    "Yamaha Remote Control did not receive a response, retrying..."
                )
                continue

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result}, retrying..."
                )
            elif result.startswith("OK devstatus runmode "):
                mode = result[len("OK devstatus runmode") :].strip().strip('"')
                if mode == "emergency":
                    logging.error(
                        f"[yamaha_remote_control] Received Device in EMERGENCY mode ({self.device_id}), retrying...)"
                    )
                elif mode == "update":
                    logging.info(
                        f"Yamaha Remote Control received Device in UPDATE mode ({self.device_id}), retrying...)"
                    )

        while exe_status != "1":
            time.sleep(0.05)
            result = self.send_command("get IO:Current/Dev/ExecMode 0 0")

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result[:-1]}, retrying..."
                )
            elif result.startswith("OK get IO:Current/Dev/ExecMode 0 0 "):
                exe_status = result[len("OK get IO:Current/Dev/ExecMode 0 0") :].strip()

        while sys_status != "2":
            time.sleep(0.05)
            result = self.send_command("get IO:Current/Dev/SystemStatus 0 0")

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result[:-1]}, retrying..."
                )
            elif result.startswith("OK get IO:Current/Dev/SystemStatus 0 0 "):
                sys_status = result[
                    len("OK get IO:Current/Dev/SystemStatus 0 0") :
                ].strip()

        # The sync state should be at 2 or 5 here.
        while sync_status != "2" and sync_status != "5":
            time.sleep(0.05)
            result = self.send_command("get IO:Current/Dev/SyncStatus 0 0")

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result[:-1]}, retrying..."
                )
            elif result.startswith("OK get IO:Current/Dev/SyncStatus 0 0 "):
                sync_status = result[
                    len("OK get IO:Current/Dev/SyncStatus 0 0") :
                ].strip()

        # Disable mute
        while muted_status != "OFF":
            time.sleep(0.05)
            result = self.send_command("set IO:Current/Dev/MuteOn 0 0 0")

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result[:-1]}, retrying..."
                )
            elif result.startswith("OK set IO:Current/Dev/MuteOn 0 0 0 "):
                muted_status = (
                    result[len("OK set IO:Current/Dev/MuteOn 0 0 0 ") :]
                    .strip()
                    .strip('"')
                )

        # After removing mute, our device should go to the sync state no. 5.
        while sync_status != "5":
            time.sleep(0.05)
            result = self.send_command("get IO:Current/Dev/SyncStatus 0 0")

            if result.startswith("ERROR"):
                logging.warning(
                    f"Yamaha Remote Control received an error response: {result[:-1]}, retrying..."
                )
            elif result.startswith("OK get IO:Current/Dev/SyncStatus 0 0 "):
                sync_status = result[
                    len("OK get IO:Current/Dev/SyncStatus 0 0") :
                ].strip()

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
        self, channels: Sequence[int], states: Sequence[int]
    ) -> None: ...

    @overload
    def set_phantom_power(self, channels: int, states: int) -> None: ...

    def set_phantom_power(self, channels, states):
        """
        Used to set the phantom power of a Yamaha device.
        Args:
            channels: List or Index of channel.s
            states: List or value of state.s

        Returns:
        """
        if isinstance(channels, int):
            channels = [channels]
            states = [states]

        for channel, state in zip(channels, states):
            command = f"set IO:Current/InCh/48VOn {channel} {self.device_id} {state}"
            self.send_command(command)

        logging.info(
            f"Yamaha Remote Control set phantom power channels: {channels} state: {states}"
        )

    @overload
    def set_ha_gain(self, channels: Sequence[int], state: Sequence[int]) -> None: ...

    @overload
    def set_ha_gain(self, channels: int, states: int) -> None: ...

    def set_ha_gain(self, channels, states):
        """
        Used to set the phantom power of a Yamaha device.
        Args:
            channels: List or Index of channel.s
            states: List or value of state.s

        Returns:
        """
        if isinstance(channels, int):
            channels = [channels]
            states = [states]

        for channel, state in zip(channels, states):
            command = f"set IO:Current/InCh/HAGain {channel} {self.device_id} {state}"
            self.send_command(command)

        logging.info(
            f"Yamaha Remote Control set hagain channels: {channels} state: {states}"
        )

    def is_general_phantom_power_activated(self) -> bool | None:
        """

        Returns:

        """
        message = f"get IO:Current/Dev/48VMasterOn 0 0"
        result = self.send_command(message)
        if not result:
            return None

        return result.replace("\n", "").split(" ")[-1] == "1"

    @staticmethod
    def scan_devices(waits=False) -> set[YSDPPacket]:
        # The discovery starts when the class is instanciated, so access it before waiting.
        discoverer = YamahaDiscoverer()
        if waits:
            time.sleep(1)

        return discoverer.get_devices()
