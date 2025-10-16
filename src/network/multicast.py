from src.network.capture import capture_udp_packets
from typing import Optional

import ipaddress


def is_multicast_ip(ip: str) -> bool:
    """
    Check if the given IP address is a multicast address (224.0.0.0/4).

    Parameters
    ----------
    ip : str
        The IP address to check.

    Returns
    -------
    bool
        True if the IP is multicast, False otherwise.
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_multicast
    except ValueError:
        # Invalid IP string
        return False


def get_multicast_stream_info(interface: str, source_ip: str) -> Optional[dict]:
    multicast_ip = None
    multicast_port = None

    # Step 1: Detect the first multicast UDP packet from the device
    for pkt in capture_udp_packets(interface=interface, source_ip=source_ip, limit=50):
        if not hasattr(pkt, "ip") or not hasattr(pkt, "udp"):
            continue

        dst_ip = pkt.ip.dst
        dst_port = int(pkt.udp.dstport)

        if is_multicast_ip(dst_ip):
            multicast_ip = dst_ip
            multicast_port = dst_port
            break

    if not multicast_ip or not multicast_port:
        return None

    # Step 2: Capture RTP packets dynamically on the detected multicast port
    decode_as = {f"udp.port=={multicast_port}": "rtp"}

    for pkt in capture_udp_packets(
        interface=interface,
        source_ip=source_ip,
        dst_port=multicast_port,
        decode_as=decode_as,
        limit=20,
    ):
        if hasattr(pkt, "rtp"):
            rtp_payload = getattr(pkt.rtp, "p_type", 97)
            if rtp_payload:
                return {
                    "multicast_ip": multicast_ip,
                    "multicast_port": multicast_port,
                    "rtp_payload": rtp_payload,
                }

    return None
