from dataclasses import dataclass

from src.network.helpers.ping import ping


@dataclass
class ADCDevice:
    name: str
    model: str
    ipv4: str
    port: int
    multicast_ip: str
    rtp_payload: int
    interface: str

    def is_online(self):
        return ping(self.ipv4)
