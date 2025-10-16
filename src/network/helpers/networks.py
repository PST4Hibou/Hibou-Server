import ipaddress
import psutil


def get_networks():
    """
    Returns a dictionary mapping local NICs to their networks.

    Output format:
    {
        'enp0s3': [{'ip': '192.168.1.10', 'netmask': '255.255.255.0', 'network': '192.168.1.0/24'}, ...],
        'lo': [{'ip': '127.0.0.1', 'netmask': '255.0.0.0', 'network': '127.0.0.0/8'}],
    }
    """
    networks = {}

    for iface, addrs in psutil.net_if_addrs().items():
        iface_networks = []
        for addr in addrs:
            # Only consider IPv4 addresses
            if addr.family.name != "AF_INET":
                continue
            ip = addr.address
            netmask = addr.netmask
            if ip and netmask:
                network = str(ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False))
                iface_networks.append(
                    {"ip": ip, "netmask": netmask, "network": network}
                )
        if iface_networks:
            networks[iface] = iface_networks

    return networks
