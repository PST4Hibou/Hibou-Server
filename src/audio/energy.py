from src.audio import Channel


def compute_energy(samples: Channel):
    # samples: a 1D array of N values (floats)
    return sum(s**2 for s in samples)


def compute_rms(samples):
    N = len(samples)
    E = compute_energy(samples)
    return (E / N) ** 0.5
