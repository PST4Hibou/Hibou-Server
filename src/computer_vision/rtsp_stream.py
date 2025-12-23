from src.computer_vision.video_recorder import VideoRecorder
from src.computer_vision.video_source import VideoSource
from typing import Callable, override
from src.arguments import args
import numpy as np
import time
import gi
import cv2

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")

from gi.repository import Gst, GstApp


def on_format_location(_, fragment_id: int):
    return f"{time.strftime("%Y%m%d-%H%M%S")}-{fragment_id:05d}.mp4"


class RtspSource(VideoSource, VideoRecorder):
    def __init__(self, rtsp_url: str):
        super().__init__()

        self._record_requests: int = 0
        self._pipeline: Gst.Pipeline | None = None
        self._app_sink: GstApp.AppSink | None = None
        self._rec_sink: Gst.Element | None = None
        self._rec_valve: Gst.Element | None = None
        self._plays: bool = False
        self._last_frame = None
        self._fps: float = 0.0

        # Setting GST's logging level to output.
        # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html
        Gst.debug_set_default_threshold(args.gst_dbg_level)
        if not Gst.init_check(None):
            raise RuntimeError("Could not initialize GStreamer")

        try:
            pipeline_str = (
                f'rtspsrc location="{rtsp_url}" protocols=tcp latency=0 ! '
                "rtpjitterbuffer latency=200 ! rtph264depay ! h264parse ! tee name=h264tee "
                "h264tee. ! queue max-size-buffers=2 leaky=downstream ! avdec_h264 ! queue ! videoconvert ! video/x-raw,format=RGB ! appsink name=app_sink max-buffers=1 drop=true sync=false "
                "h264tee. ! queue max-size-buffers=32 leaky=downstream ! valve name=rec_valve drop=true ! queue ! splitmuxsink name=rec_sink muxer=matroskamux"
            )

            self._create_pipeline(pipeline_str)
            self._connect_sinks()
        except Exception:
            # Clean up any created pipelines
            self._pipeline.set_state(Gst.State.NULL)
            raise

    def _create_pipeline(self, pipeline_str: str) -> None:
        self._pipeline = Gst.parse_launch(pipeline_str)
        if not self._pipeline:
            raise RuntimeError("Failed to parse pipeline")

    def _connect_sinks(self) -> None:
        self._app_sink = self._pipeline.get_by_name("app_sink")
        self._rec_sink = self._pipeline.get_by_name("rec_sink")
        self._rec_valve = self._pipeline.get_by_name("rec_valve")

        if not self._app_sink or not self._rec_sink or not self._rec_valve:
            raise RuntimeError("Failed to get RTSP pipeline elements")

        self._rec_sink.connect("format-location", on_format_location)
        # Set sink properties
        self._app_sink.set_property("emit-signals", True)
        # Connect signal callback
        self._app_sink.connect("new-sample", self._handle_new_sample)

    def _handle_new_sample(self, sink: GstApp.AppSink) -> Gst.FlowReturn:
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR

        caps = sample.get_caps().get_structure(0)
        if self._fps == 0.0:
            fract = caps.get_fraction("framerate")  # fract = fps_num, fps_den
            self._fps = fract[1] / fract[0]

        buf = sample.get_buffer()
        if not buf:
            return Gst.FlowReturn.ERROR

        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.OK

        try:
            w, h = caps.get_value("width"), caps.get_value("height")
            frame = np.frombuffer(
                map_info.data, dtype=np.uint8, count=h * w * 3
            ).reshape((h, w, 3))
            self._last_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            buf.unmap(map_info)
        except Exception as e:
            # Log error or handle appropriately
            print(f"Error in on_sample callback for RTSP source: {e}")
            return Gst.FlowReturn.ERROR

        return Gst.FlowReturn.OK

    @override
    def start(self) -> None:
        if self._pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to start pipeline")

        self._plays = True

    @override
    def stop(self) -> None:
        if self._pipeline.set_state(Gst.State.NULL) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to stop pipeline")

        self._plays = False

    @override
    def start_recording(self):
        if self._record_requests == 0:
            self._rec_sink.emit("split-now")
            self._rec_valve.set_property("drop", False)

        self._record_requests += 1

    @override
    def stop_recording(self) -> None:
        self._record_requests -= 1

        if self._record_requests == 0:
            self._rec_valve.set_property("drop", True)

    @override
    def release(self) -> None:
        self.stop()

    @override
    def get_fps(self) -> float:
        if self._fps != 0.0:
            return self._fps

        caps = self._app_sink.get_property("caps")
        if caps:
            struct = caps.get_structure(0)
            fps_num, fps_den = struct.get_fraction("framerate", 0, 1)
            self._fps = fps_den / fps_num if fps_den else 0.0

        return self._fps

    @override
    def get_frame(self) -> tuple[bool, any]:
        v, self._last_frame = self._last_frame, None
        return (self._plays and v is not None), v

    @override
    def is_opened(self) -> bool:
        return self._plays
