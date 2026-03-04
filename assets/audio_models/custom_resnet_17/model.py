import torch
import librosa
import numpy as np

from src.settings import SETTINGS

device = "cuda" if torch.cuda.is_available() else "cpu"

from torch import nn


def norm(c):
    return nn.GroupNorm(num_groups=8, num_channels=c)


class SE(nn.Module):
    def __init__(self, c, r=8):
        super().__init__()
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(2),
            nn.Conv2d(c, c // r, kernel_size=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(c // r, c, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return x * self.fc(x)


class ResidualBlock(nn.Module):
    def __init__(self, in_c, out_c, stride=(1, 1)):
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_c, out_c, kernel_size=(5, 3), stride=stride, padding=(2, 1), bias=False
        )
        self.bn1 = norm(out_c)
        self.act = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv2d(
            out_c, out_c, kernel_size=(3, 3), stride=1, padding=1, bias=False
        )
        self.bn2 = norm(out_c)

        self.se = SE(out_c)

        self.shortcut = nn.Identity()
        if stride != (1, 1) or in_c != out_c:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_c, out_c, kernel_size=1, stride=stride, bias=False),
                norm(out_c),
            )

    def forward(self, x):
        out = self.act(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = self.se(out)
        out = out + self.shortcut(x)
        return self.act(out)


class AudioResNet(nn.Module):
    def __init__(self):
        super().__init__()

        # Stem: preserve time, reduce frequency
        self.conv1 = nn.Conv2d(
            1, 32, kernel_size=(5, 3), stride=(1, 2), padding=(2, 1), bias=False
        )
        self.bn1 = norm(32)
        self.act = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(kernel_size=(1, 3), stride=(1, 1), padding=(0, 1))

        # Residual stages (6 blocks total)
        self.layer1 = self._make_layer(32, 64, blocks=2, stride=(1, 2))
        self.layer2 = self._make_layer(64, 128, blocks=2, stride=(1, 1))
        self.layer3 = self._make_layer(128, 256, blocks=2, stride=(2, 2))

        self.dropout = nn.Dropout(0.2)

        # Pool frequency only
        self.freq_pool = nn.AdaptiveAvgPool2d((None, 1))

        # Temporal aggregation
        self.temporal = nn.Sequential(
            nn.Conv1d(256, 128, kernel_size=3, padding=1, bias=False),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool1d(1),
        )

        # Classifier
        self.fc = nn.Linear(128, 1)

    def _make_layer(self, in_c, out_c, blocks, stride):
        layers = [ResidualBlock(in_c, out_c, stride)]
        for _ in range(1, blocks):
            layers.append(ResidualBlock(out_c, out_c, stride=(1, 1)))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.act(self.bn1(self.conv1(x)))
        x = self.pool1(x)

        x = self.layer1(x)
        x = self.dropout(x)
        x = self.layer2(x)
        x = self.dropout(x)
        x = self.layer3(x)
        # x = self.dropout(x)

        # (B, C, T, F) -> pool F only
        x = self.freq_pool(x)
        x = x.squeeze(-1)  # (B, C, T)

        x = self.temporal(x)  # (B, 128, 1)
        x = x.squeeze(-1)

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


class CustomResnet17AudioModel:
    NAME = "custom_resnet_17"

    def __init__(self):
        self.model = AudioResNet().to(device)
        self.model.load_state_dict(
            torch.load(
                f"{SETTINGS.AI_MODELS_FOLDER}{self.NAME}/model.pt", map_location=device
            )
        )
        self.model.eval()
        self.threshold = 0.50

    def infer(self, audios: list):
        inputs = preprocess(audios)
        with torch.no_grad():
            logits = self.model(inputs)
            # print(logits)
            predictions = torch.sigmoid(logits).squeeze(1).cpu().numpy()
            print(predictions)
            return predictions >= self.threshold


Model = lambda: CustomResnet17AudioModel()
