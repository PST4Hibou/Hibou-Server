#!/bin/python3

from dotenv import load_dotenv
from audio import AudioInputManager
import time

if __name__ == "__main__":
    load_dotenv()

    mgr = AudioInputManager.createFromEnv();
    mgr.start()
    time.sleep(30)
    mgr.stop()
