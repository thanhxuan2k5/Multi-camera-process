from queue import Queue
from ..threads import *
from threading import Thread
from typing import List
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage


class CameraController(QObject):
    change_pixmap_signal = pyqtSignal(int, QImage)

    def __init__(self, camera_id: int, camera_config: dict) -> None:
        super().__init__()
        self.camera_id = camera_id
        self.camera_url = camera_config["url"]

        self.zone_polygon = camera_config.get("zone_polygon", [])
        self.counting_line = camera_config.get("counting_line", [])

        self.list_thread: List[Thread] = []

        self.create_queue()
        self.create_thread()

    def create_queue(self):
        self.capture_queue = Queue(maxsize=30)


    def create_thread(self):
        self.thread_capture = ThreadCapture(self.camera_url, self.capture_queue)


        self.thread_process = ThreadProcess(
            self.camera_id,
            self.capture_queue,
            self.zone_polygon,
            self.counting_line
        )

        self.thread_process.change_pixmap_signal.connect(self.change_pixmap_signal)


        self.list_thread = [self.thread_capture,
                            self.thread_process]

    def start(self):
        print("Start camera: ", self.camera_id)
        for thread in self.list_thread:
            thread.start()

    def stop(self):
        for thread in self.list_thread:
            thread.stop()
