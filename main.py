#!/bin/python3
from src.audio.sources.file_source import FileAudioSource
from src.audio.sources.rtp_source import RTPAudioSource
from src.devices.devices import AudioDevice
from src.settings import SETTINGS
from src.logger import logger
import sounddevice as sd


def play_sample(channels: list[float], channel_id=1):
    sd.play(channels[channel_id], samplerate=SETTINGS.REC_HZ, blocking=False)


def audio_processing(channels: list[float]):
    # enhanced_audio = apply_noise_reduction(channels)

    play_sample(channels, 0)  # Only for debug purposes


if __name__ == "__main__":
    logger.debug(f"Loaded settings: {SETTINGS}")
    devices = AudioDevice.load_devices(SETTINGS.DEVICES_CONFIG_PATH)

    logger.info(f"{len(devices)} devices loaded...")
    logger.debug(f"Devices: {devices}")

    source = RTPAudioSource(
        devices=devices,
        enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
        save_fp=SETTINGS.REC_SAVE_FP,
        record_duration=int(SETTINGS.REC_DURATION),
        rec_hz=int(SETTINGS.REC_HZ),
        stream_latency=int(SETTINGS.STREAM_LATENCY),
    )

    # source = FileAudioSource(
    #     folder_path="./in",
    #     channel_prefix="ch_",
    #     channels_count=4,
    #     save_fp=SETTINGS.REC_SAVE_FP,
    #     enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
    #     record_duration=SETTINGS.REC_DURATION,
    # )

    source.set_callback(audio_processing)

    try:
        source.start()
        print("Audio source started. Press Ctrl+C to stop.")
        while True:
            import time

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio...")
        source.stop()
