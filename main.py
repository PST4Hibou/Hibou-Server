#!/bin/python3

from noise_reduction import apply_noise_reduction
from audio import AudioInputManager
from dotenv import load_dotenv
import sounddevice as sd
import time

def audio_processing(data):
    audios = apply_noise_reduction(data)

    sd.play(audios, samplerate=48000, blocking=False)

if __name__ == "__main__":
    loaded = load_dotenv()
    if not loaded:
        print("No .env file found please create one.")
        exit(1)

    mgr = AudioInputManager.create_from_env()
    mgr.on_data_ready = audio_processing
    mgr.start()
    time.sleep(30)
    mgr.stop()
