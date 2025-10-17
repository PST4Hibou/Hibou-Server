from src.settings import SETTINGS
import logging.config

logging.config.fileConfig(
    SETTINGS.LOG_CONF_PATH,
    defaults={"logfilename": SETTINGS.LOG_PATH},
    disable_existing_loggers=False,
)

root_logger = logging.getLogger()
root_logger.setLevel(SETTINGS.LOG_LEVEL)


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
