#!/bin/python3

from dotenv import load_dotenv
from audio import AudioInputManager
import time

if __name__ == "__main__":
    load_dotenv()

    mgr = AudioInputManager.create_from_env()
    mgr.start()
    time.sleep(30)
    mgr.stop()
