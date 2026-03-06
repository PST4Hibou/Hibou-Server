import time
import datetime
from src.logger import CustomLogger

logger = CustomLogger("decision").get_logger()
import os


class DecisionWorker:
    def __init__(self, dt: datetime.datetime):
        logger.info(f"Started Decision Worker | PID: {os.getpid()}")

        while True:
            print("Decision Worker is running...")
            time.sleep(5)
