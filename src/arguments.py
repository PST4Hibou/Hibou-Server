import argparse
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


def gst_dbg_level_validator(level: str):
    if not hasattr(Gst.DebugLevel, level):
        raise argparse.ArgumentTypeError(f"Invalid debug level: {level}")

    return getattr(Gst.DebugLevel, level)


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
parser.add_argument(
    "--channel-prefix",
    default="",
    help="Set the save/read channel directory name prefix",
    type=str,
)
parser.add_argument(
    "--channel-count",
    default=4,
    help="Set the number of channels. This used only when --infer-from-folder is set.",
    type=int,
)
parser.add_argument(
    "--gst-dbg-level",
    default="NONE",
    help="Set the GStreamer debug level. See https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html",
    type=gst_dbg_level_validator,
)
parser.add_argument(
    "--audio-model",
    default="",
    help="Model to use for audio detection. The .pt and .py files must be put in ./assets/models",
    type=str,
)

args = parser.parse_args()
