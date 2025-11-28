from torchvision import models
from torch import nn
import torch
import librosa
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"

"""
Model Declaration
"""
model = models.resnet50(weights=None)
# Replace final FC for binary classification
model.fc = nn.Linear(model.fc.in_features, 1)
model = model.to(device)

"""
Preprocessing and Inference
"""


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


#
def convert_to_mel_spectrogram(data):
    # Compute mel power spectrogram
    mel = librosa.feature.melspectrogram(
        y=data,
        sr=16000,
        n_fft=1024,
        hop_length=256,
        n_mels=128,
        fmin=20,
        fmax=8000,
        power=2.0,
    )

    # 1. Avoid zeros -> prevent log10(0) = -inf
    mel = np.maximum(mel, 1e-9)

    # 2. Convert to dB manually (safer than power_to_db)
    mel_db = 10.0 * np.log10(mel)

    # 3. Replace any remaining inf
    mel_db = np.nan_to_num(mel_db, neginf=-100.0, posinf=100.0)

    # 4. Safe normalization
    mean = mel_db.mean()
    std = mel_db.std()

    # Prevent division by 0
    if std < 1e-6:
        std = 1e-6

    mel_db = (mel_db - mean) / std

    # Convert to torch: [1, n_mels, time]
    mel_db = torch.tensor(mel_db, dtype=torch.float32).unsqueeze(0)

    return mel_db


# def convert_to_mel_spectrogram(data):
#     mel = librosa.feature.melspectrogram(
#         y=data,
#         sr=16000,
#         n_fft=1025,
#         hop_length=256,
#         n_mels=128,
#         fmin=20,
#         fmax=8000,
#         power=2.0,
#     )
#     # Convert to log scale (dB)
#     mel_db = librosa.power_to_db(mel, ref=np.max)
#     # Normalize
#     mel_db = (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)
#     # Convert to torch tensor: [1, n_mels, time]
#     mel_db = torch.tensor(mel_db).unsqueeze(0)
#
#     return mel_db


def preprocess(audios: list):
    """
    Convert to melspectogram, repeat channels to match ResNet input,
    and pad sequences to the same length.
    """
    inputs = []
    for idx, audio in enumerate(audios):
        # # Debug: Print audio characteristics
        # print(f"\n[Preprocess Debug #{idx}]")
        # print(f"  dtype: {audio.dtype}")
        # print(f"  shape: {np.array(audio).shape}")
        # print(f"  min: {np.min(audio):.6f}, max: {np.max(audio):.6f}")
        # print(f"  mean: {np.mean(audio):.6f}, std: {np.std(audio):.6f}")
        # print(f"  abs_max: {np.max(np.abs(audio)):.6f}")

        wave = convert_to_mel_spectrogram(audio)

        # # Debug: Print mel spectrogram characteristics
        # print(f"  mel shape: {wave.shape}")
        # print(f"  mel mean: {wave.mean():.2f}, mel std: {wave.std():.2f}")

        wave = wave.repeat(3, 1, 1)
        inputs.append(wave)
    inputs = torch.nn.utils.rnn.pad_sequence(inputs, batch_first=True).to(device=device)
    return inputs


class ResnetAudioModel:
    def __init__(self):
        self.model = model
        self.threshold = 0.5

    def infer(self, audios: list):
        """
        First preprocess the audio samples, then perform inference.
        Return binary predictions based on a threshold of 0.5.
        """
        inputs = preprocess(audios)
        with torch.no_grad():
            logits = self.model(inputs)
            # print(logits)
            predictions = torch.sigmoid(logits).squeeze(1).cpu().numpy()
            # print(predictions)
            return predictions >= self.threshold


Model = lambda: ResnetAudioModel()
