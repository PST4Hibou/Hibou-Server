import logging.config
from src.settings import SETTINGS

logging.config.fileConfig(
    SETTINGS.LOG_CONF_PATH,
    defaults={"logfilename": SETTINGS.LOG_PATH},
    disable_existing_loggers=False,
)

root_logger = logging.getLogger()
root_logger.setLevel(SETTINGS.LOG_LEVEL)

logger = logging.getLogger(__name__)
