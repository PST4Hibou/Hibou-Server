import gi, threading, os, time

from src.audio.multi_channel_queue import MultiChannelQueue
from src.audio.utils import bytes_to_audio
from src.devices.devices import AudioDevice

gi.require_version("Gst", "1.0")
from gi.repository import Gst
from src.audio.base_source import BaseAudioSource


class GStreamerAudioSource(BaseAudioSource):
    def __init__(
        self,
        can_devices: list[AudioDevice],
        enable_recording_saves: bool,
        save_fp: str,
        record_duration: int,
        rec_hz: int,
        stream_latency: int,
        net_iface: str,
    ):
        """
        Initialize a GStreamer manager to handle multi-channel audio pipelines.

        Args:
            pipeline_ports (list[str]): UDP ports providing audio streams.
            enable_recording_saves (bool): Whether to save recordings to disk.
            save_fp (str): File path for saving recordings if enabled.
            record_duration (int): Recording segment duration (ns).
            rec_hz (int): Sampling rate in Hz.
            stream_latency (int): Jitter buffer latency in ms.
            net_iface (str): Network interface used to retrieve the PTP clock from Dante/Audinate devices.
            rtp_payloads (list[str]): UDP payloads for each audio source port.
            ip_addresses (list[str]): Comma-separated list of IPs on which the audio is multicasted on.
        """
        super().__init__()
        self.can_devices = can_devices
        self.enable_recording_saves = enable_recording_saves
        self.save_fp = save_fp
        self.record_duration = record_duration
        self.rec_hz = rec_hz
        # Our audios are PCM 24, meaning each audio sample is 3 bytes.
        self.required_data = int((rec_hz * record_duration / 1e9) * 3)
        self.stream_latency = stream_latency
        self._sink_states = []
        self._pipelines = []
        self._sinks = []

        if not Gst.init_check(None):  # init gstreamer
            print("Could not initialize GStreamer.")

        channel = 0
        for dev in self.can_devices:
            port = dev.port
            payload = dev.rtp
            ip_address = dev.multicast_ip

            gst_pipeline_str = (
                f"udpsrc address={ip_address} port={port} multicast-iface={net_iface} "
                f'caps="application/x-rtp, media=(string)audio, clock-rate=(int){rec_hz}, '
                f'channels=(int)2, encoding-name=(string)L24, payload=(int){payload}" ! '
                f"rtpjitterbuffer latency={stream_latency} ! "
                f"rtpL24depay ! "
                f"queue ! "
                f"audioconvert ! "
                f"audio/x-raw, format=S24LE, channels=(int)2 ! "
                f"deinterleave name=d "
                f"d.src_0 ! tee name=t0 "
                f"d.src_1 ! tee name=t1 "
                f"t0. ! queue max-size-time={record_duration} ! appsink name=sink0 "
                f"t1. ! queue max-size-time={record_duration} ! appsink name=sink1"
            )

            if enable_recording_saves:
                os.makedirs(f"{save_fp}/{channel}", exist_ok=True)
                os.makedirs(f"{save_fp}/{channel + 1}", exist_ok=True)

                gst_pipeline_str += (
                    f" t0. ! audioconvert ! audioresample ! "
                    f'splitmuxsink location="{save_fp}/{channel}/%d.wav" muxer=wavenc '
                    f"max-size-time={record_duration} "
                    f"t1. ! audioconvert ! audioresample ! "
                    f'splitmuxsink location="{save_fp}/{channel + 1}/%d.wav" muxer=wavenc '
                    f"max-size-time={record_duration}"
                )

            # Setting GST's logging level to output.
            # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html
            # Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

            pipeline = Gst.parse_launch(gst_pipeline_str)
            if not pipeline:
                print("Could not create pipeline.")
                exit(0)

            for i in range(2):
                sink = pipeline.get_by_name(f"sink{i}")
                if not sink:
                    print("Failed to get pipeline's sink.")
                    exit(0)

                sink.set_property("emit-signals", True)
                sink.set_property("sync", False)  # Don't sync to clock
                # sink.set_property("drop", True)   # Drop buffers if app is slow
                # sink.set_property("max-buffers", 10)  # Limit buffer queue
                sink.connect(
                    "new-sample", self._on_new_sample, channel + i
                )  # Pass channel_id directly

                self._sinks.append(sink)
                self._sink_states.append({"data": b"", "accumulated_ns": 0})

            self._pipelines.append(pipeline)
            channel += 2

        self._data_queue = MultiChannelQueue(len(self._sinks))
        self._thread = threading.Thread(target=self._run, args=())
        self._continue = False

    def _run(self):
        """
        Background thread loop that continuously polls the data queue.
        Calls `on_data_ready` when new frames are available.
        """
        while self._continue:
            time.sleep(0.1)
            if not self._data_queue.ready.empty():
                self.on_data_ready(self._data_queue.get())

    def _on_new_sample(self, sink, channel_id: int):
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
        sink_state = self._sink_states[channel_id]
        sink_state["data"] += data
        sink_state["accumulated_ns"] += duration

        # Use received bytes instead of duration. This is more accurate.
        while len(sink_state["data"]) >= self.required_data:
            buff = sink_state["data"][: self.required_data]
            sink_state["data"] = sink_state["data"][self.required_data :]
            self._data_queue.put(channel_id, bytes_to_audio(buff))

        return Gst.FlowReturn.OK

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

    def _clear_pendings(self):
        """
        Clear any pending data in queues and reset internal state.
        """
        for sink_state in self._sink_states:
            sink_state["data"] = b""
            sink_state["accumulated_ns"] = 0

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

    def set_callback(self, callback):
        self.on_data_ready = callback
