from torchvision import models
from torch import nn
import torch
import librosa
import numpy as np

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

model = models.resnet50(weights=None)

# Replace final FC for binary classification
model.fc = nn.Linear(model.fc.in_features, 1)
model = model.to(DEVICE)


def convert_to_linear_spectrogram(audios: list):
    return torch.stack(
        [
            torch.tensor(
                librosa.amplitude_to_db(
                    np.abs(
                        librosa.stft(
                            np.array(a, dtype=np.float32), n_fft=2048, hop_length=512
                        )
                    ),
                    ref=np.max,
                )
            ).unsqueeze(0)
            for a in audios
        ]
    )


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


def process_resnet(audios: list):
    inputs = []
    for audio in audios:
        wave = convert_to_mel_spectrogram(audio)
        wave = wave.repeat(3, 1, 1)
        inputs.append(wave)

    inputs = torch.nn.utils.rnn.pad_sequence(inputs, batch_first=True).to(
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

    return inputs


ModelBuilder = lambda: model
ModelProcess = lambda: process_resnet
