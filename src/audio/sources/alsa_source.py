import logging
import os

from src.audio.sources.gstreamer_source import GstreamerSource
from src.settings import SETTINGS


class AlsaAudioSource(GstreamerSource):
    def __init__(
        self,
        enable_recording_saves: bool,
        save_fp: str,
        record_duration: int,
        rec_hz: int,
        stream_latency: int,
    ):
        self.enable_recording_saves = enable_recording_saves
        self.save_fp = save_fp
        self.record_duration = record_duration
        self.rec_hz = rec_hz
        self.stream_latency = stream_latency

        pipeline_strings = []

        logging.blank_line()
        logging.debug("Gstreamer pipeline:")

        channel = 0
        gst_pipeline_str = (
            f"alsasrc ! audioconvert ! audioresample ! audio/x-raw, format=F32LE, rate={rec_hz} ! "
            f"tee name=t0 t0. ! queue ! appsink name=appsink_{channel} "
        )

        logging.debug(gst_pipeline_str)

        if enable_recording_saves:
            os.makedirs(f"{save_fp}/", exist_ok=True)
            gst_pipeline_str += (
                f" t0. ! audioconvert ! audioresample ! "
                f"audioresample ! "
                f"audio/x-raw, format=F32LE, channels=(int)2, rate={rec_hz} ! "
                f'splitmuxsink location="{save_fp}//%d.wav" muxer=wavenc '
                f"max-size-time={record_duration} "
            )

        pipeline_strings.append(gst_pipeline_str)

        # Our audios are signed float 32, from -1 to 1, meaning each audio sample is 4 bytes.
        super().__init__(pipeline_strings, int((rec_hz * record_duration / 1e9) * 4))
