from dataclasses import dataclass


@dataclass
class Device:
    name: str
    model: str
    ipv4: str
    port: int
    multicast_ip: str
    rtp_payload: int
    interface: str
