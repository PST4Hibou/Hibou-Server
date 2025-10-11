import json
from pathlib import Path

from src.devices.static_checkup import static_checkup


class AudioDevice:
    """
    Represents a single audio or CAN device with its network and model configuration.

    Attributes:
        name (str): The name of the device.
        model (str): The model identifier of the device.
        ip (str): The IP address of the device.
        port (int): The network port used by the device.
        multicast_ip (str): The multicast IP address, if applicable.
        rtp (int): The RTP (Real-time Transport Protocol) port.
        interface (str): The network interface used by the device.
    """

    def __init__(
        self,
        name: str,
        model: str,
        ip: str,
        port: int,
        multicast_ip: str,
        rtp: int,
        interface: str,
    ):
        """
        Initialize an AudioDevice instance with network and device parameters.

        Args:
            name (str): The name of the device.
            model (str): The model identifier of the device.
            ip (str): The IP address of the device.
            port (int): The network port used by the device.
            multicast_ip (str): The multicast IP address, if applicable.
            rtp (int): The RTP (Real-time Transport Protocol) port.
            interface (str): The network interface used by the device.
        """
        self.name = name
        self.model = model
        self.ip = ip
        self.port = port
        self.multicast_ip = multicast_ip
        self.rtp = rtp
        self.interface = interface

    @classmethod
    def load_devices(cls, json_path: str):
        """
        Load multiple devices from a JSON file and return as AudioDevice instances.

        Args:
            json_path (str): Path to the JSON file containing device definitions.

        Returns:
            List[AudioDevice]: A list of AudioDevice instances created from the JSON data.

        Raises:
            ValueError: If the loaded devices fail static validation.
        """
        path = Path(json_path)
        with path.open("r") as f:
            data = json.load(f)
        devices = data.get("devices", [])
        if not static_checkup(devices):
            raise ValueError("Invalid devices")
        return [cls(**dev) for dev in devices]

    def __str__(self):
        """
        Return a human-readable string representation of the device.
        """
        return (
            f"Device: {self.name}, Model: {self.model}, IP: {self.ip}, "
            f"Port: {self.port}, Multicast IP: {self.multicast_ip}, "
            f"RTP: {self.rtp}, Interface: {self.interface}"
        )

    def __repr__(self):
        """
        Return the official string representation of the device, same as __str__.
        """
        return self.__str__()
