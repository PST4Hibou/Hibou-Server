from pathlib import Path
from typing import Union
from src.logger import logger

from torch.utils.data import DataLoader
from torch import nn, optim, Tensor
import torch.nn.functional as F
import torch

import torchaudio.transforms as T
import torchaudio
import torchcodec
import librosa

import numpy as np

from tqdm import tqdm
from sys import path

import importlib.util
import sys

from src.ai import has_cuda


def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def convert_to_linear_spectrogram(audios: list):
    return torch.stack([torch.tensor(librosa.amplitude_to_db(np.abs(librosa.stft(np.array(a, dtype=np.float32), n_fft=2048, hop_length=512)), ref=np.max)).unsqueeze(0) for a in audios])


class ModelProxy:
    def __init__(self, model_name: str = None):
        if not model_name:
            self._enable = False
            return

        self._enable = True
        self.is_src_parallel = False
        self.model_name = model_name

        self._load_model()

        self._disables = torch.no_grad()

    def _load_model(self):
        module = load_module("./assets/models/" + self.model_name + ".py", "external_module")
        self._model = module.ModelBuilder()

        # We need to ensure that we put on CPU when CUDA's not
        # available, or we may trigger model load issues when the
        # model was previoulsy on GPU before save.
        state = torch.load("./assets/models/" + self.model_name + ".pt") if has_cuda else torch.load("./assets/models/" + self.model_name + ".pt", map_location=torch.device("cpu"))

        # Detect if DataParallel was used
        self.is_src_parallel = any(k.startswith("module.") for k in state.keys())
        self._model.load_state_dict(state)

        if has_cuda:
            if torch.cuda.device_count() > 1:
                self._model = nn.DataParallel(self._model)
                logger.info(f"Enabled parallel data processing for '{self.model_name}' model.")
            self._model.to("cuda")

        self._model.eval()

    def infer(self, audios: list):
        if self._enable:
            return torch.argmax(self._model(convert_to_linear_spectrogram(audios)), dim=1).numpy()

        return np.zeros(len(audios), dtype=int)
