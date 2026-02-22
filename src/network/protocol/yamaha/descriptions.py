import struct

from dataclasses import dataclass


@dataclass(frozen=True)
class SCPData:
    """SCP data section structure"""

    manufacturer: str
    device_model: str
    device_id: str
    device_name: str

    @classmethod
    def from_bytes(cls, data: bytes) -> "SCPData":
        """Parse the data section"""
        offset = 0

        # Parse manufacturer
        manuf_len = data[offset]
        offset += 1
        manufacturer = data[offset : offset + manuf_len].decode("utf-8")
        offset += manuf_len

        # Parse device model
        dev_model_len = data[offset]
        offset += 1
        device_model = data[offset : offset + dev_model_len].decode("utf-8")
        offset += dev_model_len

        # Parse device ID
        dev_id_len = data[offset]
        offset += 1
        device_id = data[offset : offset + dev_id_len].decode("utf-8")
        offset += dev_id_len

        # Parse device name
        dev_name_len = data[offset]
        offset += 1
        device_name = data[offset : offset + dev_name_len].decode("utf-8")
        offset += dev_name_len

        return cls(
            manufacturer=manufacturer,
            device_model=device_model,
            device_id=device_id,
            device_name=device_name,
        )

    def to_bytes(self) -> bytes:
        """Convert back to bytes"""
        result = bytearray()

        # Manufacturer
        manuf_bytes = self.manufacturer.encode("utf-8")
        result.append(len(manuf_bytes))
        result.extend(manuf_bytes)

        # Device model
        model_bytes = self.device_model.encode("utf-8")
        result.append(len(model_bytes))
        result.extend(model_bytes)

        # Device ID
        id_bytes = self.device_id.encode("utf-8")
        result.append(len(id_bytes))
        result.extend(id_bytes)

        # Device name
        name_bytes = self.device_name.encode("utf-8")
        result.append(len(name_bytes))
        result.extend(name_bytes)

        return bytes(result)


@dataclass(frozen=True)
class YSDPPacket:
    """YSDP (by Yamaha) packet structure"""

    base_proto_name: str  # Should be "YSDP"
    message_len: int  # 2 bytes - length of message after this field
    magic_bytes: bytes  # \80\04
    ip_address: str  # Parsed from \C0\A8\FA\0F (192.168.250.15)
    reserved: bytes  # 12 zero bytes
    mac_address: str  # 6 bytes as hex string
    proto_name: str  # e.g., "_ypa_scp"
    data: SCPData

    @classmethod
    def from_bytes(cls, packet: bytes) -> "YSDPPacket":
        """Parse a complete YSDP packet"""
        offset = 0

        # Parse base protocol name (4 bytes fixed: "YSDP")
        base_proto_name = packet[offset : offset + 4].decode("utf-8")
        offset += 4

        # Parse message length (2 bytes, big-endian)
        message_len = struct.unpack(">H", packet[offset : offset + 2])[0]
        offset += 2

        # Parse magic bytes (2 bytes: \80\04)
        magic_bytes = packet[offset : offset + 2]
        offset += 2

        # Parse IP address (4 bytes)
        ip_bytes = packet[offset : offset + 4]
        ip_address = ".".join(str(b) for b in ip_bytes)
        offset += 4

        # Parse reserved bytes (12 bytes of zeros)
        reserved = packet[offset : offset + 12]
        offset += 12

        # Parse MAC address (6 bytes)
        mac_bytes = packet[offset : offset + 6]
        mac_address = ":".join(f"{b:02x}" for b in mac_bytes)
        offset += 6

        # Parse protocol name length and name
        proto_name_len = packet[offset]
        offset += 1
        proto_name = packet[offset : offset + proto_name_len].decode("utf-8")
        offset += proto_name_len

        # Parse data length (2 bytes, big-endian)
        data_len = struct.unpack(">H", packet[offset : offset + 2])[0]
        offset += 2

        # Parse data section
        data_bytes = packet[offset : offset + data_len]
        data = SCPData.from_bytes(data_bytes)

        return cls(
            base_proto_name=base_proto_name,
            message_len=message_len,
            magic_bytes=magic_bytes,
            ip_address=ip_address,
            reserved=reserved,
            mac_address=mac_address,
            proto_name=proto_name,
            data=data,
        )

    def to_bytes(self) -> bytes:
        """Convert the packet back to bytes"""
        result = bytearray()

        # Base protocol name (4 bytes fixed)
        result.extend(self.base_proto_name.encode("utf-8"))

        # Build the message content first to calculate length
        message_content = bytearray()

        # Magic bytes
        message_content.extend(self.magic_bytes)

        # IP address
        message_content.extend(int(octet) for octet in self.ip_address.split("."))

        # Reserved bytes
        message_content.extend(self.reserved)

        # MAC address
        message_content.extend(int(b, 16) for b in self.mac_address.split(":"))

        # Protocol name
        proto_name_bytes = self.proto_name.encode("utf-8")
        message_content.append(len(proto_name_bytes))
        message_content.extend(proto_name_bytes)

        # Data section
        data_bytes = self.data.to_bytes()
        message_content.extend(struct.pack(">H", len(data_bytes)))
        message_content.extend(data_bytes)

        # Add message length (2 bytes, big-endian)
        result.extend(struct.pack(">H", len(message_content)))

        # Add message content
        result.extend(message_content)

        return bytes(result)

    def __str__(self) -> str:
        """Pretty print the packet"""
        return (
            f"YSDP Packet:\n"
            f"  Base Protocol: {self.base_proto_name}\n"
            f"  Message Length: {self.message_len} bytes\n"
            f"  Magic Bytes: {self.magic_bytes.hex()}\n"
            f"  IP Address: {self.ip_address}\n"
            f"  MAC Address: {self.mac_address}\n"
            f"  Protocol Name: {self.proto_name}\n"
            f"  Device Info:\n"
            f"    Manufacturer: {self.data.manufacturer}\n"
            f"    Model: {self.data.device_model}\n"
            f"    Device ID: {self.data.device_id}\n"
            f"    Device Name: {self.data.device_name}"
        )
