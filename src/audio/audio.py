import gi


gi.require_version("Gst", "1.0")
from gi.repository import Gst
from src.audio.base_source import BaseAudioSource


class AudioInputManager:
    def __init__(self, source: BaseAudioSource):
        self.source = source
        self._on_data_ready = None

    @property
    def on_data_ready(self):
        return self._on_data_ready

    @on_data_ready.setter
    def on_data_ready(self, callback):
        self._on_data_ready = callback
        self.source.set_callback(callback)

    def start(self):
        self.source.start()

    def stop(self):
        self.source.stop()
