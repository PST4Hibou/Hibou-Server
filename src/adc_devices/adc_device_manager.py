import logging
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from src.helpers.json import read_json, write_json
from .models.adc_device import ADCDevice
from .utils.static_checkup import static_checkup
from .vendors.audinate.avio_ai2 import AVIOAI2Manager


class ADCDeviceManager:
    """High-level orchestrator for discovering, loading, and managing audio devices."""

    _SUPPORTED_MANAGERS = [
        AVIOAI2Manager,
    ]

    @classmethod
    def load_devices_from_files(cls, json_path: Path) -> List[ADCDevice]:
        """
        Load devices from a JSON configuration file and return a list of Device instances.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Device configuration file not found: {json_path}")

        data = read_json(path)
        devices_data = data.get("devices", [])
        if not devices_data:
            raise ValueError("No devices found in the provided JSON file.")

        if not static_checkup(devices_data):
            raise ValueError("Device configuration failed static validation.")

        devices = [ADCDevice(**dev) for dev in devices_data]
        logging.info("Loaded %d devices from %s", len(devices), json_path)
        return devices

    @classmethod
    def add_device(
        cls,
        json_path: Path,
        new_device: ADCDevice,
        devices: Optional[List[ADCDevice]] = None,
    ) -> List[ADCDevice]:
        """
        Add a new device to the configuration, validate, and persist to file.
        """
        path = Path(json_path)
        devices = devices or (
            cls.load_devices_from_files(path) if path.exists() else []
        )

        devices.append(new_device)
        devices_data = [asdict(dev) for dev in devices]

        if not static_checkup(devices_data):
            raise ValueError("Updated device configuration failed static validation.")

        write_json(path, {"devices": devices_data})
        logging.info("Added device '%s' and updated configuration.", new_device.name)
        return devices

    @classmethod
    def auto_discover(cls) -> List[ADCDevice]:
        """
        Automatically discover devices using all registered managers.
        """
        discovered_devices: List[ADCDevice] = []

        for manager_cls in cls._SUPPORTED_MANAGERS:
            logging.blank_line()
            logging.info("Running auto-discovery for %s...", manager_cls.__name__)
            try:
                devices = manager_cls.scan_devices()
                discovered_devices.extend(devices)
                logging.info(
                    "Discovered %d devices via %s.", len(devices), manager_cls.__name__
                )
            except Exception as e:
                logging.exception(
                    "Discovery failed for %s: %s", manager_cls.__name__, e
                )

        if not discovered_devices:
            logging.warning("No devices discovered across all managers.")

        return discovered_devices

    @staticmethod
    def to_string(device: ADCDevice) -> str:
        """Return a human-readable summary of a device."""
        return (
            f"Device: {device.name}, Model: {device.model}, IP: {device.ipv4}, "
            f"Port: {device.port}, Multicast IP: {device.multicast_ip}, "
            f"RTP: {device.rtp_payload}, Interface: {device.interface}"
        )
