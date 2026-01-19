import socket
import binascii

hex_payload = (
    "5953445000380004c0a8fa140000000000000000000000000800273de005085f7970612d736370"
    "00150659616d61686108522052656d6f74650459303030"
)


payload = binascii.unhexlify(hex_payload)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(payload, ("239.192.0.64", 54330))
sock.close()

import socket
import sys

#
# def main(argv):
#     multicast_group = argv[1]
#     multicast_port = int(argv[2])
#     interface_ip = argv[3]
#
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
#     # See man socket(7)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#
#     sock.bind(("", multicast_port))
#     sock.setsockopt(
#         socket.SOL_IP,
#         socket.IP_ADD_MEMBERSHIP,
#         socket.inet_aton(multicast_group) + socket.inet_aton(interface_ip),
#     )
#
#     while True:
#         received = sock.recv(1500)
#         print("Received packet of {0} bytes".format(len(received)))
#
#
# if __name__ == "__main__":
#     if len(sys.argv) != 4:
#         print("Usage: {0} <group address> <port> <interface ip>".format(sys.argv[0]))
#         sys.exit(1)
#     main(sys.argv)
