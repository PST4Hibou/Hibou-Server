from src.settings import SETTINGS
from src.modules.audio.streaming import GstChannel

import sounddevice as sd


def play_sample(channels: list[GstChannel], channel_id=1):
    sd.play(channels[channel_id], samplerate=SETTINGS.AUDIO_REC_HZ, blocking=False)
