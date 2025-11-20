import numpy as np
import random
import torch
from src.settings import SETTINGS
from src.logger import logger


torch.manual_seed(SETTINGS.SEED)
np.random.seed(SETTINGS.SEED)
random.seed(SETTINGS.SEED)

has_cuda = torch.cuda.is_available()
logger.info(f"CUDA usage with PyTorch: {"yes" if has_cuda else "no"}")
