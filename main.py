#!/bin/python3

from noise_reduction import apply_noise_reduction
from audio import AudioInputManager
from settings import SETTINGS
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
