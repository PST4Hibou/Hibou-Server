import numpy as np
import random
import torch
from src.settings import SETTINGS


torch.manual_seed(SETTINGS.SEED)
np.random.seed(SETTINGS.SEED)
random.seed(SETTINGS.SEED)
