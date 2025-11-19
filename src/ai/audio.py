from pathlib import Path
from typing import Union

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

def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def convert_to_linear_spectrogram(audios: list):
    return [torch.tensor(librosa.amplitude_to_db(np.abs(librosa.stft(np.array(a, dtype=np.float32), n_fft=2048, hop_length=512)), ref=np.max)) for a in audios]


class ModelProxy:
    def __init__(self, model_name: str = None):
        if not model_name:
            self._enable = False
            return

        self._enable = False

        module = load_module("./assets/models/" + model_name + ".py", "external_module")
        self._model = module.ModelBuilder()

        if torch.cuda.is_available():
            self._model.load_state_dict(torch.load("./assets/models/" + model_name + ".pt"))
            if torch.cuda.device_count() > 1:
                self._model = nn.DataParallel(self._model)
            self._model.to("cuda")
        else:
            self._model.load_state_dict(torch.load("./assets/models/" + model_name + ".pt", map_location=torch.device("cpu")))

        self._model.eval()
        self._disables = torch.no_grad()

    def infer(self, audios: list):
        if self._enable:
            inputs = convert_to_linear_spectrogram(audios)
            print([torch.argmax(self._model(i), dim=1) for i in inputs])
