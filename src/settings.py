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
        "ENABLE_REC_SAVE",
        "REC_SAVE_FP",
        "REC_DURATION",
        "REC_HZ",
        "STREAM_LATENCY",
        "NET_IFACE",
        "DEVICES_CONFIG_PATH",
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
        ENABLE_REC_SAVE=parse_bool(os.getenv("ENABLE_REC_SAVE")),
        REC_SAVE_FP=os.getenv("REC_SAVE_FP"),
        REC_DURATION=int(os.getenv("REC_DURATION")) * 10**6,  # ns
        REC_HZ=int(os.getenv("REC_HZ")),
        STREAM_LATENCY=int(os.getenv("STREAM_LATENCY")),
        NET_IFACE=os.getenv("NET_IFACE"),
        DEVICES_CONFIG_PATH=os.getenv("DEVICES_CONFIG_PATH"),
        STATIONARY=parse_bool(os.getenv("STATIONARY")),
        DEVICE=os.getenv("DEVICE"),
    )


SETTINGS = load_settings()
