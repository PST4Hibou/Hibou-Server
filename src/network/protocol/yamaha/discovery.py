import binascii
import threading
import socket
import struct
import time

from src.network.protocol.yamaha.descriptions import YSDPPacket
from src.helpers.decorators import singleton


@singleton
class YamahaDiscoverer:
    ADVERTISING_MCAST_GRP = "239.192.0.64"
    ADVERTISING_PORT = 54330
    LOCAL_IP = "192.168.250.178"
    # Notice that although we use the hex payload because we are lazy, it follows the YSDP + SCP scheme.
    PAYLOAD = binascii.unhexlify(
        "5953445000380004c0a8fa140000000000000000000000000800273de005085f7970612d73637000150659616d61686108522052656d6f74650459303030"
    )

    def __init__(self):
        self._t = threading.Thread(target=self._watcher)
        self._s = threading.Thread(target=self._sender)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.bind(("", YamahaDiscoverer.ADVERTISING_PORT))

        # Join the multicast group
        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(YamahaDiscoverer.ADVERTISING_MCAST_GRP),
            socket.inet_aton(YamahaDiscoverer.LOCAL_IP),
        )
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # Avoid receiving the packet I send.
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(YamahaDiscoverer.LOCAL_IP),
        )
        self.sock.settimeout(2.0)

        self.devices = set()
        self.connected = True

        self._t.start()
        self._s.start()

    def __del__(self):
        self.connected = False
        self._s.join()
        self._t.join()
        self.sock.close()

    def _watcher(self):
        while self.connected:
            try:
                data, (addr, _) = self.sock.recvfrom(4096)
                self.devices.add(YSDPPacket.from_bytes(data))
            except TimeoutError:
                pass
            finally:
                pass

    def _sender(self):
        while self.connected:
            self.sock.sendto(
                self.PAYLOAD,
                (
                    YamahaDiscoverer.ADVERTISING_MCAST_GRP,
                    YamahaDiscoverer.ADVERTISING_PORT,
                ),
            )

            time.sleep(3)

    def get_devices(self):
        return self.devices
