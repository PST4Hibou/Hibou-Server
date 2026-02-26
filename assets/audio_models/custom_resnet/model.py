import torch
import librosa
import numpy as np

from src.settings import SETTINGS

device = "cuda" if torch.cuda.is_available() else "cpu"

from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(
            in_channels, out_channels, kernel_size=3, stride=stride, padding=1
        )
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.prelu = nn.PReLU()
        self.conv2 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, stride=1, padding=1
        )
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x):
        out = self.prelu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = self.prelu(out)
        return out


class AudioResNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=5, stride=(2, 1), padding=2)
        self.bn1 = nn.BatchNorm2d(32)
        self.prelu = nn.PReLU()
        self.pool1 = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = ResidualBlock(32, 64, stride=2)
        self.layer2 = ResidualBlock(64, 128, stride=2)
        self.layer3 = ResidualBlock(128, 256, stride=2)

        self.pool2 = nn.AdaptiveAvgPool2d((1, 1))

        self.fc = nn.Sequential(
            nn.Linear(256, 128), nn.PReLU(), nn.Dropout(0.5), nn.Linear(128, 1)
        )

    def forward(self, x):
        x = self.pool1(self.prelu(self.bn1(self.conv1(x))))
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.pool2(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


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
        inputs.append(wave)

    inputs = torch.nn.utils.rnn.pad_sequence(inputs, batch_first=True).to(device=device)
    return inputs


class CustomResnetAudioModel:
    NAME = "custom_resnet"

    def __init__(self):
        self.model = AudioResNet().to(device)
        self.threshold = 0.5
        self.model.load_state_dict(
            torch.load(
                f"{SETTINGS.AI_MODELS_FOLDER}{self.NAME}/model.pt", map_location=device
            )
        )
        self.model.eval()
        self.threshold = 0.80

    def infer(self, audios: list):
        inputs = preprocess(audios)
        with torch.no_grad():
            logits = self.model(inputs)
            # print(logits)
            predictions = torch.sigmoid(logits).squeeze(1).cpu().numpy()
            print(predictions)
            return predictions >= self.threshold


Model = lambda: CustomResnetAudioModel()
