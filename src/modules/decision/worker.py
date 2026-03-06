from src.logger import CustomLogger

import datetime
import os

logger = CustomLogger("decision").get_logger()

class DecisionWorker:
    def __init__(self, dt: datetime.datetime):
        logger.info(f"Started Decision Worker | PID: {os.getpid()}")
