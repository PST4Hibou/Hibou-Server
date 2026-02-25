from src.devices.camera.vendors.base_vendor import BaseVendor
from typing import Type

import logging


class PTZController:
    """Central registry and factory for PTZ camera instances."""

    _instances: dict[str, "BaseVendor"] = {}  # Maps camera_name -> PTZ instance

    def __new__(
        cls,
        name: str,
        vendor_class: Type["BaseVendor"] = None,
        *args,
        **kwargs,
    ):
        """
        Factory that returns an existing PTZ instance if already created,
        otherwise initializes and registers a new one.
        """
        # If camera already registered, return it
        if name in cls._instances:
            return cls._instances[name]

        # If vendor_class not provided for a new camera, raise error
        if vendor_class is None:
            raise ValueError(
                f"Camera '{name}' not initialized yet — please provide vendor_class and connection info."
            )

        # Create new PTZ device instance
        logging.info(
            f"Initializing new PTZ camera '{name}' using {vendor_class.__name__}"
        )
        ptz_instance = vendor_class(name, *args, **kwargs)

        # Register and return it
        cls._instances[name] = ptz_instance
        return ptz_instance

    @classmethod
    def get(cls, name: str) -> "BaseVendor":
        """Retrieve an existing PTZ instance by name."""
        if name not in cls._instances:
            raise KeyError(f"No PTZ camera registered under name '{name}'")
        return cls._instances[name]

    @classmethod
    def list_cameras(cls) -> list[str]:
        """List all registered camera names."""
        return list(cls._instances.keys())

    @classmethod
    def remove(cls, name: str | None = None) -> None:
        """Unregister and release one or all PTZ cameras."""

        def _release(camera_name: str) -> None:
            ptz = cls._instances.pop(camera_name, None)
            if not ptz:
                logging.warning(f"Camera '{camera_name}' not found.")
                return

            if hasattr(ptz, "release_stream"):
                ptz.release_stream()

            logging.info(f"Camera '{camera_name}' released and unregistered.")

        # Remove all cameras
        if name is None:
            for camera_name in list(cls._instances.keys()):
                PTZController(camera_name).stop_continuous()
                _release(camera_name)
        else:
            PTZController(name).stop_continuous()
            _release(name)
