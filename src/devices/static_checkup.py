def check_names(devices: list[dict]) -> bool:
    """
    Ensure all devices have unique 'name' fields.
    """
    names = [item.get("name") for item in devices]
    return len(names) == len(set(names))


def check_ports(devices: list[dict]) -> bool:
    """
    Ensure all devices have unique 'interface' or 'port' fields.
    """
    ports = [item.get("port") for item in devices]
    return len(ports) == len(set(ports))


def check_required_fields(dev: dict, required=None) -> None:
    """Check that all required fields are present in a device."""
    if required is None:
        required = {"name", "model", "ip", "port", "multicast_ip", "rtp"}
    missing = required - set(dev.keys())
    if missing:
        raise ValueError(f"Device {dev.get('name')} is missing fields: {missing}")


def check_port_range(dev: dict) -> None:
    """Check that the device port is within valid range (1–65535)."""
    if not (1 <= dev["port"] <= 65535):
        raise ValueError(f"Invalid port {dev['port']} for {dev['name']}")


def check_rtp_payload(dev: dict) -> None:
    """Check that RTP payload is within dynamic range (96–127)."""
    if not (96 <= dev["rtp"] <= 127):
        raise ValueError(f"Invalid RTP payload {dev['rtp']} for {dev['name']}")


def check_device(dev: dict) -> None:
    """Run all checks for a single device."""
    check_required_fields(dev)
    check_port_range(dev)
    check_rtp_payload(dev)


def static_checkup(devices: list[dict]) -> bool:
    """
    Run consistency checks on devices list.
    Raises ValueError if any check fails.
    Returns True if all checks pass.
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
