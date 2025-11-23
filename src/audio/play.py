from src.settings import SETTINGS
from src.audio import Channel

import sounddevice as sd


def play_sample(channels: list[Channel], channel_id=1):
    sd.play(channels[channel_id], samplerate=SETTINGS.AUDIO_REC_HZ, blocking=False)
