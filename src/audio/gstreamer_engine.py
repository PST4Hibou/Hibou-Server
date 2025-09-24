import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


class GStreamerEngine:
    def __init__(self, pipelines_strs: list[str], on_sample):
        # Setting GST's logging level to output.
        # see https://gstreamer.freedesktop.org/documentation/tutorials/basic/debugging-tools.html
        # Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)

        if not Gst.init_check(None):
            raise RuntimeError("Could not initialize GStreamer")

        self._pipelines = []
        self._on_sample = on_sample
        self._sinks = []

        self._create_pipelines(pipelines_strs)
        self._connect_sinks()

    def _create_pipelines(self, pipelines_strs):
        for pipeline_str in pipelines_strs:
            pipeline = Gst.parse_launch(pipeline_str)
            if not pipeline:
                raise RuntimeError("Failed to parse pipeline")

            self._pipelines.append(pipeline)

    def _connect_sinks(self):
        channel = 0
        for pipeline in self._pipelines:
            it = pipeline.iterate_elements()
            while True:
                res, elem = it.next()
                if res == Gst.IteratorResult.RESYNC:
                    it.resync()
                    continue
                if res == Gst.IteratorResult.ERROR:
                    raise RuntimeError("Failed to iterate pipeline")
                if res == Gst.IteratorResult.DONE:
                    break
                if elem.get_factory().get_name() == "appsink":
                    elem.set_property("emit-signals", True)
                    elem.set_property("sync", False)
                    elem.connect("new-sample", self._handle_new_sample, channel)

                    self._sinks.append(elem)
                    channel += 1

    def _handle_new_sample(self, sink, channel_id):
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        data = buf.extract_dup(0, buf.get_size())
        self._on_sample(channel_id, data)  # pass raw data upward

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
