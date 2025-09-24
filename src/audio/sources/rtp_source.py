import os

from src.devices.devices import AudioDevice

from src.audio.sources.gstreamer_source import GstreamerSource


class RTPAudioSource(GstreamerSource):
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
        self.can_devices = can_devices
        self.enable_recording_saves = enable_recording_saves
        self.save_fp = save_fp
        self.record_duration = record_duration
        self.rec_hz = rec_hz
        self.stream_latency = stream_latency

        pipeline_strings = []

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
                f"t0. ! queue max-size-time={record_duration} ! appsink "
                f"t1. ! queue max-size-time={record_duration} ! appsink"
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

            pipeline_strings.append(gst_pipeline_str)

        # Our audios are PCM 24, meaning each audio sample is 3 bytes.
        super().__init__(pipeline_strings, int((rec_hz * record_duration / 1e9) * 3))
