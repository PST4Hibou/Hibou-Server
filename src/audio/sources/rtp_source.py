import logging
import os

from src.adc_devices.models.adc_device import ADCDevice
from src.audio.sources.gstreamer_source import GstreamerSource
from src.settings import SETTINGS


class RTPAudioSource(GstreamerSource):
    def __init__(
        self,
        devices: list[ADCDevice],
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
            payload = dev.rtp_payload
            ip_address = dev.multicast_ip

            gst_pipeline_str = (
                f"udpsrc address={ip_address} port={port} multicast-iface={dev.interface} "
                f'caps="application/x-rtp, media=(string)audio, clock-rate=(int){dev.clock_rate}, '
                f'channels=(int)2, encoding-name=(string)L24, payload=(int){payload}" ! '
                f"rtpjitterbuffer latency={stream_latency} ! "
                f"rtpL24depay ! "
                f"queue ! "
                f"audioconvert ! "
                f"volume volume={SETTINGS.AUDIO_VOLUME} !"
                f"audioresample ! "
                f"audio/x-raw, format=F32LE, channels=(int)2, rate={rec_hz} ! "
                f"deinterleave name=d "
                f"d.src_0 ! tee name=t0 "
                f"d.src_1 ! tee name=t1 "
                f"t0. ! queue ! appsink name=appsink_{channel} "
                f"t1. ! queue ! appsink name=appsink_{channel + 1}"
            )

            logging.debug(gst_pipeline_str)

            if enable_recording_saves:
                os.makedirs(f"{save_fp}/{channel}", exist_ok=True)
                os.makedirs(f"{save_fp}/{channel + 1}", exist_ok=True)

                gst_pipeline_str += (
                    f" t0. ! audioconvert ! audioresample ! "
                    f"audioresample ! "
                    f"audio/x-raw, format=F32LE, channels=(int)2, rate={rec_hz} ! "
                    f'splitmuxsink location="{save_fp}/{channel}/%d.wav" muxer=wavenc '
                    f"max-size-time={record_duration} "
                    f"t1. ! audioconvert ! audioresample ! "
                    f"audio/x-raw, format=F32LE, channels=(int)2, rate={rec_hz} ! "
                    f"volume volume={SETTINGS.AUDIO_VOLUME} !"
                    f'splitmuxsink location="{save_fp}/{channel_prefix}{channel + 1}/%d.wav" muxer=wavenc '
                    f"max-size-time={record_duration}"
                )

            pipeline_strings.append(gst_pipeline_str)
            channel += 2

        # Our audios are F32LE, so each "element" is of size 4.
        super().__init__(pipeline_strings, int((rec_hz * record_duration / 1e9) * 4))
