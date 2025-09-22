import noisereduce as nr
import torch

device = torch.device("cpu")


def apply_noise_reduction(data):
    audio_frame = data[1]  # mono

    return nr.reduce_noise(
        y=audio_frame,
        sr=48000,
        n_std_thresh_stationary=1.5,
        stationary=True,
        use_torch=True,
        device=device,
    )
