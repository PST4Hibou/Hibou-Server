import binascii
import socket
import logging
import struct
from typing import Sequence

from typing_extensions import overload


class YamahaRemoteControl:
    """
    This class implements the Yamaha Remote Control protocol.
    """

    ADVERTISING_MCAST_GRP = "239.192.0.64"
    ADVERTISING_PORT = 54330
    LOCAL_IP = "0.0.0.0"

    def __init__(self, ip: str, port: int = 49280, device_id: int = 0):
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
    def scan_devices():
        """
        Scan for Yamaha Remote Control devices.
        For the moment, we only support one device at a time.
        """

        # Construct the payload to advertise for devices
        payload_hex = "5953445000380004c0a8fa140000000000000000000000000800273de005085f7970612d73637000150659616d61686108522052656d6f74650459303030"
        payload = binascii.unhexlify(payload_hex)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("", YamahaRemoteControl.ADVERTISING_PORT))

        # Join the multicast group
        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(YamahaRemoteControl.ADVERTISING_MCAST_GRP),
            socket.inet_aton(YamahaRemoteControl.LOCAL_IP),
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # Avoid receiving the packet I send.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(YamahaRemoteControl.LOCAL_IP),
        )
        sock.settimeout(2.0)

        # Send the payload
        sock.sendto(
            payload,
            (
                YamahaRemoteControl.ADVERTISING_MCAST_GRP,
                YamahaRemoteControl.ADVERTISING_PORT,
            ),
        )

        try:
            data, (addr, _) = sock.recvfrom(4096)
        except socket.timeout:
            sock.close()
            return None

        sock.close()
        return addr, data
