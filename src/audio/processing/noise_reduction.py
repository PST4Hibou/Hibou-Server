from src.settings import SETTINGS
import noisereduce as nr
import torch


def apply_noise_reduction(channels: list[float]):

    for i in range(len(channels)):
        channels[i] = nr.reduce_noise(
            y=channels[i],
            sr=SETTINGS.REC_HZ,
            stationary=SETTINGS.STATIONARY,
            use_torch=True,
            device=torch.device(SETTINGS.DEVICE),
        )

    return channels
