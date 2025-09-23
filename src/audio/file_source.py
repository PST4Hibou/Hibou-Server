import threading
import soundfile as sf
from src.audio.base_source import BaseAudioSource

class FileAudioSource(BaseAudioSource):
    def __init__(self, file_paths, rec_hz, frame_size):
        super().__init__()
        self.file_paths = file_paths
        self.rec_hz = rec_hz
        self.frame_size = frame_size
        self._thread = None
        self._continue = False

    def start(self):
        import soundfile as sf
        self._continue = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._continue = False
        if self._thread:
            self._thread.join()

    def _read_loop(self):
        import soundfile as sf
        files = [sf.SoundFile(fp) for fp in self.file_paths]
        while self._continue:
            frames = [f.read(self.frame_size, dtype="int32") for f in files]
            if not any(len(ch) for ch in frames):
                break  # EOF
            self._emit(frames)

