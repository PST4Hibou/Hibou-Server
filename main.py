from src.audio.debug.channel_spectrogram import ChannelTimeSpectrogram
from src.audio.angle_of_arrival import AngleOfArrivalEstimator
from src.computer_vision.drone_detection import DroneDetection
from src.audio.sources.file_source import FileAudioSource
from src.audio.sources.rtp_source import RTPAudioSource
from src.audio.models.channel import Channel
from src.audio.debug.radar import RadarPlot
from src.audio.energy import compute_energy
from src.devices.devices import Devices
from src.audio.play import play_sample
from src.settings import SETTINGS
from src.arguments import args
from src.logger import logger
from collections import deque
from src.ptz.ptz import PTZ
from time import sleep

import datetime
import logging
import os


class AudioProcess:
    def __init__(self):
        self.audio_queue = deque(maxlen=1)

    def process(self, audio_samples: list[Channel]):
        # enhanced_audio = apply_noise_reduction(audio_samples)
        self.audio_queue.append(audio_samples)

        if SETTINGS.AUDIO_PLAYBACK:  # Only for debug purposes
            play_sample(audio_samples, 0)

    def get_last_channels(self) -> list[Channel] | None:
        try:
            return self.audio_queue.pop()
        except IndexError:
            return None

    def is_empty(self) -> bool:
        return len(self.audio_queue) == 0


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

    audio = AudioProcess()

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

    nb_channels = len(devices) * 2
    frame_duration_s = SETTINGS.REC_DURATION / 1000
    angle_coverage = SETTINGS.AUDIO_ANGLE_COVERAGE

    if SETTINGS.AUDIO_ENERGY_SPECTRUM:  # Only for debug purposes
        energy_spectrum_plot = ChannelTimeSpectrogram(nb_channels, frame_duration_s)
    else:
        energy_spectrum_plot = None

    if SETTINGS.AUDIO_RADAR:  # Only for debug purposes
        radar_plot = RadarPlot()
    else:
        radar_plot = None

    angle_estimator = AngleOfArrivalEstimator(nb_channels, angle_coverage)

    try:
        source.start()
        drone_detector.start(stream, display=True)
        print("Listening started. Press Ctrl+C to stop.")
        while True:
            sleep(0.01)  # TODO: Find a solution without using sleep

            if not audio.is_empty():
                channels = audio.get_last_channels()
                energies = [compute_energy(ch) for ch in channels]

                angle = angle_estimator.estimate(energies)

                ptz.go_to_angle(angle)

                # Only for debug purposes
                if SETTINGS.AUDIO_ENERGY_SPECTRUM and energy_spectrum_plot is not None:
                    energy_spectrum_plot.update(energies)

                # Only for debug purposes
                if SETTINGS.AUDIO_RADAR and radar_plot is not None:
                    radar_plot.update(angle, max(energies))

    except KeyboardInterrupt:
        print("\nStopping audio...")
    finally:
        drone_detector.stop()
        ptz.release_stream()
        source.stop()
