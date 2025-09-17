import gi, time, os, queue, threading

import numpy as np

from threading import Thread

gi.require_version('Gst', '1.0')
from gi.repository import Gst


def bytes_to_audio(raw_bytes, dtype = np.int32):
    """
        Convert 24-bit PCM raw bytes to a normalized NumPy float32 array.

        Args:
            raw_bytes (bytes): Raw 24-bit PCM audio data.
            dtype (np.dtype, optional): Intermediate dtype for conversion. Defaults to np.int32.

        Returns:
            np.ndarray: 1D array of float32 samples in range [-1.0, 1.0].
        [TOCHECK]
    """
    # Convert bytes to 1D array of uint8
    byte_array = np.frombuffer(raw_bytes, dtype=np.uint8)

    # Reshape to N x 3 bytes (24-bit samples)
    samples_24bit = byte_array.reshape(-1, 3)

    # Convert to 32-bit integers
    # Little-endian L24 -> int32
    # Pad the most significant byte (sign extend)
    samples_32bit = np.zeros((samples_24bit.shape[0],), dtype=np.int32)
    samples_32bit[:] = (
        samples_24bit[:, 0].astype(np.int32) |
        (samples_24bit[:, 1].astype(np.int32) << 8) |
        (samples_24bit[:, 2].astype(np.int32) << 16)
    )

    # Sign extension for negative numbers
    samples_32bit[samples_32bit >= 0x800000] -= 0x1000000

    return samples_32bit.astype(np.float32) / (2**23)  # 24-bit signed


