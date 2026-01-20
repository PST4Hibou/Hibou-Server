from dataclasses import dataclass
from src.network.helpers.ping import ping


@dataclass
class DanteADCDevice:
    name: str
    model: str
    ipv4: str
    port: int
    nb_channels: int
    multicast_ip: str
    rtp_payload: int
    interface: str
    clock_rate: int

    def is_online(self) -> bool:
        """
        Check if the device is online.
        This is a blocking function.
        Returns:

        """
        return ping(self.ipv4)
