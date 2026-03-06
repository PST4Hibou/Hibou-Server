from src.modules.audio.streaming import GstChannel


def compute_energy(channel: GstChannel):
    return sum(s**2 for s in channel[0])
