from src.audio.sources.gstreamer_source import GstreamerSource
from src.settings import SETTINGS
import soundfile as sf
import glob
import os


class FileAudioSource(GstreamerSource):

    def __init__(
        self,
        folder_path: str,
        channel_prefix: str,
        channels_count: int,
        enable_recording_saves: bool,
        save_fp: str,
        record_duration: int,
    ):
        """
        Initialize a FileAudioSource to read multichannel audio from WAV files
        using GStreamer pipelines, optionally in real-time playback and with
        recording/saving of processed streams.

        Args:
            folder_path (str): Path to the root folder containing per-channel
                subfolders with WAV files. Each channel folder should be named
                as "{channel_prefix}{channel_index}".

            channel_prefix (str): Prefix used for channel subfolder names
                (e.g., "ch" for folders like "ch0", "ch1", etc.).

            channels_count (int): Number of audio channels to read.

            enable_recording_saves (bool): If True, the pipeline will save
                processed audio to disk using splitmuxsink.

            save_fp (str): Root folder path where recordings will be saved if
                enable_recording_saves is True. Subfolders for each channel
                will be created automatically.

            record_duration (int): Duration of each recording segment in
                nanoseconds for splitmuxsink (used only if
                enable_recording_saves=True).

        Raises:
            FileNotFoundError: If any channel folder or WAV file is missing.
            ValueError: If WAV files have inconsistent sample rates, channel
                counts, or lengths.

        Notes:
            - This class builds a GStreamer pipeline per file per channel.
            - For real-time playback, an identity element with sync=true is
              used.
            - The pipelines mimic the structure of live UDP streams but read
              from disk instead.
        """

        self._folder_path = folder_path
        self._channel_prefix = channel_prefix
        self._channels_count = channels_count
        self._thread = None
        self._continue = False
        self._audio_paths = []
        self._enable_recording_saves = enable_recording_saves

        self._get_file_paths()

        pipeline_strings = []
        rec_hz = SETTINGS.REC_HZ

        channel = 0
        for ch, files in enumerate(self._audio_paths):
            for idx, fp in enumerate(files):
                gst_pipeline_str = (
                    f'filesrc location="{fp}" ! '
                    f"decodebin ! "
                    f"audioconvert ! "
                    f"audio/x-raw, format=F32LE ! "
                    f"audioresample ! "
                    f"audio/x-raw, format=F32LE, rate=(int){rec_hz} ! "
                    f"identity sync=true ! "  # <--- throttle to realtime
                    f"appsink name=appsink_{ch} "
                    f"drop=false max-buffers=1"
                )

                if self._enable_recording_saves:
                    os.makedirs(f"{save_fp}/{channel}", exist_ok=True)
                    os.makedirs(f"{save_fp}/{channel + 1}", exist_ok=True)

                    gst_pipeline_str = (
                        f'filesrc location="{fp}" ! '
                        f"decodebin ! "
                        f"audioconvert ! "
                        f"audio/x-raw, format=F32LE ! "
                        f"audioresample ! "
                        f"audio/x-raw, format=F32LE, rate=(int){rec_hz} ! "
                        f"tee name=t "
                        f"t. ! queue ! identity sync=true ! appsink name=appsink_{ch} "
                        f"t. ! queue ! audioconvert ! audioresample ! "
                        f'splitmuxsink location="{save_fp}/{channel}/%d.wav" '
                        f"muxer=wavenc max-size-time={record_duration}"
                    )

                pipeline_strings.append(gst_pipeline_str)
                channel += 1

        # Our audios are PCM 24, meaning each audio sample is 3 bytes.
        super().__init__(pipeline_strings, int((rec_hz * record_duration / 1e9) * 3))

    def _get_file_paths(self):
        """Collect file paths for all channels (auto-detect files inside each channel folder)."""
        self._audio_paths = []
        for ch in range(self._channels_count):
            channel_folder = os.path.join(
                self._folder_path, f"{self._channel_prefix}{ch}"
            )
            if not os.path.isdir(channel_folder):
                raise FileNotFoundError(f"Channel folder missing: {channel_folder}")

            # Collect all wav files in this channel folder
            files = sorted(glob.glob(os.path.join(channel_folder, "*.wav")))
            if not files:
                raise FileNotFoundError(
                    f"No .wav files found in channel {ch} folder: {channel_folder}"
                )

            self._audio_paths.append(files)
