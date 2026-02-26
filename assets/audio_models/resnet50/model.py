from torchvision import models
from torch import nn
import torch
import librosa
import numpy as np

from src.settings import SETTINGS

device = "cuda" if torch.cuda.is_available() else "cpu"

model = models.resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, 1)
model = model.to(device)


def convert_to_mel_spectrogram(data):
    mel = librosa.feature.melspectrogram(
        y=data,
        sr=16000,
        n_fft=1025,
        hop_length=256,
        n_mels=128,
        fmin=20,
        fmax=8000,
        power=2.0,
    )
    # Convert to log scale (dB)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    # Normalize
    mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
    # Convert to torch tensor: [1, n_mels, time]
    mel_db = torch.tensor(mel_db).unsqueeze(0)

    return mel_db


def preprocess(audios: list):
    """
    Convert to melspectogram, repeat channels to match ResNet input,
    and pad sequences to the same length.
    """
    inputs = []
    for idx, audio in enumerate(audios):
        wave = convert_to_mel_spectrogram(audio)
        wave = wave.repeat(3, 1, 1)
        inputs.append(wave)

    inputs = torch.nn.utils.rnn.pad_sequence(inputs, batch_first=True).to(device=device)
    return inputs


class ResnetAudioModel:
    NAME = "resnet50"

    def __init__(self):
        self.model = model
        self.model.eval()
        self.threshold = 0.8
        self.model.load_state_dict(
            torch.load(
                f"{SETTINGS.AI_MODELS_FOLDER}{self.NAME}/model.pt", map_location=device
            )
        )
        self.model.eval()

    def infer(self, audios: list):
        """
        First preprocess the audio samples, then perform inference.
        Return binary predictions based on a threshold of 0.5.
        """
        inputs = preprocess(audios)
        with torch.no_grad():
            logits = self.model(inputs)
            predictions = torch.sigmoid(logits).squeeze(1).cpu().numpy()
            return predictions >= self.threshold


Model = lambda: ResnetAudioModel()
