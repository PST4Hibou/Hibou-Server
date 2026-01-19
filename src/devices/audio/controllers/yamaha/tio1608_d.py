from src.devices.audio.controllers.base_controller import BaseController
from typing import List, Optional
import logging

from src.devices.audio.dante.models import DanteADCDevice
from src.devices.audio.dante.scanner import DanteADCScanner
from src.network.protocol.yamaha_remote_control import YamahaRemoteControl


class YamahaTio1608Controller(BaseController):
    def __init__(self, ip: str):
        super().__init__()

        self.ip = ip

        self.yamaha_remote_control = YamahaRemoteControl(ip)
        if not self.yamaha_remote_control.is_general_phantom_power_activated():
            logging.warning("YamahaTio1608 phantom power is not activated")
        else:
            logging.info("YamahaTio1608 phantom power activated")

        self.adc_devices: List[DanteADCDevice] = DanteADCScanner.scan_devices("1966")

    @classmethod
    def scan_devices(cls) -> Optional["YamahaTio1608Controller"]:
        """
        Scan the network for Yamaha Tio 1608 devices.

        Returns:
            YamahaTio1608Controller
        """
        if not (yamaha_device := YamahaRemoteControl.scan_devices()):
            return None
        logging.info("Discovered Yamaha Top 1608 Controller")
        yamaha_controller = cls(yamaha_device[0])

        return yamaha_controller
