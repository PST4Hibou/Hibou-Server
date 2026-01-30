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


class RtspSource(VideoSource, VideoRecorder):
    """RTSP source + recorder using GStreamer.

    This class builds a GStreamer pipeline that reads an RTSP H264 stream, decodes
    frames for use in the application (via an appsink) and optionally records the
    incoming H264 stream to disk (via separate pipelines). It implements the
    VideoSource interface (frame retrieval) and VideoRecorder (start/stop
    recording).

    Notes:
        - Frame format exposed by `get_frame()` is a BGR numpy array compatible
          with OpenCV.
        - Recording is reference-counted: multiple callers can call
          `start_recording()` and must balance with `stop_recording()`.
    """

    def __init__(self, rtsp_url: str, camera_name: str):
        super().__init__()

        self._camera_name = camera_name
        self._record_requests: int = 0
        self._app_pipeline: Gst.Pipeline | None = None
        self._rec_pipeline: Gst.Pipeline | None = None
        self._app_sink: GstApp.AppSink | None = None
        self._plays: bool = False
        self._last_frame = None
        self._fps: float = 0.0
        self._current_recording_file = None
        self._rtsp_url = rtsp_url

        # Setting GST's logging level to output.
        Gst.debug_set_default_threshold(args.gst_dbg_level)
        if not Gst.is_initialized():
            if not Gst.init_check(None):
                raise RuntimeError("Could not initialize GStreamer")

        try:
            self._create_pipeline(
                (
                    f'rtspsrc location="{rtsp_url}" protocols=tcp latency=0 ! '
                    "rtpjitterbuffer latency=200 ! rtph264depay ! h264parse ! "
                    "avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! "
                    "appsink name=app_sink max-buffers=1 drop=true sync=false emit-signals=true"
                )
            )
            self._connect()

        except Exception as e:
            # Clean up any created pipelines
            if self._rec_pipeline:
                self._rec_pipeline.set_state(Gst.State.NULL)
            if self._app_pipeline:
                self._app_pipeline.set_state(Gst.State.NULL)
            raise RuntimeError(f"Failed to create pipeline: {e}")

    def _create_pipeline(self, pipeline_str: str) -> None:
        """
        Create the GST pipeline according to the provided description.

        Args:
            pipeline_str: the pipeline description.

        Returns:

        """
        self._app_pipeline = Gst.parse_launch(pipeline_str)
        if not self._app_pipeline:
            raise RuntimeError("Failed to parse app pipeline")

    def _connect(self) -> None:
        self._app_sink = self._app_pipeline.get_by_name("app_sink")
        if not self._app_sink:
            raise RuntimeError("Failed to get app sink")

        self._app_sink.connect("new-sample", self._handle_new_sample)

    @staticmethod
    def _create_recording_pipeline(rtsp_url: str, output_file: str) -> Gst.Pipeline:
        """Create a fresh recording pipeline for each recording session."""
        rec_pipeline_str = (
            f'rtspsrc location="{rtsp_url}" protocols=tcp latency=0 ! '
            "rtpjitterbuffer latency=200 ! rtph264depay ! "
            "h264parse config-interval=-1 ! "
            "mp4mux faststart=true ! "
            f'filesink name=rec_filesink location="{output_file}" async=false'
        )

        pipeline = Gst.parse_launch(rec_pipeline_str)
        if not pipeline:
            raise RuntimeError("Failed to parse recording pipeline")

        return pipeline

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
            if fract[0] > 0:
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
        except Exception as e:
            print(f"Error in on_sample callback for RTSP source: {e}")
        finally:
            buf.unmap(map_info)

        return Gst.FlowReturn.OK

    @override
    def start(self) -> None:
        """Start playing the RTSP pipeline.

        Transitions the internal GStreamer pipeline into PLAYING state so that
        frames start being decoded and delivered.

        Raises:
            RuntimeError: If GStreamer fails to change to the PLAYING state.
        """
        if self._plays:
            return

        if (
            self._app_pipeline.set_state(Gst.State.PLAYING)
            == Gst.StateChangeReturn.FAILURE
        ):
            raise RuntimeError("Failed to start app pipeline")

        self._plays = True

    @override
    def stop(self) -> None:
        """Stop the RTSP pipeline and release resources.

        Transitions the pipeline to NULL state. Consumers should call this
        when the source is no longer needed to easy the CPU & memory usage of GST.
        Calling this function will also stop the pending recording if one is being done.

        Raises:
            RuntimeError: If GStreamer fails to change to the NULL state.
        """
        if self._rec_pipeline and self._record_requests > 0:
            self._stop_recording_pipeline()

        if (
            self._app_pipeline.set_state(Gst.State.NULL)
            == Gst.StateChangeReturn.FAILURE
        ):
            raise RuntimeError("Failed to stop app pipeline")

        self._plays = False

    @override
    def start_recording(self, saving_path: str) -> None:
        """Begin recording the incoming stream to disk.

        This method is reference-counted: the first caller will create a new
        recording fragment and open the recorder. Callers must match with
        ``stop_recording()`` to actually stop the recording.
        """

        if self._record_requests == 0:
            self._current_recording_file = f"{saving_path}/{self._camera_name}.mp4"

            self._rec_pipeline = self._create_recording_pipeline(
                self._rtsp_url,  # Note: You need to store rtsp_url in __init__
                self._current_recording_file,
            )

            if not self._rec_pipeline:
                raise RuntimeError("Failed to create recording pipeline")

            if (
                self._rec_pipeline.set_state(Gst.State.PLAYING)
                == Gst.StateChangeReturn.FAILURE
            ):
                self._rec_pipeline = None
                raise RuntimeError("Failed to start recording pipeline")

        self._record_requests += 1

    def _stop_recording_pipeline(self) -> None:
        """Stop a previously requested recording.

        Decrements the internal record-request counter. When the counter reaches
        zero the recorder valve is closed so that recording stops. The method
        does nothing if recording was not active, but callers should ensure
        balanced start/stop calls.
        """
        if not self._rec_pipeline:
            return

        """
        We MUST be very precautionous about the pipeline messages getting through,
        and let the time for finalization of the file. Not doing so can result in a
        few ugly things: Pipeline purely stopped, file not readable, etc.
        """

        # Send EOS event to properly finalize the file
        self._rec_pipeline.send_event(Gst.Event.new_eos())

        # Wait for EOS to propagate
        bus = self._rec_pipeline.get_bus()
        bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR
        )

        # Stop the pipeline
        self._rec_pipeline.set_state(Gst.State.NULL)
        self._rec_pipeline = None

        self._current_recording_file = None

    @override
    def stop_recording(self) -> None:
        """Stop recording and finalize the file."""
        if self._record_requests == 0:
            return

        self._record_requests -= 1

        if self._record_requests == 0:
            self._stop_recording_pipeline()

    @override
    def get_fps(self) -> float:
        """Return the frames-per-second of the incoming stream."""
        return self._fps

    @override
    def get_frame(self) -> tuple[bool, any]:
        """Retrieve the most recent frame."""
        v, self._last_frame = self._last_frame, None
        return (self._plays and v is not None), v

    @override
    def is_opened(self) -> bool:
        """Check if the stream is active."""
        return self._plays
