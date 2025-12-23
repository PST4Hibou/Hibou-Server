from src.computer_vision.video_recorder import VideoRecorder
from src.computer_vision.video_source import VideoSource
from src.settings import SETTINGS
from src.arguments import args
from typing import override
from pathlib import Path
import numpy as np
import time
import gi
import cv2

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")

from gi.repository import Gst, GstApp


def on_format_location(_, fragment_id: int):
    return f"{SETTINGS.VIDEO_SAVE_FP}/{time.strftime("%Y%m%d-%H%M%S")}-{fragment_id:05d}.mp4"


class RtspSource(VideoSource, VideoRecorder):
    """RTSP source + recorder using GStreamer.

    This class builds a GStreamer pipeline that reads an RTSP H264 stream, decodes
    frames for use in the application (via an appsink) and optionally records the
    incoming H264 stream to disk (via a splitmuxsink). It implements the
    VideoSource interface (frame retrieval) and VideoRecorder (start/stop
    recording).

    Notes:
        - Frame format exposed by `get_frame()` is a BGR numpy array compatible
          with OpenCV.
        - Recording is reference-counted: multiple callers can call
          `start_recording()` and must balance with `stop_recording()`.
    """

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

        # Create dir if missing, splitmuxsink will not create it.
        Path(SETTINGS.VIDEO_SAVE_FP).mkdir(parents=True, exist_ok=True)

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
        """Create the GStreamer pipeline from a pipeline description string.

        Args:
            pipeline_str: The textual GStreamer pipeline description to parse.

        Raises:
            RuntimeError: If GStreamer fails to parse or create the pipeline.
        """
        self._pipeline = Gst.parse_launch(pipeline_str)
        if not self._pipeline:
            raise RuntimeError("Failed to parse pipeline")

    def _connect_sinks(self) -> None:
        """Look up and configure the appsink/recorder elements from the pipeline.

        This method locates the named elements of the pipeline, and sets up callbacks
        and properties as needed.

        Raises:
            RuntimeError: If any required pipeline element cannot be found.
        """
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
        """GStreamer appsink callback to handle a new decoded sample.

        The BGR sample is stored in ``self._last_frame`` for retrieval by the
        consumer via ``get_frame()``.

        Args:
            sink: The GstApp.AppSink that emitted the "new-sample" signal.

        Returns:
            A Gst.FlowReturn value. Returns Gst.FlowReturn.OK on success so the
            pipeline continues, and Gst.FlowReturn.ERROR on unrecoverable
            failures.
        """
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
        """Start playing the RTSP pipeline.

        Transitions the internal GStreamer pipeline into PLAYING state so that
        frames start being decoded and delivered.

        Raises:
            RuntimeError: If GStreamer fails to change to the PLAYING state.
        """
        if self._pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to start pipeline")

        self._plays = True

    @override
    def stop(self) -> None:
        """Stop the RTSP pipeline and release resources.

        Transitions the pipeline to NULL state. Consumers should call this
        when the source is no longer needed to easy the CPU & memory usage of GST.

        Raises:
            RuntimeError: If GStreamer fails to change to the NULL state.
        """
        if self._pipeline.set_state(Gst.State.NULL) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to stop pipeline")

        self._plays = False

    @override
    def start_recording(self):
        """Begin recording the incoming stream to disk.

        This method is reference-counted: the first caller will create a new
        recording fragment and open the recorder. Callers must match with
        ``stop_recording()`` to actually stop the recording.
        """
        if self._record_requests == 0:
            self._rec_sink.emit("split-now")
            self._rec_valve.set_property("drop", False)

        self._record_requests += 1

    @override
    def stop_recording(self) -> None:
        """Stop a previously requested recording.

        Decrements the internal record-request counter. When the counter reaches
        zero the recorder valve is closed so that recording stops. The method
        does nothing if recording was not active, but callers should ensure
        balanced start/stop calls.
        """
        self._record_requests -= 1

        if self._record_requests == 0:
            self._rec_valve.set_property("drop", True)

    @override
    def get_fps(self) -> float:
        """Return the frames-per-second of the incoming stream.

        The FPS is read from the appsink caps the first time this method is
        called and cached for subsequent calls. If FPS cannot be determined
        the method returns 0.0.

        Returns:
            float: The stream's FPS, or 0.0 if unknown.
        """
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
        """Retrieve the most recent frame delivered by the appsink.

        This method returns a tuple (ok, frame) where `ok` indicates whether a
        valid frame was returned and `frame` is the OpenCV-compatible BGR
        numpy array. The last-frame buffer is cleared after reading so repeated
        calls without a new frame will return (False, None).

        Returns:
            tuple[bool, any]: (True, frame) when a frame is available, else
            (False, None).
        """
        v, self._last_frame = self._last_frame, None
        return (self._plays and v is not None), v

    @override
    def is_opened(self) -> bool:
        """Check if the RTSP stream is currently active.

        Returns:
            bool: True if the stream is playing, False otherwise
        """
        return self._plays
