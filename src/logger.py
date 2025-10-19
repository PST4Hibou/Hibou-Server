from src.settings import SETTINGS
import logging.config
import os
import colorlog

# Make sure the logs directory exists
os.makedirs(os.path.dirname(SETTINGS.LOG_PATH), exist_ok=True)

logging.config.fileConfig(
    SETTINGS.LOG_CONF_PATH,
    defaults={"logfilename": SETTINGS.LOG_PATH},
    disable_existing_loggers=False,
)

root_logger = logging.getLogger()
root_logger.setLevel(SETTINGS.LOG_LEVEL)

# Default format if nothing found
fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
# Remove only Console handler
for handler in root_logger.handlers:
    if not isinstance(handler, logging.FileHandler) and isinstance(
        handler, logging.StreamHandler
    ):
        fmt = handler.formatter._fmt
        root_logger.removeHandler(handler)

ch = logging.StreamHandler()
ch.setLevel(SETTINGS.LOG_LEVEL)

formatter = colorlog.ColoredFormatter(
    "%(log_color)s" + fmt,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)

ch.setFormatter(formatter)
root_logger.addHandler(ch)


def blank_line_module(log_level="DEBUG", how_many_lines=1):
    if SETTINGS.LOG_LEVEL == log_level:
        for _ in range(how_many_lines):
            print("")


logging.blank_line = blank_line_module
logger = logging.getLogger(__name__)

# external logger
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("matplotlib").setLevel(logging.CRITICAL)
logging.getLogger("netaudio").setLevel(logging.CRITICAL)
