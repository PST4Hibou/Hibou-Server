import logging
from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Any

from src.devices.audio.controllers.audinate.avio_ai2 import AvioAi2Controller
from src.devices.audio.controllers.base_controller import BaseController
from src.devices.audio.controllers.yamaha.tio1608_d import YamahaTio1608Controller
from src.devices.audio.dante.models import DanteADCDevice
from src.helpers.decorators import singleton
from src.helpers.json import read_json, write_json


@singleton
class ADCControllerManager:
    _SUPPORTED_CONTROLLER: List[BaseController] = [
        YamahaTio1608Controller,
        AvioAi2Controller,
    ]

    def __init__(self):
        self.controllers: List[BaseController] = []

    @property
    def adc_devices(self) -> List[DanteADCDevice]:
        """
        Return list of DanteADCDevice instances from all controllers.
        """
        _adc_devices: List[DanteADCDevice] = []
        for controller in self.controllers:
            _adc_devices.extend(controller.adc_devices)

        return _adc_devices

    def load_devices_from_files(self, json_path: Path) -> None:
        """
        Load controllers and devices from controllers_devices.json configuration file.
        Populates self.controllers with controller instances.
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Controller configuration file not found: {json_path}"
            )

        data = read_json(path)
        controllers_data = data.get("controllers", [])
        if not controllers_data:
            raise ValueError("No controllers found in the provided JSON file.")

        # Map controller names to controller classes
        controller_map: Dict[str, type] = {
            "AVIOAI2": AvioAi2Controller,
            "YamahaTio1608": YamahaTio1608Controller,
        }

        loaded_controllers: List[BaseController] = []

        for controller_data in controllers_data:
            controller_name = controller_data.get("name")
            if not controller_name:
                logging.warning("Skipping controller entry without name field")
                continue

            controller_class = controller_map.get(controller_name)
            if not controller_class:
                logging.warning(
                    f"Unknown controller type '{controller_name}'. Supported types: {list(controller_map.keys())}"
                )
                continue

            try:
                if controller_name == "AVIOAI2":
                    # AvioAi2Controller takes a list of DanteADCDevice instances
                    devices_data = controller_data.get("devices", [])
                    if not devices_data:
                        logging.warning(
                            f"No devices found for controller {controller_name}"
                        )
                        continue

                    dante_devices = [DanteADCDevice(**dev) for dev in devices_data]
                    controller = AvioAi2Controller(dante_devices)
                    loaded_controllers.append(controller)
                    logging.info(
                        f"Loaded {controller_name} controller with {len(dante_devices)} devices"
                    )

                elif controller_name == "YamahaTio1608":
                    # YamahaTio1608Controller takes an IP address string
                    # Try to get IP from controller-level field, or from first device
                    ip = controller_data.get("ip")
                    devices_data = controller_data.get("devices", [])

                    if not ip:
                        if devices_data and len(devices_data) > 0:
                            ip = devices_data[0].get("ipv4")
                        if not ip:
                            logging.warning(
                                f"No IP address found for {controller_name} controller"
                            )
                            continue

                    controller = YamahaTio1608Controller(ip, auto_discovery=False)

                    # Load devices from JSON file instead of using scanned devices
                    if devices_data:
                        dante_devices = [DanteADCDevice(**dev) for dev in devices_data]
                        controller.adc_devices = dante_devices
                        logging.info(
                            f"Loaded {controller_name} controller with IP {ip} and {len(dante_devices)} devices from file"
                        )
                    else:
                        logging.warning(
                            f"No devices found for {controller_name} controller"
                        )

                    loaded_controllers.append(controller)

            except Exception as e:
                logging.exception(f"Failed to load controller {controller_name}: {e}")
                continue

        if not loaded_controllers:
            logging.warning(
                "No controllers were successfully loaded from the configuration file."
            )

        self.controllers = loaded_controllers
        logging.info(f"Loaded {len(loaded_controllers)} controllers from {json_path}")

    def save_devices_to_files(self, json_path: Path) -> None:
        """
        Save current controllers and their devices to controllers_devices.json configuration file.
        """
        if not self.controllers:
            logging.warning("No controllers to save. Skipping file write.")
            return

        controllers_data: List[Dict[str, Any]] = []

        for controller in self.controllers:
            controller_dict: Dict[str, Any] = {}

            if isinstance(controller, AvioAi2Controller):
                controller_dict["name"] = "AVIOAI2"
                # Extract devices from AvioAi2Controller
                devices = controller.adc_devices
                controller_dict["devices"] = [asdict(dev) for dev in devices]

            elif isinstance(controller, YamahaTio1608Controller):
                controller_dict["name"] = "YamahaTio1608"
                # Extract IP from YamahaTio1608Controller
                controller_dict["ip"] = controller.ip
                # Extract devices from YamahaTio1608Controller
                devices = controller.adc_devices
                controller_dict["devices"] = [asdict(dev) for dev in devices]

            else:
                logging.warning(
                    f"Unknown controller type {type(controller).__name__}. Skipping."
                )
                continue

            controllers_data.append(controller_dict)

        if not controllers_data:
            logging.warning("No valid controllers to save. Skipping file write.")
            return

        output_data = {"controllers": controllers_data}
        write_json(json_path, output_data)
        logging.info(
            f"Saved {len(controllers_data)} controllers with "
            f"{sum(len(c.get('devices', [])) for c in controllers_data)} total devices to {json_path}"
        )

    def auto_discover(self):
        """
        Automatically discover devices using all controllers.
        """
        discovered_controllers: List[BaseController] = []
        for manager in self._SUPPORTED_CONTROLLER:
            logging.blank_line()
            logging.info(f"Auto-discovering devices for {manager.__name__}")

            try:
                controllers = manager.scan_devices()
                discovered_controllers.extend(controllers)
                logging.info(
                    f"Discovered {len(discovered_controllers)} devices via {manager.__name__}"
                )
            except Exception as e:
                logging.exception(
                    f"Failed to auto-discover devices for {manager.__class__.__name__}, {e}",
                )

        if not discovered_controllers:
            logging.warning("No devices discovered on all managers.")

        self.controllers = discovered_controllers

    def __str__(self):
        return f"{self.__class__.__name__}({self.adc_devices})"
