import datetime
import time
import os
from collections import deque

from src.arguments import args
from src.logger import logger
from src.modules.audio.devices.audio_device_controller import ADCControllerManager
from src.modules.audio.dispatcher import AudioDispatcher
from src.modules.audio.streaming import GstChannel
from src.modules.audio.streaming.play import play_sample
from src.modules.audio.streaming.sources.file_source import FileAudioSource
from src.modules.audio.streaming.sources.rtp_source import RTPAudioSource
from src.settings import SETTINGS


class AudioWorker:
    """
    Main class responsible for managing audio devices, streaming audio data and inferencing
    """

    def __init__(self):
        logger.info(f"Started Audio Worker | PID: {os.getpid()}")

        # In charge of managing audio devices, including discovery and control
        self.controller_manager = ADCControllerManager()
        self._load_devices()
        # Get the source, either from a folder or from the network, based on command-line arguments
        self.source = self._get_source()

        try:
            self.run()
        except KeyboardInterrupt:
            logger.critical("Stopping Audio Worker...")
        finally:
            self.source.stop()

    def _load_devices(self):
        """
        Load devices from configuration file or auto-discover them on the network.
        """
        if SETTINGS.DEVICES_CONFIG_PATH:
            self.controller_manager.load_devices_from_files(
                SETTINGS.DEVICES_CONFIG_PATH
            )
        else:
            self.controller_manager.auto_discover()

        logger.info(f"{len(self.controller_manager.adc_devices)} devices loaded")
        logger.debug(f"Devices: {self.controller_manager.adc_devices}")
        for dev in self.controller_manager.adc_devices:
            if not dev.is_online():
                logger.warning(f"{dev.name} is offline")

    def _get_source(self):
        """
        Return the audio source based on the command-line arguments.
        """
        # Folder to save recordings
        recs_folder_name = os.path.join(
            SETTINGS.REC_SAVE_FP,
            f"{datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}",
        )

        if args.infer_from_folder:
            return FileAudioSource(
                folder_path=args.infer_from_folder,
                channel_prefix=args.channel_prefix,
                channels_count=args.channel_count,
                save_fp=recs_folder_name,
                enable_recording_saves=SETTINGS.REC_AUDIO_ENABLE,
                record_duration=SETTINGS.AUDIO_CHUNK_DURATION,
            )
        else:
            return RTPAudioSource(
                devices=self.controller_manager.adc_devices,
                enable_recording_saves=SETTINGS.REC_AUDIO_ENABLE,
                save_fp=recs_folder_name,
                record_duration=int(SETTINGS.AUDIO_CHUNK_DURATION),
                rec_hz=int(SETTINGS.AUDIO_REC_HZ),
                stream_latency=int(SETTINGS.AUDIO_STREAM_LATENCY),
                channel_prefix=args.channel_prefix,
            )

    def run(self):
        audio = AudioDispatcher()
        self.source.set_callback(audio.process)
        self.source.start()

        while True:
            time.sleep(0.01)
