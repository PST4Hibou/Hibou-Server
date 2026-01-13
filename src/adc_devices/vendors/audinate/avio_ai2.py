import asyncio
import logging
from typing import List

from netaudio import DanteBrowser, DanteDevice

from src.network.helpers.interface import get_interface_from_ipv4
from src.network.multicast import get_multicast_stream_info
from ..base_vendor import BaseVendor
from ...models.adc_device import ADCDevice


class AVIOAI2Manager(BaseVendor):
    """Manager for Audinate AVIO AI2 devices."""

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
    def scan_devices(cls) -> List[ADCDevice]:
        """Synchronous wrapper for asynchronous Dante discovery."""
        logging.debug("Starting synchronous device discovery for AVIOAI2.")
        dante_devices = cls._run(cls._scan_devices)
        if not dante_devices:
            logging.warning("No devices returned from async discovery.")
            return []

        converted_devices = [cls.to_device(d) for d in dante_devices]
        logging.info(
            "Converted %d Dante devices to internal Device objects",
            len(converted_devices),
        )
        return converted_devices

    @staticmethod
    def to_device(device: DanteDevice) -> ADCDevice:
        """Convert DanteDevice to your internal Device model."""
        interface = get_interface_from_ipv4(device.ipv4)
        if not interface:
            raise ValueError(
                f"No network interface matches the IP address {device.ipv4}. "
                "Please verify that the IP address is part of the configured target network."
            )
        res = get_multicast_stream_info(interface, device.ipv4)
        return ADCDevice(
            name=device.name,
            model=device.model_id,
            ipv4=str(device.ipv4),
            port=res.get("multicast_port"),
            multicast_ip=res.get("multicast_ip"),
            rtp_payload=res.get("rtp_payload"),
            interface=interface,
            clock_rate=48000,
        )
