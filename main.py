#!/bin/python3

from src.processing.noise_reduction import apply_noise_reduction
from src.audio.audio import AudioInputManager
from src.settings import SETTINGS
import sounddevice as sd
import time


def audio_processing(data):
    audios = apply_noise_reduction(data)

    sd.play(audios, samplerate=SETTINGS.REC_HZ, blocking=False)


if __name__ == "__main__":
    print("Loaded settings: ", SETTINGS)
    mgr = AudioInputManager.create_from_env()
    mgr.on_data_ready = audio_processing
    mgr.start()
    time.sleep(30)
    mgr.stop()
