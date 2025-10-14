from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from src.devices.models import Device
from src.helpers.json import read_json, write_json
from src.devices.static_checkup import static_checkup


class Devices:

    @classmethod
    def load_devices(cls, json_path: Path) -> List[Device]:
        """
        Load devices from a JSON configuration file and return Device instances.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Device configuration file not found: {json_path}")

        data = read_json(path)
        devices = data.get("devices", [])
        if not devices:
            raise ValueError("No devices found in the provided JSON file.")

        if not static_checkup(devices):
            raise ValueError("Device configuration failed static validation.")

        return [Device(**dev) for dev in devices]

    @classmethod
    def add_device(
        cls,
        json_path: Path,
        new_device: Device,
        devices: Optional[List[Device]] = None,
    ) -> List[Device]:
        """
        Add a new device to the configuration, validate, and persist to file.
        """
        path = Path(json_path)
        devices = devices or (cls.load_devices(path) if path.exists() else [])

        devices.append(new_device)
        devices_data = [asdict(dev) for dev in devices]

        if not static_checkup(devices_data):
            raise ValueError("Updated device configuration failed static validation.")

        write_json(path, {"devices": devices_data})
        return devices

    @staticmethod
    def to_string(device: Device) -> str:
        """Return a human-readable summary of a device."""
        return (
            f"Device: {device.name}, Model: {device.model}, IP: {device.ip}, "
            f"Port: {device.port}, Multicast IP: {device.multicast_ip}, "
            f"RTP: {device.rtp}, Interface: {device.interface}"
        )
