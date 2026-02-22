import logging

from src.network.protocol.yamaha_remote_control import YamahaRemoteControl
from src.devices.audio.controllers.base_controller import BaseController
from src.devices.audio.dante.scanner import DanteADCScanner
from src.devices.audio.dante.models import DanteADCDevice
from typing import List, Optional


class YamahaTio1608Controller(BaseController):
    def __init__(
        self,
        ip: str,
        auto_discovery: bool = True,
        default_ha_gains: Optional[List[int]] = None,
    ):
        super().__init__()

        self.ip = ip

        self.yamaha_remote_control = YamahaRemoteControl(ip)

        if not self.yamaha_remote_control.is_general_phantom_power_activated():
            logging.warning("YamahaTio1608 phantom power is not activated")
        else:
            logging.info("YamahaTio1608 phantom power activated")
            self.yamaha_remote_control.set_phantom_power(
                [i for i in range(0, 16)], [1] * 16
            )

        if default_ha_gains:
            self.yamaha_remote_control.set_ha_gain(
                [i for i in range(len(default_ha_gains))], default_ha_gains
            )

        self.adc_devices: List[DanteADCDevice] = []
        if auto_discovery:
            self.adc_devices = DanteADCScanner.scan_devices("1966")

    @classmethod
    def scan_devices(cls) -> List["YamahaTio1608Controller"]:
        """
        Scan the network for Yamaha Tio 1608 devices.

        Returns:
            YamahaTio1608Controller
        """
        if not (yamaha_device := YamahaRemoteControl.scan_devices(waits=True)):
            return []
        logging.info("Discovered Yamaha Top 1608 Controller")

        return [cls(dev.ip_address) for dev in yamaha_device]
