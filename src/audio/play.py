from src.audio.models.channel import Channel
from src.settings import SETTINGS

import sounddevice as sd


def play_sample(channels: list[Channel], channel_id=1):
    sd.play(channels[channel_id], samplerate=SETTINGS.REC_HZ, blocking=False)
