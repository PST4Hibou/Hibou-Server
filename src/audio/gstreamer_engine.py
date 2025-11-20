from src.arguments import args
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class GStreamerEngine:
    def __init__(self, pipelines_strs: list[str], on_sample):
        # Setting GST's logging level to output.
        # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html
        Gst.debug_set_default_threshold(args.gst_dbg_level)

        if not Gst.init_check(None):
            raise RuntimeError("Could not initialize GStreamer")

        self._pipelines = []
        self._on_sample = on_sample
        self._sinks = []
        try:
            self._create_pipelines(pipelines_strs)
            self._connect_sinks()
        except Exception:
            # Clean up any created pipelines
            for p in self._pipelines:
                p.set_state(Gst.State.NULL)
            raise

    def _create_pipelines(self, pipelines_strs):
        for pipeline_str in pipelines_strs:
            pipeline = Gst.parse_launch(pipeline_str)
            if not pipeline:
                raise RuntimeError("Failed to parse pipeline")

            self._pipelines.append(pipeline)

    def _connect_sinks(self):
        pipelines = {}

        for pipeline_idx, pipeline in enumerate(self._pipelines):
            it = pipeline.iterate_elements()
            while True:
                res, elem = it.next()
                if res == Gst.IteratorResult.RESYNC:
                    it.resync()
                    continue
                if res == Gst.IteratorResult.ERROR:
                    raise RuntimeError(f"Failed to iterate pipeline #{pipeline_idx}")
                if res == Gst.IteratorResult.DONE:
                    break

                # Check if this element is an appsink
                if elem.get_factory().get_name() == "appsink":
                    name = elem.get_name()
                    parts = name.split("_")

                    if len(parts) != 2 or not parts[1].isdigit():
                        raise ValueError(
                            f"Invalid appsink name '{name}'. Expected format 'appsink_<channel_id>'."
                        )

                    channel = int(parts[1])

                    if channel in pipelines:
                        raise ValueError(
                            f"Duplicate channel id {channel} found in pipeline #{pipeline_idx} "
                            f"(appsink name='{name}')"
                        )

                    # Set sink properties
                    elem.set_property("emit-signals", True)
                    elem.set_property("sync", False)

                    # Connect signal callback
                    elem.connect("new-sample", self._handle_new_sample, channel)

                    # Register in dict for sorting later
                    pipelines[channel] = elem

        # Sort channels to ensure deterministic order
        for channel in sorted(pipelines.keys()):
            self._sinks.append(pipelines[channel])

    def _handle_new_sample(self, sink, channel_id):
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR
        buf = sample.get_buffer()
        if not buf:
            return Gst.FlowReturn.ERROR

        try:
            data = buf.extract_dup(0, buf.get_size())
            self._on_sample(channel_id, data)  # pass raw data upward
        except Exception as e:
            # Log error or handle appropriately
            print(f"Error in on_sample callback for channel {channel_id}: {e}")
            return Gst.FlowReturn.ERROR

        return Gst.FlowReturn.OK

    def start(self):
        for p in self._pipelines:
            if p.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")

    def stop(self):
        for p in self._pipelines:
            if p.set_state(Gst.State.NULL) == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to stop pipeline")

    def channels_count(self):
        return len(self._sinks)
