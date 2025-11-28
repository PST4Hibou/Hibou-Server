from src.audio.utils import bytes_to_audio, MultiChannelQueue
from src.audio.gstreamer_engine import GStreamerEngine
from src.audio.audio import Source
from typing import override
import time
import numpy as np


def normalize(arr: np.array):
    return arr
    # return arr / np.max(np.abs(arr))


class GstreamerSource(Source):
    def __init__(self, pipelines_strs, buffer_size=0):
        super().__init__()
        self._engine = GStreamerEngine(pipelines_strs, self._on_new_sample)
        self._data_queue = MultiChannelQueue(self._engine.channels_count())
        self.required_buffer_size = buffer_size

        # DEBUG: Check if buffer size is aligned
        if buffer_size % 4 != 0:
            self.required_buffer_size = (buffer_size // 4) * 4

        self._sinks_data = [b"" for _ in range(self.channels_count())]
        self._debug_counter = {}  # Track callbacks per channel for debug

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
        # DEBUG: Log first 10 callbacks per channel only
        if channel_id not in self._debug_counter:
            self._debug_counter[channel_id] = 0

        # store data per channel
        self._sinks_data[channel_id] += data

        # IMPORTANT: Ensure we only slice on float32 boundaries (4 bytes)
        # to prevent buffer misalignment corruption
        bytes_per_sample = 4  # float32 = 4 bytes
        aligned_buffer_size = (
            self.required_buffer_size // bytes_per_sample
        ) * bytes_per_sample

        # Use received bytes instead of duration. This is more accurate.
        extracted_any = False
        while len(self._sinks_data[channel_id]) >= aligned_buffer_size:
            buff = self._sinks_data[channel_id][:aligned_buffer_size]
            self._sinks_data[channel_id] = self._sinks_data[channel_id][
                aligned_buffer_size:
            ]
            extracted_any = True

            # Convert bytes to audio array
            audio_array = bytes_to_audio(buff)

            # CRITICAL FIX: Remove corruption from multifilesrc file transitions
            # GStreamer's multifilesrc+wavparse can insert garbage bytes between files
            # Detect and zero out any values that are clearly corrupted (> 1000 or < -1000)
            corrupt_mask = np.abs(audio_array) > 1000
            if np.any(corrupt_mask):
                num_corrupt = np.sum(corrupt_mask)
                corrupt_indices = np.where(corrupt_mask)[0]
                audio_array[corrupt_mask] = 0.0
            else:
                audio_min, audio_max = np.min(audio_array), np.max(audio_array)

            self._push_data(channel_id, normalize(audio_array))

        # CRITICAL FIX: Discard small leftover fragments ONLY after extracting at least one buffer
        # This prevents cross-file contamination while allowing chunks to accumulate normally.
        # When multifilesrc switches files, leftover bytes from the previous file
        # will corrupt the start of the next file. Discard fragments < 50% of buffer.
        if extracted_any:
            max_leftover = aligned_buffer_size // 2
            if 0 < len(self._sinks_data[channel_id]) < max_leftover:
                discarded = len(self._sinks_data[channel_id])
                self._sinks_data[channel_id] = b""
