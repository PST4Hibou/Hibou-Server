from src.audio.debug.channel_spectrogram import ChannelTimeSpectrogram, StftSpectrogram
from src.devices.camera.vendors.hikvision.ds_2dy9250iax_a import DS2DY9250IAXA
from src.devices.audio.audio_device_controller import ADCControllerManager
from src.devices.camera.utils.calibration import start_ptz_calibration
from src.logger import update_log_level, update_global_log_level
from src.audio.angle_of_arrival import AngleOfArrivalEstimator
from src.computer_vision.drone_detection import DroneDetection
from src.devices.camera.ptz_controller import PTZController
from src.audio.sources.file_source import FileAudioSource
from src.audio.sources.rtp_source import RTPAudioSource
from src.tracking.pid_tracker import PIDTracker
from src.audio.debug.radar import RadarPlot
from src.audio.energy import compute_energy
from src.audio.play import play_sample
from src.ai.audio import ModelProxy
from src.doctor import run_doctor
from src.settings import SETTINGS
from src.arguments import args
from src.audio import Channel
from src.logger import logger
from collections import deque
from pathlib import Path
from time import sleep

import datetime
import logging
import os


def apply_arguments():
    if args.rec_duration:
        SETTINGS.AUDIO_CHUNK_DURATION = int(args.rec_duration) * 10**6
    if args.infer_from_folder:
        SETTINGS.INFER_FROM_FOLDER = args.infer_from_folder
    if args.log_level:
        SETTINGS.LOG_LEVEL = args.log_level
        update_log_level()
        update_global_log_level()
    if args.doctor:
        run_doctor()
    if args.ptz_calibration:
        start_ptz_calibration()


class AudioProcess:
    def __init__(self):
        self.audio_queue = deque(maxlen=1)
        self.model = ModelProxy(args.audio_model)

    def process(self, audio_samples: list[Channel]):
        self.audio_queue.append(audio_samples)

        res = self.model.infer(audio_samples)
        # if np.any(res):
        #     print(f"DRONE: {res}")
        # else:
        #     print(f"NONE: {res}")

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
    apply_arguments()

    logger.debug(f"Loaded settings: {SETTINGS}")

    controller_manager = ADCControllerManager()
    if SETTINGS.DEVICES_CONFIG_PATH:
        controller_manager.load_devices_from_files(SETTINGS.DEVICES_CONFIG_PATH)
    else:
        controller_manager.auto_discover()
    devices = controller_manager.adc_devices

    logging.info(f"{len(devices)} devices loaded")
    logging.debug(f"Devices: {devices}")
    for dev in devices:
        if not dev.is_online():
            logging.warning(f"{dev.name} is offline")

    now = datetime.datetime.now()
    recs_folder_name = os.path.join(
        SETTINGS.REC_SAVE_FP, f"{now.strftime('%d-%m-%Y_%H:%M:%S')}"
    )
    if args.infer_from_folder:
        audio_source = FileAudioSource(
            folder_path=args.infer_from_folder,
            channel_prefix=args.channel_prefix,
            channels_count=args.channel_count,
            save_fp=recs_folder_name,
            enable_recording_saves=SETTINGS.REC_AUDIO_ENABLE,
            record_duration=SETTINGS.AUDIO_CHUNK_DURATION,
        )
    else:
        audio_source = RTPAudioSource(
            devices=devices,
            enable_recording_saves=SETTINGS.REC_AUDIO_ENABLE,
            save_fp=recs_folder_name,
            record_duration=int(SETTINGS.AUDIO_CHUNK_DURATION),
            rec_hz=int(SETTINGS.AUDIO_REC_HZ),
            stream_latency=int(SETTINGS.AUDIO_STREAM_LATENCY),
            channel_prefix=args.channel_prefix,
        )

    audio = AudioProcess()
    audio_source.set_callback(audio.process)  # Called every SETTING.REC_DURATION
    drone_detector = DroneDetection(
        enable=SETTINGS.AI_CV_ENABLE,
        model_type=SETTINGS.AI_CV_MODEL_TYPE,
        model_path=Path("assets/computer_vision_models/", SETTINGS.AI_CV_MODEL),
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
    # PTZController(
    #     "opencv_vendor",
    #     OpenCVStreamingVendor,
    #     video_channel=0,
    # )

    PTZController("main_camera").set_absolute_ptz_position(
        pan=160,
        tilt=20,
        zoom=1,
    )

    stream = PTZController("main_camera").get_video_stream()

    tracker = PIDTracker(
        pan_pid=PIDTracker.PidCoefs(
            kp=30,
            ki=0.0,
            kd=0.3,
            setpoint=0,
            output_limits=(-20, 20),
        ),
        tilt_pid=PIDTracker.PidCoefs(
            kp=10,
            ki=0.0,
            kd=0.03,
            setpoint=0,
            output_limits=(-5, 5),
        ),
        zoom_pid=PIDTracker.PidCoefs(
            kp=5, ki=0.0, kd=0.5, setpoint=0.2, output_limits=(-10, 5)
        ),
    )

    nb_channels = sum([x.nb_channels for x in devices])
    if nb_channels == 0:
        raise Exception("No ADC devices found! 0 channels available. Exiting.")
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
        audio_source.start()
        if SETTINGS.REC_VIDEO_ENABLE:
            stream.start_recording(recs_folder_name)
        drone_detector.start(stream, display=SETTINGS.CV_VIDEO_PLAYBACK)
        print("Listening started. Press Ctrl+C to stop.")

        # Main loop
        while True:
            sleep(0.01)  # TODO: Find a solution without using sleep

            if not audio.is_empty():
                channels = audio.get_last_channels()

                energies = [compute_energy(ch) for ch in channels]

                phi_angle = angle_estimator.estimate(energies)

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

            results = drone_detector.get_last_results()

            if results is not None:
                for result in results:
                    if result is None:
                        continue
                    if not "drone" in result.names.values():
                        continue

                    boxes = result.boxes
                    for box, cls_id, conf in zip(boxes.xyxyn, boxes.cls, boxes.conf):
                        class_id = int(cls_id.item())
                        if class_id != 0:  # Skip if not a drone
                            continue
                        x1, y1, x2, y2 = box
                        box_center_x = (x1 + x2) / 2
                        box_center_y = (y1 + y2) / 2

                        controls = tracker.update(box)

                        is_center = (
                            abs(0.5 - box_center_x) < 0.1
                            and abs(0.5 - box_center_y) < 0.1
                        )

                        # print(controls)
                        PTZController("main_camera").set_relative_ptz_position(
                            pan=controls[0],
                            tilt=controls[1],
                            zoom=controls[2] if is_center else None,
                        )

    except KeyboardInterrupt:
        print("\nStopping audio...")
    finally:
        stream.stop_recording()
        drone_detector.stop()
        PTZController.remove()
        audio_source.stop()
