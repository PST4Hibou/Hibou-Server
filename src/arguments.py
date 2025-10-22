from src.ptz.calibration import start_ptz_calibration
from src.settings import SETTINGS
from src.doctor import run_doctor

import argparse

parser = argparse.ArgumentParser(
    prog="Hibou",
    description="Hibou Drone Acoustic Detection",
)

parser.add_argument("--rec-duration", help="In milliseconds", type=int)
parser.add_argument("--infer-from-folder", help="Use a folder to infer", type=str)
parser.add_argument(
    "--log-level", help="Change log level from ERROR to DEBUG", type=str
)
parser.add_argument("--doctor", action="store_true", help="Run doctor")
parser.add_argument(
    "--ptz-calibration", action="store_true", help="Run PTZ calibration"
)

args = parser.parse_args()

if args.rec_duration:
    SETTINGS.REC_DURATION = int(args.rec_duration) * 10**6
if args.infer_from_folder:
    SETTINGS.INFER_FROM_FOLDER = args.infer_from_folder
if args.log_level:
    SETTINGS.LOG_LEVEL = args.log_level
if args.doctor:
    run_doctor()
if args.ptz_calibration:
    start_ptz_calibration()
