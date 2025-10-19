from src.network.helpers.ping import ping
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

    def is_online(self):
        return ping(self.ipv4)
