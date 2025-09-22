from src.settings import SETTINGS
import noisereduce as nr
import torch


def apply_noise_reduction(audios):
    audio_frame = audios[1]  # mono

    return nr.reduce_noise(
        y=audio_frame,
        sr=SETTINGS.REC_HZ,
        stationary=SETTINGS.STATIONARY,
        use_torch=True,
        device=torch.device(SETTINGS.DEVICE),
    )
