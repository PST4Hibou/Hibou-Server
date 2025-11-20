from src.ptz_devices.vendors.base_vendor import BaseVendor
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
        ptz_instance = vendor_class(*args, **kwargs)

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
    def remove(cls, name: str) -> None:
        """Unregister and release a PTZ camera."""
        if name in cls._instances:
            ptz = cls._instances[name]
            if hasattr(ptz, "release_stream"):
                ptz.release_stream()
            del cls._instances[name]
            logging.info(f"Camera '{name}' released and unregistered.")
