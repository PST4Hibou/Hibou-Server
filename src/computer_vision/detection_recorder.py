from pathlib import Path

import threading
import queue
import time
import cv2


class DetectionRecording:

    def __init__(self, target_file: Path, fps=30, size=(640, 480)):
        self._fps = fps
        self._frame_interval = 1.0 / fps
        self._size = size

        self._frame_queue = queue.Queue(maxsize=200)
        self._stop_event = threading.Event()
        self._thread = None
        self._is_recording = False

        self._start_time = None
        self._next_pts_time = None
        self._last_frame = None

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter(target_file, fourcc, fps, size)

    def _record_worker(self):
        while not self._stop_event.is_set() or not self._frame_queue.empty():

            try:
                frame, ts = self._frame_queue.get(timeout=0.1)
                self._last_frame = frame
            except queue.Empty:
                continue

            # Initialize timeline
            if self._next_pts_time is None:
                self._next_pts_time = ts

            # Write frames aligned to real time
            while self._next_pts_time <= ts:
                if self._last_frame is not None:
                    self.out.write(self._last_frame)

                self._next_pts_time += self._frame_interval

            self._frame_queue.task_done()

    def start_recording(self):
        if self._is_recording:
            return

        self._is_recording = True
        self._stop_event.clear()
        self._start_time = time.time()
        self._next_pts_time = None

        self._thread = threading.Thread(target=self._record_worker, daemon=True)
        self._thread.start()

    def update_frame(self, frame):
        if not self._is_recording:
            return

        ts = time.time()

        try:
            self._frame_queue.put_nowait((frame, ts))
        except queue.Full:
            # Drop frame if overloaded
            pass

    def stop_recording(self):
        if not self._is_recording:
            return

        self._is_recording = False
        self._stop_event.set()
        self._thread.join()
        self.out.release()
