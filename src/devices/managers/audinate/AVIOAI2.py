from src.network.helpers.interface import get_interface_from_ipv4
from src.network.multicast import get_multicast_stream_info
from src.devices.managers.base import DeviceManager
from netaudio import DanteBrowser, DanteDevice
from src.devices.models import Device
from typing import List

import asyncio
import logging


logger = logging.getLogger("netaudio")
logger.setLevel(logging.WARNING)


class AVIOAI2Manager(DeviceManager):
    """Manager for Audinate AVIO AI2 devices."""

    @staticmethod
    def _run(async_fn):
        """Safely run an async function synchronously."""
        try:
            return asyncio.run(async_fn())
        except Exception as e:
            logger.exception("Error while running asyncio function: %s", e)
            return []

    @staticmethod
    async def _scan_devices() -> List[DanteDevice]:
        """Asynchronously discover Dante devices and fetch their control data."""
        dante_browser = DanteBrowser(mdns_timeout=1.5)
        discovered = await dante_browser.get_devices()

        if not discovered:
            logger.warning("No Dante devices discovered.")
            return []

        await asyncio.gather(*(device.get_controls() for device in discovered.values()))

        devices = list(discovered.values())
        logger.info("Discovered %d Dante devices", len(devices))
        return devices

    @classmethod
    def scan_devices(cls) -> List[Device]:
        """Synchronous wrapper for asynchronous Dante discovery."""
        logger.debug("Starting synchronous device discovery for AVIOAI2.")
        dante_devices = cls._run(cls._scan_devices)
        if not dante_devices:
            logger.warning("No devices returned from async discovery.")
            return []

        converted_devices = [cls.to_device(d) for d in dante_devices]
        logger.info(
            "Converted %d Dante devices to internal Device objects",
            len(converted_devices),
        )
        return converted_devices

    @staticmethod
    def to_device(device: DanteDevice) -> Device:
        """Convert DanteDevice to your internal Device model."""
        interface = get_interface_from_ipv4(device.ipv4)
        if not interface:
            raise ValueError(f"No interface found for IP {device.ipv4}")
        res = get_multicast_stream_info(interface, device.ipv4)
        return Device(
            name=device.name,
            model=device.model_id,
            ipv4=device.ipv4,
            port=res.get("multicast_port"),
            multicast_ip=res.get("multicast_ip"),
            rtp_payload=res.get("rtp_payload"),
            interface=interface,
        )
