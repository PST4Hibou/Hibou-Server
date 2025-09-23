#!/bin/python3
from src.processing.noise_reduction import apply_noise_reduction
from src.audio.gstreamer_source import GStreamerAudioSource
from src.audio.file_source import FileAudioSource
from src.audio.audio import AudioInputManager
from src.devices.devices import AudioDevice
from src.settings import SETTINGS
import sounddevice as sd


def play_sample(channels: list[float], channel_id=1):
    sd.play(channels[channel_id], samplerate=SETTINGS.REC_HZ, blocking=False)


def audio_processing(channels: list[float]):
    enhanced_audio = apply_noise_reduction(channels)

    play_sample(enhanced_audio)  # Only for debug purposes


if __name__ == "__main__":
    print("Loaded settings: ", SETTINGS)

    devices = AudioDevice.load_devices(SETTINGS.DEVICES_CONFIG_PATH)

    source = GStreamerAudioSource(
        can_devices=devices,
        enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
        save_fp=SETTINGS.REC_SAVE_FP,
        record_duration=int(SETTINGS.REC_DURATION),
        rec_hz=int(SETTINGS.REC_HZ),
        stream_latency=int(SETTINGS.STREAM_LATENCY),
        net_iface=SETTINGS.NET_IFACE,
    )

    # source = FileAudioSource()

    manager = AudioInputManager(source)
    manager.on_data_ready = audio_processing

    try:
        source.start()
        print("Audio source started. Press Ctrl+C to stop.")
        while True:
            import time

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio...")
        source.stop()
