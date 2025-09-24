from src.audio.utils import bytes_to_audio, MultiChannelQueue
from src.audio.gstreamer_engine import GStreamerEngine
from src.audio.audio import Source
from typing import override
import time


class GstreamerSource(Source):
    def __init__(self, pipelines_strs, buffer_size=0):
        super().__init__()
        self._engine = GStreamerEngine(pipelines_strs, self._on_new_sample)
        self._data_queue = MultiChannelQueue(self._engine.channels_count())
        self.required_buffer_size = buffer_size

        self._sinks_data = [b"" for _ in range(self.channels_count())]

    @override
    def start(self):
        super().start()
        self._engine.start()

    @override
    def stop(self):
        self._engine.stop()
        super().stop()
        self.clear_pendings()

    @override
    def _run(self):
        while self._continue:
            time.sleep(0.1)
            while self._data_queue.has_data() and self._continue:
                self._emit(self._data_queue.get())

    def _push_data(self, channel_id, data):
        self._data_queue.put(channel_id, data)

    def channels_count(self):
        return self._engine.channels_count()

    def clear_pendings(self):
        self._data_queue.clear()
        self._sinks_data = [b"" for _ in range(self.channels_count())]

    def set_buffer_size(self, buffer_size):
        self.required_buffer_size = buffer_size

    def _on_new_sample(self, channel_id: int, data):

        # store data per channel
        self._sinks_data[channel_id] += data

        # Use received bytes instead of duration. This is more accurate.
        while len(self._sinks_data[channel_id]) >= self.required_buffer_size:
            buff = self._sinks_data[channel_id][: self.required_buffer_size]
            self._sinks_data[channel_id] = self._sinks_data[channel_id][
                self.required_buffer_size :
            ]
            self._push_data(channel_id, bytes_to_audio(buff))
