import json
from pathlib import Path

from src.devices.static_checkup import static_checkup


class AudioDevice:
    """
    Represents a single audio/CAN device.
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
        Load all devices from a JSON file and return a list of AudioDevice instances.
        """
        path = Path(json_path)
        with path.open("r") as f:
            data = json.load(f)
        devices = data.get("devices", [])
        if not static_checkup(devices):
            raise ValueError("Invalid devices")
        return [cls(**dev) for dev in devices]

    def __str__(self):
        return f"Device: {self.name}, Model: {self.model}, IP: {self.ip}, Port: {self.port}, Multicast IP: {self.multicast_ip}, RTP: {self.rtp}, Interface: {self.interface}"

    def __repr__(self):
        return self.__str__()
