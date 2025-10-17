from src.audio.debug.channel_spectrogram import ChannelTimeSpectrogram
from src.audio.angle_of_arrival import AngleOfArrivalEstimator
from src.audio.sources.file_source import FileAudioSource
from src.audio.sources.rtp_source import RTPAudioSource
from src.audio.energy import compute_energy
from src.devices.devices import Devices
from src.audio.play import play_sample
from src.settings import SETTINGS
from src.arguments import args
from src.logger import logger

import logging


class AudioProcess:
    def __init__(self, nb_channels, frame_duration_s, angle_coverage):
        if SETTINGS.AUDIO_ENERGY_SPECTRUM:  # Only for debug purposes
            self.spectro = ChannelTimeSpectrogram(nb_channels, frame_duration_s)
        self.angle_estimator = AngleOfArrivalEstimator(nb_channels, angle_coverage)

    def process(self, channels):
        # enhanced_audio = apply_noise_reduction(channels)

        energies = [compute_energy(ch) for ch in channels]
        if SETTINGS.AUDIO_ENERGY_SPECTRUM:  # Only for debug purposes
            self.spectro.update(energies)

        angle = self.angle_estimator.estimate(energies)
        print(f"Angle: {angle:.2f}°")

        if SETTINGS.AUDIO_PLAYBACK:  # Only for debug purposes
            play_sample(channels, 0)


if __name__ == "__main__":
    logger.debug(f"Loaded settings: {SETTINGS}")
    devices = Devices.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    # devices = Devices.auto_discover()

    logging.info(f"{len(devices)} devices loaded...")
    logging.debug(f"Devices: {devices}")

    if args.infer_from_folder:
        source = FileAudioSource(
            folder_path=args.infer_from_folder,
            channel_prefix="ch_",
            channels_count=4,
            save_fp=SETTINGS.REC_SAVE_FP,
            enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
            record_duration=SETTINGS.REC_DURATION,
        )
    else:
        source = RTPAudioSource(
            devices=devices,
            enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
            save_fp=SETTINGS.REC_SAVE_FP,
            record_duration=int(SETTINGS.REC_DURATION),
            rec_hz=int(SETTINGS.REC_HZ),
            stream_latency=int(SETTINGS.STREAM_LATENCY),
        )

    # Every SETTING.REC_DURATION seconds, this function is called
    audio = AudioProcess(
        nb_channels=len(devices) * 2,
        frame_duration_s=SETTINGS.REC_DURATION / 1000,
        angle_coverage=90,
    )
    source.set_callback(audio.process)

    try:
        source.start()
        print("Audio source started. Press Ctrl+C to stop.")
        while True:
            import time

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio...")
        source.stop()
