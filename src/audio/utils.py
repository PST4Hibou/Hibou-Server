import numpy as np


def bytes_to_audio(raw_bytes):
    """
    Convert 24-bit PCM raw bytes to a normalized NumPy float32 array.

    Args:
        raw_bytes (bytes): Raw 24-bit PCM audio data.

    Returns:
        np.ndarray: 1D array of float32 samples in range [-1.0, 1.0].
    """
    # Convert bytes to 1D array of uint8
    byte_array = np.frombuffer(raw_bytes, dtype=np.uint8)

    # Reshape to N x 3 bytes (24-bit samples)
    samples_24bit = byte_array.reshape(-1, 3)

    # Convert to 32-bit integers
    # Little-endian L24 -> int32
    # Pad the most significant byte (sign extend)
    samples_32bit = np.zeros((samples_24bit.shape[0],), dtype=np.int32)
    # Transform each 3 btes-per-bytes to uint32 by performing shift on each 0th,
    # 1st and 2nd following bytes of each seq of 3 elems.
    samples_32bit[:] = (
        samples_24bit[:, 0].astype(np.int32)
        | (samples_24bit[:, 1].astype(np.int32) << 8)
        | (samples_24bit[:, 2].astype(np.int32) << 16)
    )

    # Sign extension for negative numbers
    samples_32bit[samples_32bit >= 0x800000] -= 0x1000000

    return samples_32bit.astype(np.float32) / (2**23)  # 24-bit signed
