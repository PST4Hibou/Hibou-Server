import logging
import os

from src.audio.sources.gstreamer_source import GstreamerSource
from src.devices.audio.dante.models import DanteADCDevice
from src.settings import SETTINGS


class RTPAudioSource(GstreamerSource):
    def __init__(
        self,
        devices: list[DanteADCDevice],
        enable_recording_saves: bool,
        save_fp: str,
        record_duration: int,
        channel_prefix: str,
        rec_hz: int,
        stream_latency: int,
    ):
        """
        Initialize a GStreamer manager to handle multichannel audio streams
        received via RTP from CAN/Dante audio devices.

        Args:
            devices (list[Device]): List of devices objects representing
                the devices providing RTP audio streams.

            enable_recording_saves (bool): Whether to save incoming streams to disk.

            save_fp (str): Root folder path for saving recordings if
                enable_recording_saves is True. Subfolders will be created per channel.

            record_duration (int): Duration of each recording segment in nanoseconds.

            rec_hz (int): Sampling rate of the incoming audio streams in Hz.

            stream_latency (int): Latency of the RTP jitter buffer in milliseconds.

            net_iface (str): Network interface used to retrieve the PTP clock from
                Dante/Audinate devices.

        Raises:
            ValueError: If device configurations are inconsistent or unsupported.
            RuntimeError: If GStreamer pipeline creation fails.

        Notes:
            - Each AudioDevice in can_devices is mapped to a separate GStreamer pipeline.
            - Pipelines are structured to handle multichannel audio with optional
              recording to disk.
        """
        self.devices = devices
        self.enable_recording_saves = enable_recording_saves
        self.save_fp = save_fp
        self.record_duration = record_duration
        self.rec_hz = rec_hz
        self.stream_latency = stream_latency

        pipeline_strings = []

        logging.blank_line()
        logging.debug("Gstreamer pipeline:")

        channel = 0
        for dev in self.devices:
            port = dev.port
            ip_address = dev.multicast_ip
            nb_channels = dev.nb_channels
            payload = dev.rtp_payload

            branches = " ".join(
                f"d.src_{i} ! tee name=t{i} t{i}. ! queue ! appsink name=appsink_{channel + i}"
                for i in range(nb_channels)
            )

            # rtpsrc has issues using & figuring out the net stream.
            gst_pipeline_str = (
                f"udpsrc address={ip_address} port={port} multicast-iface={dev.interface} "
                f'caps="application/x-rtp, media=(string)audio, clock-rate=(int){dev.clock_rate}, '
                f'channels=(int){nb_channels}, encoding-name=(string)L24, payload=(int){payload}" ! '
                f"rtpjitterbuffer latency={stream_latency} ! "
                f"rtpL24depay ! "
                f"queue ! "
                f"audioconvert ! "
                f"volume volume={SETTINGS.AUDIO_VOLUME} ! "
                f"audioresample ! "
                f"audio/x-raw, format=F32LE, channels=(int){nb_channels}, rate={rec_hz} ! "
                f"deinterleave name=d "
                f"{branches} "
            )

            if enable_recording_saves:
                for i in range(nb_channels):
                    os.makedirs(f"{save_fp}/{i}", exist_ok=True)

                record_branches = " ".join(
                    (
                        f"t{i}. ! "
                        f'splitmuxsink location="{save_fp}/'
                        f'{channel_prefix}{channel + i}/%d.wav" '
                        f"muxer=wavenc max-size-time={record_duration}"
                    )
                    for i in range(nb_channels)
                )

                gst_pipeline_str += record_branches

            logging.debug(gst_pipeline_str)

            pipeline_strings.append(gst_pipeline_str)
            channel += nb_channels

        # Our audios are F32LE, so each "element" is of size 4.
        super().__init__(pipeline_strings, int((rec_hz * record_duration / 1e9) * 4))
