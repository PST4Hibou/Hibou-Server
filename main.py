#!/bin/python3
from src.audio.file_source import FileAudioSource
from src.audio.gstreamer_source import GStreamerAudioSource
from src.processing.noise_reduction import apply_noise_reduction
from src.audio.audio import AudioInputManager
from src.settings import SETTINGS
import sounddevice as sd


def play_sample(audio):
    sd.play(audio, samplerate=SETTINGS.REC_HZ, blocking=False)


def audio_processing(data):
    enhanced_audio = apply_noise_reduction(data)

    play_sample(enhanced_audio)

    return enhanced_audio


if __name__ == "__main__":
    print("Loaded settings: ", SETTINGS)

    source = GStreamerAudioSource(
        pipeline_ports=SETTINGS.SOURCE_PORTS,
        enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
        save_fp=SETTINGS.REC_SAVE_FP,
        record_duration=int(SETTINGS.REC_DURATION),
        rec_hz=int(SETTINGS.REC_HZ),
        stream_latency=int(SETTINGS.STREAM_LATENCY),
        net_iface=SETTINGS.NET_IFACE,
        rtp_payloads=SETTINGS.RTP_PAYLOADS,
        ip_addresses=SETTINGS.MULTICAST_IPS,
    )

    # source = FileAudioSource()

    manager = AudioInputManager(source)
    manager.on_data_ready = audio_processing
    manager.start()
