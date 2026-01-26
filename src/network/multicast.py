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


def extract_rtp_payload_type(sdp):
    formats = sdp.media_format.all_fields
    for format in formats:
        value = format.show
        if value.isdigit():
            return int(value)
    return None


def get_multicast_stream_info(interface: str, source_ip: str) -> Optional[dict]:
    multicast_ip = None
    multicast_port = None
    rtp_payload = None
    active_channels = None

    for pkt in capture_udp_packets(
        interface=interface,
        source_ip=source_ip,
        dst_port=9875,
        decode_as={"udp.port==9875": "sap"},
        limit=1,
    ):
        if not hasattr(pkt, "sdp"):
            continue

        sdp = pkt.sdp

        rtp_payload = extract_rtp_payload_type(sdp)
        multicast_port = int(getattr(sdp, "media_port", 0))
        active_channels = int(getattr(sdp, "channels", 0))
        multicast_ip = getattr(sdp, "connection_info_address", None)

    if not is_multicast_ip(multicast_ip):
        return None

    if not multicast_ip or not multicast_port:
        return None

    return {
        "multicast_ip": multicast_ip,
        "multicast_port": multicast_port,
        "rtp_payload": rtp_payload,
        "active_channels": active_channels,
    }
