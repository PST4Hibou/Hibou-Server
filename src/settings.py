from dataclasses import dataclass
from dotenv import load_dotenv
import os

if not load_dotenv():
    print("No .env file found. Please create one.")
    exit(1)


@dataclass
class Settings:
    ENABLE_REC_SAVE: bool
    REC_SAVE_FP: str
    REC_DURATION: int  # in nanoseconds
    REC_HZ: int
    STREAM_LATENCY: int
    DEVICES_CONFIG_PATH: str
    STATIONARY: bool
    DEVICE: str
    LOG_PATH: str
    LOG_CONF_PATH: str
    LOG_LEVEL: str
    INFER_FROM_FOLDER: str
    AUDIO_VOLUME: int


def parse_list(value: str):
    """Split a comma-separated string and strip whitespace."""
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_bool(value: str) -> bool:
    """Parse a boolean from string (True/False, yes/no)."""
    return str(value).strip().lower() in ("true", "1", "yes")


SETTINGS = Settings(
    ENABLE_REC_SAVE=parse_bool(os.getenv("ENABLE_REC_SAVE")),
    REC_SAVE_FP=os.getenv("REC_SAVE_FP"),
    REC_DURATION=int(os.getenv("REC_DURATION")) * 10**6,  # ns
    REC_HZ=int(os.getenv("REC_HZ")),
    STREAM_LATENCY=int(os.getenv("STREAM_LATENCY")),
    DEVICES_CONFIG_PATH=os.getenv("DEVICES_CONFIG_PATH"),
    STATIONARY=parse_bool(os.getenv("STATIONARY")),
    DEVICE=os.getenv("DEVICE"),
    LOG_PATH=os.getenv("LOG_PATH"),
    LOG_CONF_PATH=os.getenv("LOG_CONF_PATH"),
    LOG_LEVEL=os.getenv("LOG_LEVEL"),
    INFER_FROM_FOLDER=os.getenv("INFER_FROM_FOLDER"),
    AUDIO_VOLUME=int(os.getenv("AUDIO_VOLUME")),
)
