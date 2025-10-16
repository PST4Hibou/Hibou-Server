from typing import Optional

import asyncio
import pyshark


def capture_udp_packets(
    interface: str,
    source_ip: Optional[str] = None,
    dest_ip: Optional[str] = None,
    src_port: Optional[int] = None,
    dst_port: Optional[int] = None,
    protocol: str = "udp",
    decode_as: dict | None = None,
    limit: int = 10,
):
    filters = [protocol]

    if source_ip:
        filters.append(f"ip.src == {source_ip}")
    if dest_ip:
        filters.append(f"ip.dst == {dest_ip}")
    if src_port:
        filters.append(f"{protocol}.srcport == {src_port}")
    if dst_port:
        filters.append(f"{protocol}.dstport == {dst_port}")

    display_filter = " && ".join(filters)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    capture = pyshark.LiveCapture(
        interface=interface, display_filter=display_filter, decode_as=decode_as
    )

    try:
        for packet in capture.sniff_continuously(packet_count=limit):
            yield packet
    finally:
        capture.close()
