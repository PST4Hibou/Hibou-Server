from src.audio.debug.channel_spectrogram import ChannelTimeSpectrogram, StftSpectrogram
from src.ptz_devices.vendors.custom.opencv_stream import OpenCVStreamingVendor
from src.ptz_devices.vendors.hikvision.ds_2dy9250iax_a import DS2DY9250IAXA
from src.adc_devices.adc_device_manager import ADCDeviceManager
from src.audio.angle_of_arrival import AngleOfArrivalEstimator
from src.computer_vision.drone_detection import DroneDetection
from src.audio.sources.file_source import FileAudioSource
from src.ptz_devices.ptz_controller import PTZController
from src.audio.sources.rtp_source import RTPAudioSource
from src.audio.debug.radar import RadarPlot
from src.audio.energy import compute_energy
from src.audio.play import play_sample
from src.ai.audio import ModelProxy
from src.settings import SETTINGS
from src.arguments import args
from src.audio import Channel
from src.logger import logger
from collections import deque
from time import sleep

import numpy as np
import datetime
import logging
import os


class AudioProcess:
    def __init__(self):
        self.audio_queue = deque(maxlen=1)
        self.model = ModelProxy(args.audio_model)

    def process(self, audio_samples: list[Channel]):
        # enhanced_audio = apply_noise_reduction(audio_samples)
        self.audio_queue.append(audio_samples)

        res = self.model.infer(audio_samples)
        if np.any(res):
            print(f"DRONE: {res}")
        else:
            print(f"NONE: {res}")

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
    devices = ADCDeviceManager.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    # devices = ADCDeviceManager.auto_discover()

    logging.info(f"{len(devices)} devices loaded...")
    logging.debug(f"Devices: {devices}")

    now = datetime.datetime.now()
    recs_folder_name = os.path.join(
        SETTINGS.REC_SAVE_FP, f"{now.strftime('%d-%m-%Y_%H:%M:%S')}"
    )
    if args.infer_from_folder:
        source = FileAudioSource(
            folder_path=args.infer_from_folder,
            channel_prefix=args.channel_prefix,
            channels_count=args.channel_count,
            save_fp=recs_folder_name,
            enable_recording_saves=SETTINGS.REC_ENABLE,
            record_duration=SETTINGS.AUDIO_CHUNK_DURATION,
        )
    else:
        source = RTPAudioSource(
            devices=devices,
            enable_recording_saves=SETTINGS.REC_ENABLE,
            save_fp=recs_folder_name,
            record_duration=int(SETTINGS.AUDIO_CHUNK_DURATION),
            rec_hz=int(SETTINGS.AUDIO_REC_HZ),
            stream_latency=int(SETTINGS.AUDIO_STREAM_LATENCY),
            channel_prefix=args.channel_prefix,
        )

    audio = AudioProcess()
    source.set_callback(audio.process)  # Called every SETTING.REC_DURATION
    drone_detector = DroneDetection(
        model_type="yolo", model_path="assets/computer_vision_models/best.pt"
    )

    PTZController(
        "main_camera",
        DS2DY9250IAXA,
        host=SETTINGS.PTZ_HOST,
        username=SETTINGS.PTZ_USERNAME,
        password=SETTINGS.PTZ_PASSWORD,
        start_azimuth=SETTINGS.PTZ_START_AZIMUTH,
        end_azimuth=SETTINGS.PTZ_END_AZIMUTH,
        rtsp_port=SETTINGS.PTZ_RTSP_PORT,
        video_channel=SETTINGS.PTZ_VIDEO_CHANNEL,
    )
    PTZController(
        "opencv_vendor",
        OpenCVStreamingVendor,
        video_channel=0,
    )
    stream = PTZController("opencv_vendor").get_video_stream()

    nb_channels = len(devices) * 2
    frame_duration_s = SETTINGS.AUDIO_CHUNK_DURATION / 1000
    angle_coverage = SETTINGS.AUDIO_ANGLE_COVERAGE

    angle_estimator = AngleOfArrivalEstimator(nb_channels, angle_coverage)

    # Only for debug purposes
    energy_spectrum_plot = (
        ChannelTimeSpectrogram(nb_channels, frame_duration_s)
        if SETTINGS.AUDIO_ENERGY_SPECTRUM
        else None
    )
    stft_spectrum_plot = (
        StftSpectrogram(nb_channels, frame_duration_s)
        if SETTINGS.AUDIO_STFT_SPECTRUM
        else None
    )

    # Only for debug purposes
    radar_plot = RadarPlot() if SETTINGS.AUDIO_RADAR else None

    try:
        source.start()
        drone_detector.start(stream, display=SETTINGS.CV_VIDEO_PLAYBACK)
        print("Listening started. Press Ctrl+C to stop.")

        # Main loop
        while True:
            sleep(0.01)  # TODO: Find a solution without using sleep

            if not audio.is_empty():
                channels = audio.get_last_channels()

                energies = [compute_energy(ch) for ch in channels]

                phi_angle = angle_estimator.estimate(energies)

                PTZController("main_camera").go_to_angle(phi=phi_angle)

                # Only for debug purposes
                if SETTINGS.AUDIO_ENERGY_SPECTRUM and energy_spectrum_plot is not None:
                    energy_spectrum_plot.set_input(energies)

                # Only for debug purposes
                if SETTINGS.AUDIO_STFT_SPECTRUM and stft_spectrum_plot is not None:
                    stft_spectrum_plot.set_input(channels)

                # Only for debug purposes
                if SETTINGS.AUDIO_RADAR and radar_plot is not None:
                    radar_plot.set_input(phi_angle, max(energies))

            if radar_plot:
                radar_plot.update()
            if stft_spectrum_plot:
                stft_spectrum_plot.update()
            if energy_spectrum_plot:
                energy_spectrum_plot.update()

            if not drone_detector.is_empty():
                results = drone_detector.get_last_results()

                for result in results:
                    pass
                    # print(result.boxes)

    except KeyboardInterrupt:
        print("\nStopping audio...")
    finally:
        drone_detector.stop()
        PTZController.remove("main_camera")
        source.stop()
