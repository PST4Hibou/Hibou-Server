from torch import nn
import torch
import librosa
import numpy as np
import timm

from src.settings import SETTINGS

device = "cuda" if torch.cuda.is_available() else "cpu"
VIT_MODEL = "vit_base_patch16_224"
NUM_CLASSES = 1
PRETRAINED = True
FREEZE_BACKBONE = False
SPEC_HEIGHT = 128
SPEC_WIDTH = 256


class SpectrogramViT(nn.Module):
    def __init__(
        self,
        model_name: str = VIT_MODEL,
        num_classes: int = NUM_CLASSES,
        img_size: tuple = (SPEC_HEIGHT, SPEC_WIDTH),
        pretrained: bool = PRETRAINED,
        freeze_backbone: bool = FREEZE_BACKBONE,
    ):
        super().__init__()
        self.channel_expand = nn.Conv2d(1, 3, kernel_size=1, bias=False)

        self.vit = timm.create_model(
            model_name,
            pretrained=pretrained,
            num_classes=num_classes,
            img_size=img_size,
            in_chans=3,
        )

        if freeze_backbone:
            for name, param in self.vit.named_parameters():
                if "head" not in name:
                    param.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x : [B, 1, H, W]  →  logits : [B, num_classes]"""
        x = self.channel_expand(x)  # [B, 3, H, W]
        return self.vit(x)


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


def resize_spec(spec: torch.Tensor, height: int, width: int) -> torch.Tensor:
    spec = spec.unsqueeze(0)
    spec = torch.nn.functional.interpolate(
        spec,
        size=(height, width),
        mode="bilinear",
        align_corners=False,
    )
    return spec.squeeze(0)


def preprocess(audios: list):
    inputs = []
    for idx, audio in enumerate(audios):
        mel_tensor = convert_to_mel_spectrogram(audio)
        x = resize_spec(mel_tensor, SPEC_HEIGHT, SPEC_WIDTH).unsqueeze(0).to(device)
        inputs.append(x)

    return inputs


class VitAudioModel:
    NAME = "vit_base_patch16_224"

    def __init__(self):
        self.model = SpectrogramViT().to(device)
        self.threshold = 0.5
        self.model.load_state_dict(
            torch.load(
                f"{SETTINGS.AI_MODELS_FOLDER}{self.NAME}/model.pt", map_location=device
            )["model_state_dict"]
        )
        self.model.eval()

    def infer(self, audios: list):
        inputs = preprocess(audios)
        predictions = []

        with torch.no_grad():
            for input in inputs:
                logits = self.model(input)
                predictions.append(torch.sigmoid(logits).cpu().squeeze(0).squeeze(0))

        return [pred >= self.threshold for pred in predictions]


Model = lambda: VitAudioModel()
