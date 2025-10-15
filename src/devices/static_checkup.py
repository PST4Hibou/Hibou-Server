from src.devices.supported_devices import supported_devices


def check_names(devices: list[dict]) -> bool:
    """
    Ensure all devices have unique 'name' fields.

    Args:
        devices (list[dict]): List of device dictionaries.

    Returns:
        bool: True if all device names are unique, False otherwise.
    """
    names = [item.get("name") for item in devices]
    return len(names) == len(set(names))


def check_ports(devices: list[dict]) -> bool:
    """
    Ensure all devices have unique 'port' fields.

    Args:
        devices (list[dict]): List of device dictionaries.

    Returns:
        bool: True if all device ports are unique, False otherwise.
    """
    ports = [item.get("port") for item in devices]
    return len(ports) == len(set(ports))


def check_required_fields(dev: dict, required=None) -> None:
    """
    Check that all required fields are present in a device dictionary.

    Args:
        dev (dict): Device dictionary to validate.
        required (set, optional): Set of required fields. Defaults to
            {"name", "model", "ip", "port", "multicast_ip", "rtp"}.

    Raises:
        ValueError: If any required field is missing.
    """
    if required is None:
        required = {"name", "model", "ip", "port", "multicast_ip", "rtp"}
    missing = required - set(dev.keys())
    if missing:
        raise ValueError(f"Device {dev.get('name')} is missing fields: {missing}")


def check_port_range(dev: dict) -> None:
    """
    Check that the device port is within the valid range (1–65535).

    Args:
        dev (dict): Device dictionary containing a 'port' key.

    Raises:
        ValueError: If the port is out of the valid range.
    """
    if not (1 <= dev.get("port") <= 65535):
        raise ValueError(f"Invalid port {dev.get('port')} for {dev.get('name')}")


def check_rtp_payload(dev: dict) -> None:
    """
    Check that the RTP payload is within the dynamic range (96–127).

    Args:
        dev (dict): Device dictionary containing an 'rtp' key.

    Raises:
        ValueError: If the RTP payload is out of range.
    """
    rtp = dev.get("rtp")
    if not (96 <= rtp <= 127):
        raise ValueError(f"Invalid RTP payload {rtp} for {dev.get('name')}")


def check_device_model(dev: dict) -> None:
    model = dev.get("model")
    name = dev.get("name", "Unknown device")

    if model not in supported_devices:
        raise ValueError(
            f"Invalid device model '{model}' for {name}.\n"
            f"Supported models: {', '.join(supported_devices)}"
        )


def check_device(dev: dict) -> None:
    """
    Run all validation checks for a single device.

    Args:
        dev (dict): Device dictionary to validate.

    Raises:
        ValueError: If any validation check fails.
    """
    check_device_model(dev)
    check_required_fields(dev)
    check_port_range(dev)
    check_rtp_payload(dev)


def static_checkup(devices: list[dict]) -> bool:
    """
    Run consistency and validation checks on a list of devices.

    Performs the following checks:
        - All device names are unique.
        - All device ports are unique.
        - Each device contains all required fields.
        - Each device's port is within valid range (1–65535).
        - Each device's RTP payload is within dynamic range (96–127).

    Args:
        devices (list[dict]): List of device dictionaries to validate.

    Returns:
        bool: True if all checks pass.

    Raises:
        ValueError: If any check fails.
    """
    ok_names = check_names(devices)
    if not ok_names:
        raise ValueError("Device names must be unique!")

    ok_ports = check_ports(devices)
    if not ok_ports:
        raise ValueError("Device ports must be unique!")

    for dev in devices:
        check_device(dev)

    return True
