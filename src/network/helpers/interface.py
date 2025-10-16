from src.network.helpers.networks import get_networks

import ipaddress
import psutil


def get_local_interfaces():
    """
    Return a list of local network interface names on Linux.
    """
    return list(psutil.net_if_addrs().keys())


def get_interface_from_ipv4(ipv4: str):
    """
    Return the network interface(s) whose network contains the given IPv4 address.

    Args:
        ipv4 (str): IPv4 address to check.

    Returns:
        str: String of interface names matching the given IP.
                   None if no interface matches.
    """
    target_ip = ipaddress.IPv4Address(ipv4)
    nets = get_networks()
    matching_ifaces: str | None = None

    for iface, iface_nets in nets.items():
        for net_info in iface_nets:
            network = ipaddress.IPv4Network(net_info["network"])
            if target_ip in network:
                matching_ifaces = iface
                break

    return matching_ifaces
