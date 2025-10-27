from src.audio.debug.channel_spectrogram import ChannelTimeSpectrogram
from src.audio.angle_of_arrival import AngleOfArrivalEstimator
from src.computer_vision.drone_detection import DroneDetection
from src.audio.sources.file_source import FileAudioSource
from src.audio.sources.rtp_source import RTPAudioSource
from src.audio.debug.radar import RadarPlot
from src.audio.energy import compute_energy
from src.devices.devices import Devices
from src.audio.play import play_sample
from src.settings import SETTINGS
from src.arguments import args
from src.logger import logger
from src.ptz.ptz import PTZ
from time import sleep

import datetime
import logging
import os


class AudioProcess:
    def __init__(self, nb_channels, frame_duration_s, angle_coverage):
        if SETTINGS.AUDIO_ENERGY_SPECTRUM:  # Only for debug purposes
            self.spectro = ChannelTimeSpectrogram(nb_channels, frame_duration_s)
        if SETTINGS.AUDIO_RADAR:  # Only for debug purposes
            self.radar = RadarPlot()
        self.angle_estimator = AngleOfArrivalEstimator(nb_channels, angle_coverage)
        self.ptz = PTZ.get_instance()

    def process(self, channels):
        # enhanced_audio = apply_noise_reduction(channels)

        energies = [compute_energy(ch) for ch in channels]
        if SETTINGS.AUDIO_ENERGY_SPECTRUM:  # Only for debug purposes
            self.spectro.update(energies)

        angle = self.angle_estimator.estimate(energies)

        self.ptz.go_to_angle(angle)

        if SETTINGS.AUDIO_RADAR:
            self.radar.update(angle, max(energies))

        if SETTINGS.AUDIO_PLAYBACK:  # Only for debug purposes
            play_sample(channels, 0)


if __name__ == "__main__":
    logger.debug(f"Loaded settings: {SETTINGS}")
    devices = Devices.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    # devices = Devices.auto_discover()
    ptz = PTZ(
        SETTINGS.PTZ_HOST,
        SETTINGS.PTZ_USERNAME,
        SETTINGS.PTZ_PASSWORD,
        SETTINGS.PTZ_START_AZIMUTH,
        SETTINGS.PTZ_END_AZIMUTH,
    )

    audio = AudioProcess(
        nb_channels=len(devices) * 2,
        frame_duration_s=SETTINGS.REC_DURATION / 1000,
        angle_coverage=SETTINGS.AUDIO_ANGLE_COVERAGE,
    )

    logging.info(f"{len(devices)} devices loaded...")
    logging.debug(f"Devices: {devices}")

    now = datetime.datetime.now()
    recs_folder_name = os.path.join(
        SETTINGS.REC_SAVE_FP, f"{now.strftime('%d-%m-%Y_%H:%M:%S')}"
    )
    if args.infer_from_folder:
        source = FileAudioSource(
            folder_path=args.infer_from_folder,
            channel_prefix="ch_",
            channels_count=4,
            save_fp=recs_folder_name,
            enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
            record_duration=SETTINGS.REC_DURATION,
        )
    else:
        source = RTPAudioSource(
            devices=devices,
            enable_recording_saves=SETTINGS.ENABLE_REC_SAVE,
            save_fp=recs_folder_name,
            record_duration=int(SETTINGS.REC_DURATION),
            rec_hz=int(SETTINGS.REC_HZ),
            stream_latency=int(SETTINGS.STREAM_LATENCY),
        )

    # Every SETTING.REC_DURATION seconds, this function is called
    source.set_callback(audio.process)
    drone_detector = DroneDetection(
        model_type="yolo", model_path="assets/computer_vision_models/yolov8n.pt"
    )
    stream = ptz.get_video_stream()

    try:
        source.start()
        drone_detector.start(stream, display=True)
        print("Listening started. Press Ctrl+C to stop.")
        while True:
            sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping audio...")
    finally:
        drone_detector.stop()
        ptz.release_stream()
        source.stop()
