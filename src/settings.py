from dataclasses import dataclass
from dotenv import load_dotenv

import logging
import shutil
import os


current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)
project_root = os.path.abspath(os.path.join(script_dir, ".."))

# Paths
source_file = os.path.join(project_root, ".env.exemple")
target_file = os.path.join(project_root, ".env")

# Copy .env if it does not exist
if not os.path.exists(target_file) and os.path.exists(source_file):
    shutil.copy2(source_file, target_file)
    logging.info(f"Copied {source_file} → {target_file}")

if not load_dotenv():
    raise FileNotFoundError("Failed to load .env file.")


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
    PTZ_USERNAME: str
    PTZ_PASSWORD: str
    PTZ_HOST: str
    PTZ_VIDEO_CHANNEL: int
    PTZ_RTSP_PORT: int
    PTZ_START_AZIMUTH: int
    PTZ_END_AZIMUTH: int
    AUDIO_ANGLE_COVERAGE: int
    AUDIO_PLAYBACK: bool = False  # Only for debug purposes
    AUDIO_ENERGY_SPECTRUM: bool = False  # Only for debug purposes
    AUDIO_RADAR: bool = False  # Only for debug purposes
    CV_VIDEO_PLAYBACK: bool = False  # Only for debug purposes


def parse_list(value: str):
    """Split a comma-separated string and strip whitespace."""
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_bool(value: str) -> bool:
    """Parse a boolean from string (True/False, yes/no)."""
    return str(value).strip().lower() in ("true", "1", "yes")


try:
    if Settings.CV_VIDEO_PLAYBACK and (
        Settings.AUDIO_RADAR or Settings.AUDIO_ENERGY_SPECTRUM
    ):
        logging.warning(
            "Both CV video and audio visualization are enabled. Disabling CV video."
        )
        Settings.CV_VIDEO_PLAYBACK = False

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
        PTZ_USERNAME=os.getenv("PTZ_USERNAME"),
        PTZ_PASSWORD=os.getenv("PTZ_PASSWORD"),
        PTZ_HOST=os.getenv("PTZ_HOST"),
        PTZ_VIDEO_CHANNEL=int(os.getenv("PTZ_VIDEO_CHANNEL")),
        PTZ_RTSP_PORT=int(os.getenv("PTZ_RTSP_PORT")),
        AUDIO_ANGLE_COVERAGE=int(os.getenv("AUDIO_ANGLE_COVERAGE")),
        PTZ_START_AZIMUTH=int(os.getenv("PTZ_START_AZIMUTH")),
        PTZ_END_AZIMUTH=int(os.getenv("PTZ_END_AZIMUTH")),
    )
except TypeError as e:
    raise ValueError(f"Invalid value in .env: {e}. Please check the .env file.")
