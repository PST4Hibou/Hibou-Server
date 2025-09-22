#!/bin/python3

from dotenv import load_dotenv
from audio import AudioInputManager
import time

if __name__ == "__main__":
    loaded = load_dotenv()
    if not loaded:
        print("No ..env file found please create one.")
        exit(1)

    mgr = AudioInputManager.create_from_env()
    mgr.start()
    time.sleep(30)
    mgr.stop()
