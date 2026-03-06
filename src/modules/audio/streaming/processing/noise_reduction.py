from noisereduce.torchgate import TorchGate as TG
from src.settings import SETTINGS
import noisereduce as nr
import torch


def apply_noise_reduction(channels: list[float]):

    for i in range(len(channels)):
        channels[i] = nr.reduce_noise(
            y=channels[i],
            sr=SETTINGS.AUDIO_REC_HZ,
            stationary=SETTINGS.STATIONARY,
            use_torch=True,
            device=torch.device(SETTINGS.AI_DEVICE),
        )

    return channels


def apply_noise_reduction_torch(channels: list[float]):
    tg = TG(sr=SETTINGS.AUDIO_REC_HZ, nonstationary=True).to(
        torch.device(SETTINGS.AI_DEVICE)
    )

    # Apply Spectral Gate to noisy speech signal
    # noisy_speech = torch.randn(3, 32000, device=torch.device(SETTINGS.DEVICE))
    return tg(channels)
