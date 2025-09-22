from collections import namedtuple
from dotenv import load_dotenv
import os

if not load_dotenv():
    print("No .env file found. Please create one.")
    exit(1)

# Namedtuple definition
Settings = namedtuple(
    "Settings",
    [
        "SOURCE_PORTS",
        "RTP_PAYLOADS",
        "ENABLE_REC_SAVE",
        "REC_SAVE_FP",
        "REC_DURATION",
        "REC_HZ",
        "STREAM_LATENCY",
        "NET_IFACE",
        "MULTICAST_IPS",
        "STATIONARY",
        "DEVICE",
    ],
)


def parse_list(value: str):
    """Split a comma-separated string and strip whitespace."""
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_bool(value: str) -> bool:
    """Parse a boolean from string (True/False, yes/no)."""
    return str(value).strip().lower() in ("true", "1", "yes")


def load_settings() -> Settings:
    return Settings(
        SOURCE_PORTS=parse_list(os.getenv("SOURCE_PORTS", "5004")),
        RTP_PAYLOADS=parse_list(os.getenv("RTP_PAYLOADS", "98")),
        ENABLE_REC_SAVE=parse_bool(os.getenv("ENABLE_REC_SAVE", "true")),
        REC_SAVE_FP=os.getenv("REC_SAVE_FP", "./recs"),
        REC_DURATION=int(os.getenv("REC_DURATION", "1000")) * 10**6,  # ns
        REC_HZ=int(os.getenv("REC_HZ", "48000")),
        STREAM_LATENCY=int(os.getenv("STREAM_LATENCY", "50")),
        NET_IFACE=os.getenv("NET_IFACE", "enp2s0"),
        MULTICAST_IPS=parse_list(os.getenv("MULTICAST_IPS", "192.168.250.255")),
        STATIONARY=parse_bool(os.getenv("STATIONARY", "true")),
        DEVICE=os.getenv("DEVICE", "cpu"),
    )


SETTINGS = load_settings()
