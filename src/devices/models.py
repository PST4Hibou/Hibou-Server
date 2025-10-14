from dataclasses import dataclass


@dataclass
class Device:
    name: str
    model: str
    ip: str
    port: int
    multicast_ip: str
    rtp: int
    interface: str
