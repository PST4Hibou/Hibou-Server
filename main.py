from src.helpers.ipc import base_ipc
from src.helpers.ipc.zmqhandler import ZmqHandler
from src.logger import CustomLogger, update_global_log_level
from src.helpers.process_manager import managed_processes
from src.modules.decision.worker import DecisionWorker
from src.modules.vision.worker import VisionWorker
from src.helpers.decorators import SingletonMeta
from src.modules.audio.worker import AudioWorker
from src.settings import SETTINGS
from src.doctor import run_doctor
from src.arguments import args
import multiprocessing as mp
import time


def apply_arguments():
    if args.rec_duration:
        SETTINGS.AUDIO_CHUNK_DURATION = int(args.rec_duration) * 10**6
    if args.infer_from_folder:
        SETTINGS.INFER_FROM_FOLDER = args.infer_from_folder
    if args.log_level:
        SETTINGS.LOG_LEVEL = args.log_level
    update_global_log_level()

    if args.doctor:
        run_doctor()


logger = CustomLogger("main").get_logger()

if __name__ == "__main__":
    # Set the start method to spawn for multiprocessing
    mp.set_start_method("spawn")

    start_time = time.time()
    apply_arguments()

    
    base_ipc.get_ipc_handler().lifespan()

    """
    Start audio, vision and decision modules in separate processes.
    """
    try:
        with managed_processes(
            [
                # AudioWorker,
                # VisionWorker,
                DecisionWorker,
            ]
        ):
            pass
    except KeyboardInterrupt:
        logger.critical("\nStopping main process...")
    finally:
        SingletonMeta.clear()
