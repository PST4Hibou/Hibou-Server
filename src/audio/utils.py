import numpy as np
import queue


def bytes_to_audio(raw_bytes):
    """
    Convert float 32 LE raw bytes to a normalized NumPy float32 array.

    Args:
        raw_bytes (bytes): Raw 32 LE float audio data.

    Returns:
        np.ndarray: 1D array of float32 samples in range [-1.0, 1.0].
    """
    # EOSs coming from the GST pipelines generates NaNs, that can be played as audio spikes,
    # and can also cause problems in the downstream code (e.g.: librosa can complain).
    # Thus, we need to remove them.
    return np.nan_to_num(np.frombuffer(raw_bytes, dtype=np.float32))


class MultiChannelQueue:
    """
    MultiChannelQueue for synchronizing data across channels.
    Methods of this class are thread safe.
    """

    def __init__(self, num_channels: int = None):
        """
        Initialize a MultiChannelQueue for synchronizing data across channels.

        Args:
            num_channels (int, optional): Number of channels to set up immediately. Defaults to None.
        """
        # Ready frames
        self._ready = queue.Queue()

        self.num_channels = num_channels
        if num_channels is not None:
            self.set_channels_count(num_channels)
        else:
            self._channel_queues = []

    def set_channels_count(self, num_channels: int):
        """
        Configure the number of channels for the queue.

        Args:
            num_channels (int): Number of audio/data channels to manage.
        """
        self.num_channels = num_channels
        # Per-channel FIFO queues
        self._channel_queues = [queue.Queue() for _ in range(num_channels)]

    def put(self, channel_id: int, data):
        """
        Insert data into the specified channel queue.
        When all channel queues contain at least one item,
        a complete frame is assembled and added to the ready queue.

        Args:
            channel_id (int): Index of the channel.
            data: Data sample to insert.
        """
        self._channel_queues[channel_id].put(data)
        # Check if all channels have at least one frame available
        if all(not q.empty() for q in self._channel_queues):
            # Collect one frame from each channel
            frame = [self._channel_queues[i].get() for i in range(self.num_channels)]
            self._ready.put(frame)

    def get(self, block: bool = True, timeout: int = None):
        """
        Retrieve the next completed multi-channel frame.

        Args:
            block (bool, optional): Whether to block until a frame is available. Defaults to True.
            timeout (int, optional): Timeout in seconds when blocking. Defaults to None.

        Returns:
            list: A list containing one data sample per channel.
        """
        return self._ready.get(block=block, timeout=timeout)

    def clear(self):
        """
        Clear all channel queues and the ready queue.
        Thread-safe.
        """
        self.set_channels_count(self.num_channels)
        self._ready = queue.Queue()

    def has_data(self):
        return not self._ready.empty()
