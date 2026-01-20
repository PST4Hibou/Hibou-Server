from src.devices.audio.controllers.base_controller import BaseController
from typing import List
import logging

from src.devices.audio.dante.models import DanteADCDevice
from src.devices.audio.dante.scanner import DanteADCScanner


class AvioAi2Controller(BaseController):
    def __init__(self, devices: List[DanteADCDevice]):
        super().__init__()

        self.adc_devices: List[DanteADCDevice] = devices

    @classmethod
    def scan_devices(cls) -> List["AvioAi2Controller"]:
        """
        Scan the network for AvioAi2 devices

        Returns:
            AvioAi2Controller
        """
        adc_devices = DanteADCScanner.scan_devices("DAI2")
        if len(adc_devices) == 0:
            return []

        return [AvioAi2Controller(adc_devices)]
