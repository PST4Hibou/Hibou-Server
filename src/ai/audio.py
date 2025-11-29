from pathlib import Path
from typing import Union
from src.logger import logger

from torch import nn
import torch

import librosa

import numpy as np

import importlib.util
import sys

from src.ai import has_cuda


def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class ModelProxy:
    def __init__(self, model_name: str = None):
        if not model_name:
            self._enable = False
            return

        self._enable = True
        self.model_name = model_name

        self._load_model()

    def _load_model(self):
        module = load_module(
            "./assets/models/" + self.model_name + ".py", "external_module"
        )
        self._model = module.Model()

        # We need to ensure that we put on CPU when CUDA's not
        # available, or we may trigger model load issues when the
        # model was previoulsy on GPU before save.
        state = (
            torch.load("./assets/models/" + self.model_name + ".pt")
            if has_cuda
            else torch.load(
                "./assets/models/" + self.model_name + ".pt",
                map_location=torch.device("cpu"),
            )
        )

        self._model.model.load_state_dict(state)
        self._model.model.eval()

    def infer(self, audios: list) -> np.ndarray:
        if not self._enable:
            return np.zeros(len(audios), dtype=int)

        predictions = self._model.infer(audios)
        return predictions