class MultiChannelQueue:
    """
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

        if num_channels != None:
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
        return self.ready.get(block = block, timeout = timeout)


class AudioInputManager:
    """
    """
    def createFromEnv():
        """
        Factory method to create a AudioInputManager instance using environment variables.

        Environment Variables:
            SOURCE_PORTS (str): Comma-separated list of UDP source ports.
            ENABLE_REC_SAVE (str): "True" or "False" to enable/disable recording.
            REC_SAVE_FP (str): File path for saving recordings.
            REC_DURATION (str): Recording duration in nanoseconds.
            REC_HZ (str): Audio sampling rate.
            STREAM_LATENCY (str): GStreamer jitter buffer latency in ms.

        Returns:
            AudioInputManager: Configured AudioInputManager instance.
        """
        return AudioInputManager(pipeline_ports = os.getenv("SOURCE_PORTS").split(","), enable_recording_saves = eval(os.getenv("ENABLE_REC_SAVE"), {}, {}), save_fp = os.getenv("REC_SAVE_FP"), record_duration = int(os.getenv("REC_DURATION")), rec_hz = int(os.getenv("REC_HZ")), stream_latency = int(os.getenv("STREAM_LATENCY")))

    def __init__(self, pipeline_ports: list[str], enable_recording_saves: bool, save_fp: str, record_duration: int, rec_hz: int, stream_latency: int):
        """
            Initialize a GStreamer manager to handle multi-channel audio pipelines.

            Args:
                pipeline_ports (list[str]): UDP ports providing audio streams.
                enable_recording_saves (bool): Whether to save recordings to disk.
                save_fp (str): File path for saving recordings if enabled.
                record_duration (int): Recording segment duration (ns).
                rec_hz (int): Sampling rate in Hz.
                stream_latency (int): Jitter buffer latency in ms.
        """
        self.pipeline_ports = pipeline_ports
        self.enable_recording_saves = enable_recording_saves
        self.save_fp = save_fp
        self.record_duration = record_duration
        self.rec_hz = rec_hz
        self.stream_latency = stream_latency
        self._channel_states = {}
        self._pipelines = []
        self._sinks = []

        if not Gst.init_check(None):  # init gstreamer
            print("Could not initialize GStreamer.")

        channel = 0
        for port in pipeline_ports:
            pipeline = None

            gst_pipeline_str: str = f"udpsrc port={port} caps=\"application/x-rtp, media=(string)audio, clock-rate=(int){rec_hz}, channels=(int)2, encoding-name=(string)L24, payload=(int)98\" ! rtpjitterbuffer latency={stream_latency} ! rtpL24depay !  queue ! audioconvert ! audio/x-raw,channels=2 ! deinterleave name=d \
                d.src_0 ! tee name=t0 \
                d.src_1 ! tee name=t1 \
                t0. ! queue max-size-time={record_duration} ! appsink name=sink1 \
                t1. ! queue max-size-time={record_duration} ! appsink name=sink2"

            if enable_recording_saves:
                os.makedirs(f"{save_fp}/{channel}", exist_ok=True)
                os.makedirs(f"{save_fp}/{channel+1}", exist_ok=True)

                gst_pipeline_str += f" \
                t0. ! audioconvert ! audioresample ! splitmuxsink location=\"{save_fp}/{channel}/%d.wav\" muxer=wavenc max-size-time={record_duration} \
                t1. ! audioconvert ! audioresample ! splitmuxsink location=\"{save_fp}/{channel+1}/%d.wav\" muxer=wavenc max-size-time={record_duration}"

            # Setting GST's logging level to output.
            # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html
            # Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

            pipeline = Gst.parse_launch(gst_pipeline_str)
            if not pipeline:
                print("Could not create pipeline.")
                exit(0)

            for i in range(2):
                sink = pipeline.get_by_name(f"sink{i+1}")
                if not sink:
                    print("Failed to get pipeline's sink.")
                    exit(0)

                sink.set_property("emit-signals", True)
                sink.connect("new-sample", lambda x, z = i: self._on_new_sample(z, x))

                self._sinks.append(sink)
                self._channel_states.update({sink: {"data": [], "accumulated_ns": 0}})

            self._pipelines.append(pipeline)
            channel += 2

        self._dataQueue = MultiChannelQueue(len(self._sinks))
        self._thread = Thread(target = self._run, args = ())
        self._continue = False

    def _on_new_sample(self, channel_id: int, sink):
        """
            Callback triggered when a new sample is available from a sink.

            Args:
                channel_id (int): Channel index associated with the sink.
                sink (Gst.Element): The GStreamer appsink providing the sample.

            Returns:
                Gst.FlowReturn: GStreamer flow control signal.
        """
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        duration = buf.duration  # in nanoseconds
        data = buf.extract_dup(0, buf.get_size())

        # store data per channel
        self._channel_states[sink]["data"].append(data)
        self._channel_states[sink]["accumulated_ns"] += duration

        if self._channel_states[sink]["accumulated_ns"] >= self.record_duration:
            # reset state
            self._channel_states[sink]["data"].clear()
            self._channel_states[sink]["accumulated_ns"] = 0

            self._dataQueue.put(channel_id, bytes_to_audio(b"".join(self._channel_states[sink]["data"])))

        return Gst.FlowReturn.OK

    def on_data_ready(self, data: list):
        """
            Hook method called when a new multi-channel frame is ready.
            Intended to be overridden by subclasses or reassigned.

            Args:
                data (list): List of channel-aligned audio frames.
        """
        pass

    def _run(self):
        """
            Background thread loop that continuously polls the data queue.
            Calls `on_data_ready` when new frames are available.
        """
        while self._continue:
            # [TODO] Use a smaller
            time.sleep(0.1)
            if not self._dataQueue.ready.empty():
                self.on_data_ready(self._dataQueue.get())

    def _clear_pendings(self):
        """
            Clear any pending data in queues and reset internal state.
            (Currently a placeholder, does nothing.)
        """
        for sink_state in self._channel_states:
            sink_state["data"].clear()
            sink_state["accumulated_ns"] = 0

    def start(self):
        """
            Start all GStreamer pipelines and the background processing thread.

            Raises:
                SystemExit: If a pipeline fails to transition to PLAYING.
        """
        if self._continue:
            return

        self._continue = True
        self._thread.start()

        for pipeline in self._pipelines:
            ret = pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                print("Failed to make the pipeline play.")
                exit(0)

    def stop(self):
        """
            Stop all GStreamer pipelines and terminate the background thread.
            Also clears pending data.

            Raises:
                SystemExit: If a pipeline fails to transition to PAUSED.
        """
        for pipeline in self._pipelines:
            ret = pipeline.set_state(Gst.State.PAUSED)
            if ret == Gst.StateChangeReturn.FAILURE:
                print("Failed to make the pipeline pause.")
                exit(0)

        self._continue = False
        self._thread.join()
        self._clear_pendings()
