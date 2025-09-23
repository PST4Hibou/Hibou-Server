import queue
import threading


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
        self.lock = threading.Lock()
        # Ready frames
        self.ready = queue.Queue()

        if num_channels is not None:
            self.set_channels_count(num_channels)

    def set_channels_count(self, num_channels: int):
        """
        Configure the number of channels for the queue.

        Args:
            num_channels (int): Number of audio/data channels to manage.
        """
        self.num_channels = num_channels
        # Per-channel FIFO queues
        self.channel_queues = [queue.Queue() for _ in range(num_channels)]

    def put(self, channel_id: int, data):
        """
        Insert data into the specified channel queue.
        When all channel queues contain at least one item,
        a complete frame is assembled and added to the ready queue.

        Args:
            channel_id (int): Index of the channel.
            data: Data sample to insert.
        """
        with self.lock:
            self.channel_queues[channel_id].put(data)
            # Check if all channels have at least one frame available
            if all(not q.empty() for q in self.channel_queues):
                # Collect one frame from each channel
                frame = [self.channel_queues[i].get() for i in range(self.num_channels)]
                self.ready.put(frame)

    def get(self, block: bool = True, timeout: int = None):
        """
        Retrieve the next completed multi-channel frame.

        Args:
            block (bool, optional): Whether to block until a frame is available. Defaults to True.
            timeout (int, optional): Timeout in seconds when blocking. Defaults to None.

        Returns:
            list: A list containing one data sample per channel.
        """
        return self.ready.get(block=block, timeout=timeout)
