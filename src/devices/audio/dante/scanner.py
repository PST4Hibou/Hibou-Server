import asyncio
import logging
from typing import List

from netaudio import DanteBrowser, DanteDevice

from src.devices.audio.dante.models import DanteADCDevice
from src.network.helpers.interface import get_interface_from_ipv4
from src.network.multicast import get_multicast_stream_info


class DanteADCScanner:
    @staticmethod
    def _run(async_fn):
        """Safely run an async function synchronously."""
        try:
            return asyncio.run(async_fn())
        except Exception as e:
            logging.exception("Error while running asyncio function: %s", e)
            return []

    @staticmethod
    async def _scan_devices() -> List[DanteDevice]:
        """Asynchronously discover Dante devices and fetch their control data."""
        dante_browser = DanteBrowser(mdns_timeout=1.5)
        discovered = await dante_browser.get_devices()

        if not discovered:
            logging.warning("No Dante devices discovered.")
            return []

        await asyncio.gather(*(device.get_controls() for device in discovered.values()))

        devices = list(discovered.values())
        logging.info("Discovered %d Dante devices", len(devices))
        return devices

    @classmethod
    def scan_devices(cls, model_id: str = None) -> List[DanteADCDevice]:
        """Synchronous wrapper for asynchronous Dante discovery."""
        logging.debug("Starting device discovery for Yamaha Tio1608-D.")
        dante_devices = cls._run(cls._scan_devices)
        if not dante_devices:
            logging.warning("No devices returned from discovery.")
            return []

        if model_id:
            dante_devices = list(
                filter(lambda d: d.model_id == model_id, dante_devices)
            )
        converted_devices = [cls.to_device(d) for d in dante_devices]
        logging.info(
            "Converted %d Dante devices to internal Device objects for %s",
            len(converted_devices),
            model_id,
        )
        return converted_devices

    @staticmethod
    def to_device(device: DanteDevice) -> DanteADCDevice:
        """Convert DanteDevice to your internal Device model."""
        interface = get_interface_from_ipv4(device.ipv4)
        if not interface:
            raise ValueError(
                f"No network interface matches the IP address {device.ipv4}. "
                "Please verify that the IP address is part of the configured target network."
            )
        res = get_multicast_stream_info(interface, device.ipv4)
        return DanteADCDevice(
            name=device.name,
            model=device.model_id,
            ipv4=str(device.ipv4),
            nb_channels=res.get("active_channels"),
            port=res.get("multicast_port"),
            multicast_ip=res.get("multicast_ip"),
            rtp_payload=res.get("rtp_payload"),
            interface=interface,
            clock_rate=48000,
        )
